"""Paired analysis of the live TextFooler run: attack effect and both frozen filters on a second attack.

Conditions: clean (main run) and, from the TextFooler run, textfooler (no defence), textfooler_defended
(entropy-filter-v1) and textfooler_contextual (contextual-filter-v1), paired by schedule index.
Edited-text exposure and the perturbed-target stratum use the TextFooler attack manifest
(backend/data/poisoned_textfooler/), not the PWWS one. Statistics are those of analyse_defence.py:
question-level means, 95% cluster bootstrap (B=10000, seed 20261016), two-sided Wilcoxon on non-zero
question differences. Offline, no model calls.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/analyse_textfooler_defence.py MAIN_RUN TEXTFOOLER_RUN OUT_DIR
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

from scipy.stats import wilcoxon

from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from app.ingestion.section_metadata import normalize_heading

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse_defence import B, SEED, outcome  # noqa: E402

CORPUS = Path(__file__).resolve().parents[3] / "backend/data/poisoned_textfooler"
MARKER = "/data/poisoned_textfooler/knowledge_base/"
CONDITIONS = ("clean", "textfooler", "textfooler_defended", "textfooler_contextual")
METRICS = ("correctness", "faithfulness", "hit3", "rr", "exposure")


def manifest():
    return [json.loads(line) for line in (CORPUS / "pwws_attack_manifest.jsonl").read_text().splitlines() if line.strip()]


def edited_spans(entries):
    spans = defaultdict(list)
    for e in entries:
        if not e.get("success"):
            continue
        text = (CORPUS / "knowledge_base" / e["file"]).read_text(encoding="utf-8")
        start = text.find(e["adversarial_text"])
        for tag, _i1, _i2, j1, j2 in SequenceMatcher(None, e["original_text"], e["adversarial_text"], autojunk=False).get_opcodes():
            if tag in ("insert", "replace"):
                spans[e["file"]] += [(start + j1 + m.start(), start + j1 + m.end()) for m in re.finditer(r"\S+", e["adversarial_text"][j1:j2])]
    return spans


def exposure(sources, spans):
    for s in sources:
        path = (s.get("source") or s["metadata"]["source"]).replace("\\", "/")
        if MARKER not in path:
            continue
        name, a = path.split(MARKER, 1)[1], s["metadata"].get("start_index")
        if any(x < a + len(s["content"]) and a < y for x, y in spans.get(name, [])):
            return 1
    return 0


def main(main_dir, tf_dir, out_dir):
    main_run, tf_run, out = Path(main_dir), Path(tf_dir), Path(out_dir)
    m = json.loads((main_run / "manifest.json").read_text())
    tf_manifest = json.loads((tf_run / "manifest.json").read_text())
    assert tf_manifest["paired_main_run"] == m["run_id"], "TextFooler run is not paired with this main run"
    questions = {q["id"]: q for q in m["benchmark"]["data"]}
    entries = manifest()
    treated = {(e["file"], normalize_heading(e["section"])) for e in entries if e.get("success")}
    spans = edited_spans(entries)

    def load(condition, index, stage):
        run = main_run if condition == "clean" else tf_run
        path = run / "observations" / f"{index:06d}-{condition}-{stage}.json"
        return json.loads(path.read_text()) if path.exists() else None

    rows = []
    for unit in m["schedule"]:
        i, q = unit["index"], questions[unit["question_id"]]
        row = {"index": i, "question_id": q["id"], "split": q["split"],
               "target_perturbed": int((q["source_document"], q["expected_sections"][0]) in treated)}
        for c in CONDITIONS:
            rag, corr, faith = (load(c, i, s) for s in ("rag", "correctness", "faithfulness"))
            cap = (rag or {}).get("capture") or {}
            ok = cap.get("retrieval_status") == "ok"
            sources = cap.get("sources") or []
            hit, rr = hit_at_3_and_reciprocal_rank(sources, q["expected_attack_type"], q["expected_sections"]) if ok else (None, None)
            score = ((corr or {}).get("capture") or {}).get("raw_score")
            row.update({f"{c}_correctness": score, f"{c}_faithfulness": ((faith or {}).get("capture") or {}).get("raw_score"),
                        f"{c}_hit3": hit, f"{c}_rr": rr, f"{c}_exposure": exposure(sources, spans) if ok else None,
                        f"{c}_outcome": outcome((rag or {}).get("answer"), score)})
        rows.append(row)

    by_q = defaultdict(list)
    for r in rows:
        by_q[r["question_id"]].append(r)

    def mean(values):
        values = [v for v in values if v is not None]
        return st.mean(values) if values else None

    qm = {k: {f"{c}_{x}": mean(r[f"{c}_{x}"] for r in v) for c in CONDITIONS for x in METRICS}
          | {"target_perturbed": v[0]["target_perturbed"], "split": v[0]["split"]} for k, v in by_q.items()}

    def compare(keys, a, b, x):
        qs = [qm[k] for k in keys if qm[k][f"{a}_{x}"] is not None and qm[k][f"{b}_{x}"] is not None]
        if not qs:
            return None
        diffs = [q[f"{a}_{x}"] - q[f"{b}_{x}"] for q in qs]
        rng = random.Random(SEED)
        boot = sorted(st.mean(rng.choice(diffs) for _ in diffs) for _ in range(B))
        nonzero = [d for d in diffs if d != 0]
        p = wilcoxon(nonzero).pvalue if len(nonzero) >= 5 else None
        return {"a": round(st.mean(q[f"{a}_{x}"] for q in qs), 4), "b": round(st.mean(q[f"{b}_{x}"] for q in qs), 4),
                "delta": round(st.mean(diffs), 4), "ci95": [round(boot[int(0.025 * B)], 4), round(boot[int(0.975 * B)], 4)],
                "wilcoxon_p": None if p is None else round(float(p), 4), "questions": len(qs),
                "improved": sum(d > 0 for d in diffs), "worsened": sum(d < 0 for d in diffs)}

    keys = sorted(qm)
    strata = {"all": keys, "target_perturbed": [k for k in keys if qm[k]["target_perturbed"]],
              "target_not_perturbed": [k for k in keys if not qm[k]["target_perturbed"]],
              "held_out": [k for k in keys if qm[k]["split"] == "held_out"]}
    pairs = {"textfooler_vs_clean": ("textfooler", "clean"), "textfooler_defended_vs_textfooler": ("textfooler_defended", "textfooler"),
             "textfooler_contextual_vs_textfooler": ("textfooler_contextual", "textfooler"),
             "textfooler_contextual_vs_textfooler_defended": ("textfooler_contextual", "textfooler_defended"),
             "textfooler_contextual_vs_clean": ("textfooler_contextual", "clean")}
    results = {n: {s: {x: compare(ks, a, b, x) for x in METRICS} for s, ks in strata.items() if ks} for n, (a, b) in pairs.items()}
    outcomes = {c: {o: sum(r[f"{c}_outcome"] == o for r in rows) for o in ("correct", "partial", "incorrect", "abstained", "unavailable")}
                for c in CONDITIONS}
    filters = {}
    for c in ("textfooler_defended", "textfooler_contextual"):
        flagged = candidates = 0
        for unit in m["schedule"]:
            rag = load(c, unit["index"], "rag")
            for d in ((rag or {}).get("capture") or {}).get("entropy_filter", {}).get("decisions", []):
                candidates += 1
                flagged += bool(d.get("flagged"))
        filters[c] = {"candidates": candidates, "flagged": flagged, "share": round(flagged / candidates, 4) if candidates else None}

    def asr(c):
        flags = [int(r[f"{c}_exposure"] == 1 and r["clean_correctness"] - r[f"{c}_correctness"] >= 0.25)
                 for r in rows if None not in (r[f"{c}_exposure"], r["clean_correctness"], r[f"{c}_correctness"])]
        return round(st.mean(flags), 4) if flags else None

    summary = {"main_run": m["run_id"], "textfooler_run": tf_manifest["run_id"], "pairs": len(rows), "questions": len(keys),
               "perturbed_target_questions": len(strata["target_perturbed"]), "comparisons": results, "outcomes": outcomes,
               "flagged_candidates": filters, "asr_edited_exposure": {c: asr(c) for c in CONDITIONS[1:]},
               "unavailable_observations": {c: {x: sum(r[f"{c}_{x}"] is None for r in rows) for x in METRICS} for c in CONDITIONS},
               "method": "question-level means; cluster bootstrap B=10000 seed 20261016; two-sided Wilcoxon on non-zero question differences; exposure and strata from the TextFooler manifest"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").open("x").write(json.dumps(summary, indent=2) + "\n")
    with (out / "pairs.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [f"# TextFooler live run {tf_manifest['run_id']} paired with {m['run_id']}", ""]
    for name, by_s in results.items():
        lines += [f"## {name}", "", "| Stratum | Metric | A | B | Δ | 95% CI | Wilcoxon p |", "|---|---|---|---|---|---|---|"]
        for s, res in by_s.items():
            for x, v in res.items():
                if v:
                    lines.append(f"| {s} | {x} | {v['a']:.3f} | {v['b']:.3f} | {v['delta']:+.3f} | {v['ci95']} | {v['wilcoxon_p']} |")
        lines.append("")
    lines += [f"Outcomes: {json.dumps(outcomes)}", f"Flagged candidates: {json.dumps(filters)}", f"ASR: {json.dumps(summary['asr_edited_exposure'])}"]
    (out / "report.md").open("x").write("\n".join(lines) + "\n")
    print("\n".join(lines[-3:]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
