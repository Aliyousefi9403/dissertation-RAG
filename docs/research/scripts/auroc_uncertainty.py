"""Uncertainty for the detector AUROCs: document-clustered bootstrap intervals.

Offline: reads the per-chunk rows saved by entropy_detection_eval.py (detector-*.json)
and entropy_family_eval.py (family-*.json); no model is run. Chunks from one document
are not independent, so the bootstrap resamples documents (with replacement) and keeps
all their chunks (B = 10000, seed 20261016). Reported for each corpus and score:
AUROC, its 95% percentile interval, and for the contextual synonym gap the paired
difference to the word-frequency synonym gap (same resamples). Resamples without both
classes are skipped and counted. With few attacked documents the intervals are wide;
that is the honest statement of what these corpora can show.

Usage: python docs/research/scripts/auroc_uncertainty.py OUT.json
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / "results"
SEED, B = 20261016, 10000
FAMILY_SCORES = ("syngap_top3_domain", "syngap_top3_dirichlet", "js_domain", "lm_mean_surprisal", "ctx_syngap_top3")
DETECTOR_SCORES = ("char_kl", "kl_english", "kl_domain", "mean_domain", "syngap_top3_english", "syngap_top3_domain")


def auroc(pairs):
    """Mann-Whitney AUROC with ties counted as one half; pairs = [(score, label)]."""
    ordered = sorted(pairs, key=lambda x: x[0])
    ranks, i = [0.0] * len(ordered), 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][0] == ordered[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    pos = sum(lab for _, lab in ordered)
    neg = len(ordered) - pos
    if not pos or not neg:
        return None
    return (sum(r for r, (_, lab) in zip(ranks, ordered) if lab) - pos * (pos + 1) / 2) / (pos * neg)


def percentile(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, max(0, round(q * (len(values) - 1))))]


def intervals(rows, scores, paired=None):
    by_doc = defaultdict(list)
    for r in rows:
        by_doc[r["document"]].append(r)
    docs = sorted(by_doc)
    rng = random.Random(SEED)
    draws = {s: [] for s in scores}
    diffs, skipped = [], 0
    for _ in range(B):
        sample = [r for d in (rng.choice(docs) for _ in docs) for r in by_doc[d]]
        values = {s: auroc([(r[s], r["label"]) for r in sample]) for s in scores}
        if any(v is None for v in values.values()):
            skipped += 1
            continue
        for s in scores:
            draws[s].append(values[s])
        if paired:
            diffs.append(values[paired[0]] - values[paired[1]])
    out = {s: {"auroc": round(auroc([(r[s], r["label"]) for r in rows]), 4),
               "ci95": [round(percentile(draws[s], 0.025), 4), round(percentile(draws[s], 0.975), 4)]} for s in scores}
    meta = {"chunks": len(rows), "attacked_chunks": sum(r["label"] for r in rows), "documents": len(docs),
            "documents_with_attacked_chunks": len({r["document"] for r in rows if r["label"]}),
            "bootstrap_resamples_used": B - skipped, "resamples_skipped_one_class": skipped}
    if paired:
        out[f"{paired[0]}_minus_{paired[1]}"] = {
            "difference": round(out[paired[0]]["auroc"] - out[paired[1]]["auroc"], 4),
            "ci95": [round(percentile(diffs, 0.025), 4), round(percentile(diffs, 0.975), 4)],
            "share_of_resamples_above_zero": round(sum(d > 0 for d in diffs) / len(diffs), 4)}
    return {**meta, "scores": out}


def main(out_path):
    report = {"method": "document-clustered percentile bootstrap", "B": B, "seed": SEED, "corpora": {}}
    for path in sorted((RES / "entropy-family").glob("family-*.json")):
        corpus = path.stem.removeprefix("family-")
        rows = json.loads(path.read_text())["rows"]
        report["corpora"].setdefault(corpus, {})["family"] = intervals(
            rows, FAMILY_SCORES, paired=("ctx_syngap_top3", "syngap_top3_domain"))
    detector_files = {"poisoned": RES / "entropy-detector-20261016/detector-poisoned.json",
                      "control": RES / "entropy-detector-20261016/detector-control.json"}
    detector_files |= {p.stem.removeprefix("detector-"): p for p in (RES / "entropy-family").glob("detector-*.json")}
    for corpus, path in sorted(detector_files.items()):
        rows = json.loads(path.read_text())["rows"]
        report["corpora"].setdefault(corpus, {})["word_frequency"] = intervals(rows, DETECTOR_SCORES)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as handle:  # create-only
        json.dump(report, handle, indent=1)
    for corpus, parts in report["corpora"].items():
        fam = parts.get("family", {}).get("scores", {})
        if fam:
            c, w = fam["ctx_syngap_top3"], fam["syngap_top3_domain"]
            print(f"{corpus:22s} word-freq {w['auroc']:.3f} {w['ci95']}  contextual {c['auroc']:.3f} {c['ci95']}")


if __name__ == "__main__":
    main(sys.argv[1])
