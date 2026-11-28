"""Independent test of the poisoning detectors on knowledge base v2 (pre-registered analysis).

This script was written and committed before the knowledge base v2 corpus was attacked, so the
hypothesis, the thresholds and the comparisons below were fixed before any v2 score existed.

Corpus: knowledge base v2 poisoned with plain PWWS by the 60-class surrogate
(data/kb_v2/poisoned_pwws, attack_kb_v2.py). Only the 46 documents that knowledge base v1 does
not have are attacked and analysed (the "held_out" split of entropy_family_eval.py and
mlm_detector_eval.py with corpus kb_v2); no detector setting was tuned on them.

Primary hypothesis (H1): on the new documents the contextual synonym gap (ctx_syngap_top3) ranks
edited passages above unedited ones better than the word-frequency synonym gap
(syngap_top3_domain): paired AUROC difference > 0, with a 95% document-clustered bootstrap
interval that excludes 0.

Secondary, reported whatever they show:
  - AUROC with 95% intervals for every detector below;
  - paired differences: contextual vs top-5 surprisal; masked-LM synonym gap vs contextual and vs
    top-5 surprisal; masked-LM top-5 pseudo-log-likelihood vs top-5 surprisal;
  - detection and false-alarm rates at thresholds frozen on the original PWWS development
    documents (never re-tuned): the two deployed thresholds, and the FPR-10% development
    thresholds for the other detectors;
  - false alarms on the 18 unedited v1 documents of the same corpus.

Bootstrap: documents resampled with replacement, all their passages kept, B = 10000, seed
20261016, the same resamples for every score; resamples without both classes are skipped and
counted.

Inputs (results/kb-v2/): family-kb_v2.json (entropy_family_eval.py) and, if present,
mlm-kb_v2.json (mlm_detector_eval.py). Offline; no model is run.
Usage: python docs/research/scripts/kb_v2_independent_test.py OUT.json
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auroc_uncertainty import auroc, percentile

RES = Path(__file__).resolve().parents[1] / "results"
SEED, B = 20261016, 10000
PRIMARY = ("ctx_syngap_top3", "syngap_top3_domain")
SECONDARY = (
    ("ctx_syngap_top3", "lm_top5_surprisal"),
    ("mlm_syngap_top3", "ctx_syngap_top3"),
    ("mlm_syngap_top3", "lm_top5_surprisal"),
    ("mlm_top5_pll", "lm_top5_surprisal"),
)
DEPLOYED = {"syngap_top3_domain": 7.2262, "ctx_syngap_top3": 4.4611}
FAMILY_SCORES = ("syngap_top3_domain", "ctx_syngap_top3", "lm_top5_surprisal")
MLM_SCORES = ("mlm_syngap_top3", "mlm_mean_pll", "mlm_top5_pll")


def frozen_thresholds(scores):
    """Deployed thresholds, else the FPR-10% threshold on the v1 PWWS development documents."""
    out = dict(DEPLOYED)
    sources = {
        "family": RES / "entropy-family/family-poisoned.json",
        "mlm": RES / "mlm-detector/family-poisoned.json",
    }
    for path in sources.values():
        if path.exists():
            dev = json.loads(path.read_text())["results"]["development"]
            for s in scores:
                if s not in out and isinstance(dev.get(s), dict):
                    t = dev[s].get("threshold_fpr10")
                    if t is not None:
                        out[s] = t
    return out


def rates(rows, score, threshold):
    pos = [r for r in rows if r["label"]]
    neg = [r for r in rows if not r["label"]]
    return {
        "threshold": threshold,
        "edited_flagged": sum(r[score] > threshold for r in pos),
        "edited": len(pos),
        "tpr": round(sum(r[score] > threshold for r in pos) / len(pos), 4)
        if pos
        else None,
        "unedited_flagged": sum(r[score] > threshold for r in neg),
        "unedited": len(neg),
        "fpr": round(sum(r[score] > threshold for r in neg) / len(neg), 4)
        if neg
        else None,
    }


def bootstrap(rows, scores, pairs):
    by_doc = defaultdict(list)
    for r in rows:
        by_doc[r["document"]].append(r)
    docs = sorted(by_doc)
    rng = random.Random(SEED)
    draws = {s: [] for s in scores}
    diffs = {p: [] for p in pairs}
    skipped = 0
    for _ in range(B):
        sample = [r for d in (rng.choice(docs) for _ in docs) for r in by_doc[d]]
        values = {s: auroc([(r[s], r["label"]) for r in sample]) for s in scores}
        if any(v is None for v in values.values()):
            skipped += 1
            continue
        for s in scores:
            draws[s].append(values[s])
        for a, b in pairs:
            diffs[(a, b)].append(values[a] - values[b])
    point = {s: auroc([(r[s], r["label"]) for r in rows]) for s in scores}
    out = {
        "chunks": len(rows),
        "attacked_chunks": sum(r["label"] for r in rows),
        "documents": len(docs),
        "documents_with_attacked_chunks": len(
            {r["document"] for r in rows if r["label"]}
        ),
        "bootstrap_resamples_used": B - skipped,
        "auroc": {
            s: {
                "auroc": round(point[s], 4),
                "ci95": [
                    round(percentile(draws[s], 0.025), 4),
                    round(percentile(draws[s], 0.975), 4),
                ],
            }
            for s in scores
        },
        "paired": {},
    }
    for a, b in pairs:
        d = diffs[(a, b)]
        out["paired"][f"{a}_minus_{b}"] = {
            "difference": round(point[a] - point[b], 4),
            "ci95": [round(percentile(d, 0.025), 4), round(percentile(d, 0.975), 4)],
            "share_of_resamples_above_zero": round(sum(x > 0 for x in d) / len(d), 4),
        }
    return out


def main(out_path):
    family = json.loads((RES / "kb-v2/family-kb_v2.json").read_text())["rows"]
    rows = {(r["document"], r["start"]): dict(r) for r in family}
    scores = list(FAMILY_SCORES)
    mlm_path = RES / "kb-v2/mlm-kb_v2.json"
    if mlm_path.exists():
        for r in json.loads(mlm_path.read_text())["rows"]:
            key = (r["document"], r["start"])
            if key in rows:
                rows[key].update({s: r[s] for s in MLM_SCORES})
        scores += MLM_SCORES
    rows = [r for r in rows.values() if all(s in r for s in scores)]
    new = [r for r in rows if r["split"] == "held_out"]
    old = [r for r in rows if r["split"] == "development"]
    pairs = [PRIMARY] + [p for p in SECONDARY if p[0] in scores and p[1] in scores]
    thresholds = frozen_thresholds(scores)
    result = bootstrap(new, scores, pairs)
    primary = result["paired"][f"{PRIMARY[0]}_minus_{PRIMARY[1]}"]
    report = {
        "corpus": "kb_v2 (PWWS, 60-class surrogate), 46 new documents",
        "pre_registered": "analysis committed before the corpus was attacked",
        "bootstrap": {"B": B, "seed": SEED, "resample": "documents"},
        "primary_hypothesis": {
            "statement": "AUROC(ctx_syngap_top3) > AUROC(syngap_top3_domain) on the new documents",
            "difference": primary["difference"],
            "ci95": primary["ci95"],
            "supported": primary["ci95"][0] > 0,
        },
        "new_documents": result,
        "frozen_thresholds": {
            s: {
                "new_documents": rates(new, s, t),
                "unedited_v1_documents": rates(old, s, t),
            }
            for s, t in thresholds.items()
            if s in scores
        },
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as handle:  # create-only
        json.dump(report, handle, indent=1)
    print(json.dumps(report["primary_hypothesis"]))
    for s, v in result["auroc"].items():
        print(f"{s:20s} {v['auroc']:.3f} {v['ci95']}")
    for k, v in result["paired"].items():
        print(f"{k:45s} {v['difference']:+.3f} {v['ci95']}")


if __name__ == "__main__":
    main(sys.argv[1])
