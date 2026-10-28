"""Paired analysis: clean, poisoned (main run) vs defended and clean_filtered (defence run).

Offline, no model calls. Every observation is paired by schedule index
(question x repetition). Questions are the unit of analysis: repetitions are
averaged per question, then 95% cluster-bootstrap intervals (B=10000, seed
20261016) and two-sided Wilcoxon signed-rank tests are computed over questions.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/analyse_defence.py MAIN_RUN DEFENCE_RUN OUT_DIR [OTHER_DEFENCE_RUN ...]

Conditions come from each defence run's manifest (defended/clean_filtered, or
repaired/clean_repaired). Each is compared with its source corpus (poisoned or
clean), and defences on the same corpus are compared with each other.
"""

import csv
import json
import random
import re
import statistics as st
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from app.config import get_knowledge_base_path
from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from app.ingestion.section_metadata import normalize_heading
from scipy.stats import wilcoxon

SEED, B = 20261016, 10000
ABSTAIN = re.compile(
    r"(does not|doesn't|do not) (provide|contain|mention|include|describe|specify)"
    r"|cannot (provide|answer|determine)|insufficient|not (enough|sufficient) information",
    re.I,
)


def outcome(answer, score):
    if answer is None or score is None:
        return "unavailable"
    if ABSTAIN.search(answer):
        return "abstained"
    return "correct" if score >= 0.75 else "partial" if score >= 0.25 else "incorrect"


def edited_spans():
    root = get_knowledge_base_path("poisoned")
    manifest = Path(root).parents[1] / "poisoned/pwws_attack_manifest.jsonl"
    spans = defaultdict(list)
    for line in manifest.read_text().splitlines():
        e = json.loads(line)
        if not e.get("success"):
            continue
        text = (root / e["file"]).read_text(encoding="utf-8")
        start = text.find(e["adversarial_text"])
        for tag, _i1, _i2, j1, j2 in SequenceMatcher(
            None, e["original_text"], e["adversarial_text"], autojunk=False
        ).get_opcodes():
            if tag in ("insert", "replace"):
                spans[e["file"]] += [
                    (start + j1 + m.start(), start + j1 + m.end())
                    for m in re.finditer(r"\S+", e["adversarial_text"][j1:j2])
                ]
    return root, spans


def exposure(sources, root, spans):
    marker = "/data/poisoned/knowledge_base/"  # portable: records may come from another checkout path
    for s in sources:
        path = (s.get("source") or s["metadata"]["source"]).replace("\\", "/")
        if marker not in path:
            continue
        name = path.split(marker, 1)[1]
        a = s["metadata"].get("start_index")
        if any(x < a + len(s["content"]) and a < y for x, y in spans.get(name, [])):
            return 1
    return 0


