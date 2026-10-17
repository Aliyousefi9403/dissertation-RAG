"""Matched comparison: each PWWS-edited chunk vs the identical chunk in the
formatting-only control corpus (same document, same chunk position; the only
difference is the substituted words). Offline; reads saved detector outputs.

Usage: python docs/research/scripts/matched_control_eval.py OUT.json
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[3] / "docs/research/results/entropy-detector-20261016"
SCORES = ["char_kl", "kl_english", "mean_english", "topk_english", "kl_domain", "mean_domain",
          "topk_domain", "syngap_top3_english", "syngap_top3_domain"]


def by_document(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["document"]].append(row)
    return {k: sorted(v, key=lambda r: r["start"]) for k, v in grouped.items()}


def main(out):
    poisoned = by_document(json.loads((ROOT / "detector-poisoned.json").read_text())["rows"])
    control = by_document(json.loads((ROOT / "detector-control.json").read_text())["rows"])
    pairs = [(p, c) for doc in poisoned if len(poisoned[doc]) == len(control.get(doc, []))
             for p, c in zip(poisoned[doc], control[doc]) if p["label"]]
    result = {"matched_edited_chunks": len(pairs), "scores": {}}
    for score in SCORES:
        diffs = [p[score] - c[score] for p, c in pairs]
        higher = sum(d > 0 for d in diffs)
        nonzero = sum(d != 0 for d in diffs)
        result["scores"][score] = {
            "poisoned_higher": higher, "nonzero": nonzero,
            "mean_delta": round(sum(diffs) / len(diffs), 4),
            "sign_test_p": round(binomtest(higher, nonzero, 0.5).pvalue, 6) if nonzero else None}
    Path(out).open("x").write(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
