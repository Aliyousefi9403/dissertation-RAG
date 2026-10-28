"""Human check of the LLM correctness judge.

  sample  RUN_DIR... OUT_DIR   draw a blind, stratified sample of answers to grade by hand
  score   OUT_DIR              compare the hand grades with the judge once the sheet is filled

The sample takes one repetition per (question, condition) and draws up to 5 answers
from each judge score level (0, 0.5, 0.75, 1.0) per condition, seed 20261016. The
grading sheet shows only the question, the reference facts and the answer: no
condition, no judge score, shuffled order. The key that links rows back to the
judge is a separate file. Grade with the judge's own rubric (written in the sheet).

`score` reports exact agreement, agreement within 0.25, mean absolute difference,
Spearman correlation and quadratic-weighted Cohen's kappa, overall and per condition.
Offline, no model calls.
"""

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import spearmanr

SEED = 20261016
PER_LEVEL = 5
LEVELS = (0.0, 0.5, 0.75, 1.0)
GRADES = (0.0, 0.25, 0.5, 0.75, 1.0)
# The judge's rubric, verbatim from the correctness prompt.
RUBRIC = (
    "1.0 = correct and covers the important expected facts; 0.5 = partially correct; "
    "0.0 = incorrect / substantially fails to answer. Intermediate values (e.g. 0.25, 0.75) are allowed when useful. "
    "A correct answer does not need to restate the reference facts verbatim, but must not contradict them "
    "and should cover the important ones."
)
ROOT = Path(__file__).resolve().parents[3]


def sample(run_dirs, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    questions = {
        q["id"]: q
        for q in json.loads(
            (ROOT / "backend/data/evaluation/questions_v1.json").read_text()
        )
    }
    pool = defaultdict(dict)  # (condition, level) -> {question_id: item}
    for run in map(Path, run_dirs):
        for path in sorted((run / "observations").glob("*-correctness.json")):
            judged = json.loads(path.read_text())
            score = judged["capture"].get("raw_score")
            rag_path = path.with_name(
                path.name.replace("-correctness.json", "-rag.json")
            )
            if score not in LEVELS or not rag_path.exists():
                continue
            answer = json.loads(rag_path.read_text()).get("answer")
            key = (judged["condition"], score)
            if answer and judged["question_id"] not in pool[key]:
                pool[key][judged["question_id"]] = {
                    "run_id": judged["run_id"],
                    "index": judged["index"],
                    "condition": judged["condition"],
                    "judge_score": score,
                    "question_id": judged["question_id"],
                    "answer": answer,
                }
    rng = random.Random(SEED)
    chosen = []
    for key in sorted(pool):
        items = [pool[key][q] for q in sorted(pool[key])]
        chosen += rng.sample(items, min(PER_LEVEL, len(items)))
    rng.shuffle(chosen)
    with (out / "grading-sheet.csv").open("x", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "item",
                "question",
                "reference_facts",
                "answer",
                "your_grade (0, 0.25, 0.5, 0.75, 1)",
                "note",
            ]
        )
        writer.writerow(["RUBRIC", RUBRIC, "", "", "", ""])
        for i, item in enumerate(chosen, start=1):
            q = questions[item["question_id"]]
            writer.writerow(
                [
                    i,
                    q["question"],
                    " | ".join(q["reference_facts"]),
                    item["answer"],
                    "",
                    "",
                ]
            )
    key = [
        {"item": i, **{k: v for k, v in item.items() if k != "answer"}}
        for i, item in enumerate(chosen, start=1)
    ]
    (out / "grading-key.json").open("x").write(
        json.dumps({"seed": SEED, "per_level": PER_LEVEL, "items": key}, indent=1)
        + "\n"
    )
    print(f"{len(chosen)} items written to {out / 'grading-sheet.csv'}")


def weighted_kappa(a, b):
    index = {g: i for i, g in enumerate(GRADES)}
    n, k = len(a), len(GRADES)
    observed = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        observed[index[x]][index[y]] += 1
    rows = [sum(r) for r in observed]
    cols = [sum(observed[i][j] for i in range(k)) for j in range(k)]
    w = lambda i, j: (i - j) ** 2 / (k - 1) ** 2  # noqa: E731
    num = sum(w(i, j) * observed[i][j] for i in range(k) for j in range(k))
    den = sum(w(i, j) * rows[i] * cols[j] / n for i in range(k) for j in range(k))
    return 1 - num / den if den else None


def score(out_dir):
    out = Path(out_dir)
    key = {
        item["item"]: item
        for item in json.loads((out / "grading-key.json").read_text())["items"]
    }
    pairs = []
    with (out / "grading-sheet.csv").open(newline="") as handle:
        for row in csv.reader(handle):
            if not row or not row[0].isdigit() or not row[4].strip():
                continue
            human = float(row[4])
            if human not in GRADES:
                raise SystemExit(
                    f"item {row[0]}: grade {row[4]} is not one of {GRADES}"
                )
            pairs.append((key[int(row[0])], human))

    def stats(subset):
        judge = [p[0]["judge_score"] for p in subset]
        human = [p[1] for p in subset]
        if len(subset) < 2:
            return {"items": len(subset)}
        rho = spearmanr(judge, human).statistic
        return {
            "items": len(subset),
            "exact_agreement": round(
                sum(j == h for j, h in zip(judge, human)) / len(subset), 3
            ),
            "within_0.25": round(
                sum(abs(j - h) <= 0.25 for j, h in zip(judge, human)) / len(subset), 3
            ),
            "mean_abs_difference": round(
                sum(abs(j - h) for j, h in zip(judge, human)) / len(subset), 3
            ),
            "judge_minus_human_mean": round(
                sum(j - h for j, h in zip(judge, human)) / len(subset), 3
            ),
            "spearman": None if rho != rho else round(float(rho), 3),
            "quadratic_weighted_kappa": (lambda v: None if v is None else round(v, 3))(
                weighted_kappa(judge, human)
            ),
        }

    by_condition = defaultdict(list)
    for p in pairs:
        by_condition[p[0]["condition"]].append(p)
    result = {
        "graded": len(pairs),
        "of": len(key),
        "all": stats(pairs),
        "by_condition": {c: stats(v) for c, v in sorted(by_condition.items())},
    }
    (out / "agreement.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "sample":
        sample(sys.argv[2:-1], sys.argv[-1])
    else:
        score(sys.argv[2])