def main(main_dir, defence_dir, out_dir, *other_defence_dirs):
    main_run, defence_run, out = Path(main_dir), Path(defence_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((main_run / "manifest.json").read_text())
    defence_manifest = json.loads((defence_run / "manifest.json").read_text())
    runs_by_condition, source_of = {"clean": main_run, "poisoned": main_run}, {}
    for run_dir in (defence_dir, *other_defence_dirs):
        run_manifest = json.loads((Path(run_dir) / "manifest.json").read_text())
        assert run_manifest["paired_main_run"] == manifest["run_id"], (
            f"{run_dir} is not paired with the main run"
        )
        for condition, source in run_manifest["conditions"].items():
            runs_by_condition[condition], source_of[condition] = Path(run_dir), source
    CONDITIONS = tuple(runs_by_condition)
    questions = {q["id"]: q for q in manifest["benchmark"]["data"]}
    treated = {
        (e["file"], normalize_heading(e["section"]))
        for e in manifest["attack_manifest"]["entries"]
        if e.get("success")
    }
    root, spans = edited_spans()

    def load(run, index, condition, stage):
        path = run / "observations" / f"{index:06d}-{condition}-{stage}.json"
        return json.loads(path.read_text()) if path.exists() else None

    rows = []
    for unit in manifest["schedule"]:
        i, q = unit["index"], questions[unit["question_id"]]
        row = {
            "index": i,
            "question_id": q["id"],
            "repetition": unit["repetition"],
            "split": q["split"],
            "category": q["question_category"],
            "target_perturbed": int(
                (q["source_document"], q["expected_sections"][0]) in treated
            ),
        }
        for condition in CONDITIONS:
            run = runs_by_condition[condition]
            rag, corr, faith = (
                load(run, i, condition, s)
                for s in ("rag", "correctness", "faithfulness")
            )
            capture = (rag or {}).get("capture") or {}
            retrieved = capture.get("retrieval_status") == "ok"
            sources = capture.get("sources") or []
            hit, rr = (
                hit_at_3_and_reciprocal_rank(
                    sources, q["expected_attack_type"], q["expected_sections"]
                )
                if retrieved
                else (None, None)
            )
            c = ((corr or {}).get("capture") or {}).get("raw_score")
            f = ((faith or {}).get("capture") or {}).get("raw_score")
            row.update(
                {
                    f"{condition}_correctness": c,
                    f"{condition}_faithfulness": f,
                    f"{condition}_hit3": hit,
                    f"{condition}_rr": rr,
                    f"{condition}_exposure": exposure(sources, root, spans)
                    if retrieved
                    else None,
                    f"{condition}_outcome": outcome((rag or {}).get("answer"), c),
                }
            )
        rows.append(row)

    by_q = defaultdict(list)
    for r in rows:
        by_q[r["question_id"]].append(r)
    metrics = ("correctness", "faithfulness", "hit3", "rr", "exposure")

    def available_mean(values):
        values = [x for x in values if x is not None]
        return st.mean(values) if values else None

    qmeans = {
        k: {
            f"{c}_{m}": available_mean(x[f"{c}_{m}"] for x in v)
            for c in CONDITIONS
            for m in metrics
        }
        | {"target_perturbed": v[0]["target_perturbed"], "split": v[0]["split"]}
        for k, v in by_q.items()
    }

    def compare(keys, a, b, m):
        qs = [
            qmeans[k]
            for k in keys
            if qmeans[k][f"{a}_{m}"] is not None and qmeans[k][f"{b}_{m}"] is not None
        ]
        diffs = [x[f"{a}_{m}"] - x[f"{b}_{m}"] for x in qs]
        rng = random.Random(SEED)
        boot = sorted(st.mean(rng.choice(diffs) for _ in diffs) for _ in range(B))
        nonzero = [d for d in diffs if d != 0]
        p = wilcoxon(nonzero).pvalue if len(nonzero) >= 5 else None
        return {
            "a": round(st.mean(x[f"{a}_{m}"] for x in qs), 4),
            "b": round(st.mean(x[f"{b}_{m}"] for x in qs), 4),
            "delta": round(st.mean(diffs), 4),
            "ci95": [round(boot[int(0.025 * B)], 4), round(boot[int(0.975 * B)], 4)],
            "wilcoxon_p": None if p is None else round(float(p), 4),
            "questions": len(qs),
            "questions_changed": len(nonzero),
            "improved": sum(d > 0 for d in diffs),
            "worsened": sum(d < 0 for d in diffs),
        }

    keys = sorted(qmeans)
    strata = {
        "all": keys,
        "target_perturbed": [k for k in keys if qmeans[k]["target_perturbed"]],
        "target_not_perturbed": [k for k in keys if not qmeans[k]["target_perturbed"]],
        "held_out": [k for k in keys if qmeans[k]["split"] == "held_out"],
    }
    comparisons = {f"{c}_vs_{source}": (c, source) for c, source in source_of.items()}
    comparisons |= {
        f"{c}_vs_clean": (c, "clean")
        for c, source in source_of.items()
        if source == "poisoned"
    }
    on_poisoned = [c for c, source in source_of.items() if source == "poisoned"]
    comparisons |= {
        f"{a}_vs_{b}": (a, b)
        for i, a in enumerate(on_poisoned)
        for b in on_poisoned[i + 1 :]
    }
    results = {
        name: {
            s: {m: compare(ks, a, b, m) for m in metrics}
            for s, ks in strata.items()
            if ks
        }
        for name, (a, b) in comparisons.items()
    }
    outcomes = {
        c: {
            o: sum(r[f"{c}_outcome"] == o for r in rows)
            for o in ("correct", "partial", "incorrect", "abstained", "unavailable")
        }
        for c in CONDITIONS
    }

    def asr(cond):
        flags = [
            int(
                r[f"{cond}_exposure"] == 1
                and r["clean_correctness"] - r[f"{cond}_correctness"] >= 0.25
            )
            for r in rows
            if None
            not in (
                r[f"{cond}_exposure"],
                r["clean_correctness"],
                r[f"{cond}_correctness"],
            )
        ]
        return round(st.mean(flags), 4)

    unavailable = {
        c: {m: sum(r[f"{c}_{m}"] is None for r in rows) for m in metrics}
        for c in CONDITIONS
    }

    summary = {
        "main_run": manifest["run_id"],
        "defence_run": defence_manifest["run_id"],
        "pairs": len(rows),
        "questions": len(keys),
        "defence": defence_manifest["defence"],
        "comparisons": results,
        "outcomes": outcomes,
        "asr_edited_exposure": {c: asr(c) for c in ("poisoned", *on_poisoned)},
        "unavailable_observations": unavailable,
        "method": "question-level means; cluster bootstrap B=10000 seed 20261016; two-sided Wilcoxon signed-rank on non-zero question differences",
    }
    (out / "summary.json").open("x").write(json.dumps(summary, indent=2) + "\n")
    with (out / "pairs.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        f"# Defence evaluation: {defence_manifest['run_id']} paired with {manifest['run_id']}",
        f"{len(rows)} pairs, {len(keys)} questions.",
        "",
    ]
    for name, by_stratum in results.items():
        lines += [
            f"## {name}",
            "",
            "| Stratum | Metric | A | B | Δ (A−B) | 95% CI | Wilcoxon p | improved / worsened |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for stratum, res in by_stratum.items():
            for m, v in res.items():
                lines.append(
                    f"| {stratum} | {m} | {v['a']:.3f} | {v['b']:.3f} | {v['delta']:+.3f} | {v['ci95']} | {v['wilcoxon_p']} | {v['improved']} / {v['worsened']} |"
                )
        lines.append("")
    lines += [
        f"Outcomes: {json.dumps(outcomes)}",
        f"ASR (edited exposure, drop ≥0.25): {json.dumps(summary['asr_edited_exposure'])}",
        f"Unavailable observations (kept as missing, never zero): {json.dumps(unavailable)}",
    ]
    (out / "report.md").open("x").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:])
