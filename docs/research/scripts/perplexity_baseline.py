"""Perplexity-filter baseline against the contextual synonym gap, on every corpus.

Perplexity filtering (scoring a passage by its language-model surprisal) is the standard
model-agnostic baseline for adversarial and poisoned text (Jain et al., 2023; Alon and
Kamfonas, 2023). Two variants, from the same distilgpt2 the contextual detector uses, are
already stored per chunk by entropy_family_eval.py:
  lm_mean_surprisal   mean per-token surprisal (log2 perplexity of the whole passage)
  lm_top5_surprisal   mean of the 5 largest token surprisals (a windowed / max-style filter)
Offline: no model is run.

For each corpus this reports AUROC with document-clustered 95% intervals and the paired
difference contextual synonym gap minus each perplexity score (same resamples; B = 10000,
seed 20261016, via auroc_uncertainty.intervals). It also freezes a threshold for each
perplexity score exactly as the deployed filters were frozen (PWWS development chunks, 10%
false-positive rate) and reports the edited and unedited chunks flagged on every corpus,
next to the frozen contextual filter (4.4611 bits).

Usage: python docs/research/scripts/perplexity_baseline.py OUT.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auroc_uncertainty import RES, intervals  # noqa: E402

SCORES = ("ctx_syngap_top3", "lm_top5_surprisal", "lm_mean_surprisal")
CONTEXTUAL_THRESHOLD = 4.4611


def threshold_at_fpr(rows, score, fpr=0.10):
    """Smallest threshold whose false-positive rate on unedited chunks is at most fpr (flag: score > t)."""
    negatives = sorted((r[score] for r in rows if not r["label"]), reverse=True)
    allowed = int(fpr * len(negatives))
    return negatives[allowed] if allowed < len(negatives) else negatives[-1]


def rates(rows, score, threshold):
    pos = [r for r in rows if r["label"]]
    neg = [r for r in rows if not r["label"]]
    return {
        "threshold": round(threshold, 4),
        "edited_flagged": sum(r[score] > threshold for r in pos),
        "edited": len(pos),
        "unedited_flagged": sum(r[score] > threshold for r in neg),
        "unedited": len(neg),
        "fpr": round(sum(r[score] > threshold for r in neg) / len(neg), 4)
        if neg
        else None,
    }


def main(out_path):
    corpora = {
        p.stem.removeprefix("family-"): json.loads(p.read_text())["rows"]
        for p in sorted((RES / "entropy-family").glob("family-*.json"))
    }
    dev = [r for r in corpora["poisoned"] if r["split"] == "development"]
    frozen = {s: threshold_at_fpr(dev, s) for s in SCORES[1:]}
    frozen["ctx_syngap_top3"] = CONTEXTUAL_THRESHOLD
    report = {
        "method": __doc__.strip().splitlines()[0],
        "frozen_thresholds_from_pwws_development": frozen,
        "corpora": {},
    }
    for corpus, rows in corpora.items():
        if not any(r["label"] for r in rows):
            continue
        entry = {}
        for other in SCORES[1:]:
            res = intervals(rows, SCORES, paired=("ctx_syngap_top3", other))
            entry.setdefault("scores", res["scores"])
            entry["scores"].update(
                {k: v for k, v in res["scores"].items() if "_minus_" in k}
            )
            entry.setdefault("chunks", res["chunks"])
            entry.setdefault("attacked_chunks", res["attacked_chunks"])
        entry["frozen"] = {s: rates(rows, s, frozen[s]) for s in SCORES}
        report["corpora"][corpus] = entry
        sc = entry["scores"]
        print(
            f"{corpus:32s} ctx {sc['ctx_syngap_top3']['auroc']:.3f}  top5 {sc['lm_top5_surprisal']['auroc']:.3f}  "
            f"mean {sc['lm_mean_surprisal']['auroc']:.3f}  ctx-top5 {sc['ctx_syngap_top3_minus_lm_top5_surprisal']['difference']:+.3f} "
            f"{sc['ctx_syngap_top3_minus_lm_top5_surprisal']['ci95']}  | flagged ctx "
            f"{entry['frozen']['ctx_syngap_top3']['edited_flagged']}/{entry['frozen']['ctx_syngap_top3']['edited']} "
            f"top5 {entry['frozen']['lm_top5_surprisal']['edited_flagged']} (FPR {entry['frozen']['ctx_syngap_top3']['fpr']} / "
            f"{entry['frozen']['lm_top5_surprisal']['fpr']})"
        )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as handle:  # create-only
        json.dump(report, handle, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
