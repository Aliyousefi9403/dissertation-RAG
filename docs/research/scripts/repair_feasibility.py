"""Offline feasibility check for a repair defence: can the detector put the original word back?

Ground truth comes from the PWWS attack manifest: aligning each successful
original_text with its adversarial_text gives the exact (substitute -> original)
word pairs. For every word of every attacked passage, the deployed scorer's pieces
(app.defence.entropy_filter: tokens, synonyms, leave-one-document-out reference on
the poisoned corpus) give a gap in bits and a most-likely synonym. A repair rule
"replace w by its most likely synonym when gap(w) > tau" is evaluated per word:

  precision        repaired words that really were PWWS substitutions
  recall           PWWS substitutions that were repaired
  exact restore    repaired substitutions whose replacement equals the original word
  lemma restore    ... or has the same WordNet base form (plant / implants -> plant)

tau is chosen on development documents only (highest recall with precision >= 0.8,
fixed before looking at held-out); held-out documents are reported with that tau.
No model calls.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/repair_feasibility.py OUT.json
"""

import json
import math
import sys
from difflib import SequenceMatcher
from pathlib import Path

from app.config import get_knowledge_base_path
from app.defence.entropy_filter import (
    STOPWORDS,
    _wordnet,
    reference_for,
    synonyms,
    tokens,
)

ROOT = Path(__file__).resolve().parents[3]
TAUS = [round(2 + 0.5 * i, 1) for i in range(21)]  # 2 .. 12 bits
MIN_PRECISION = 0.8


def main(out):
    record = json.loads(
        (ROOT / "backend/data/evaluation/benchmark_v1_record.json").read_text()
    )
    held_out = {Path(d).stem for d in record["held_out_documents"]}
    root = get_knowledge_base_path("poisoned")
    reference = reference_for(str(root))
    manifest = [
        json.loads(l)
        for l in (root.parent / "pwws_attack_manifest.jsonl").read_text().splitlines()
        if l.strip()
    ]
    words = []
    for e in manifest:
        if not e.get("success"):
            continue
        original, adversarial = (
            tokens(e["original_text"]),
            tokens(e["adversarial_text"]),
        )
        truth = {}
        for tag, i1, i2, j1, j2 in SequenceMatcher(
            None, original, adversarial, autojunk=False
        ).get_opcodes():
            if tag == "replace" and i2 - i1 == j2 - j1:
                truth.update(
                    {j: original[i] for i, j in zip(range(i1, i2), range(j1, j2))}
                )
        split = "held_out" if Path(e["file"]).stem in held_out else "development"
        for j, w in enumerate(adversarial):
            if len(w) <= 2 or w in STOPWORDS or not synonyms(w):
                continue
            q = lambda x: reference.probability(x, e["file"])  # noqa: E731
            best = max(synonyms(w), key=q)
            words.append(
                {
                    "split": split,
                    "file": e["file"],
                    "word": w,
                    "gap": math.log2(q(best)) - math.log2(q(w)),
                    "suggested": best,
                    "substituted": j in truth and truth[j] != w,
                    "original": truth.get(j),
                }
            )

    wordnet = _wordnet()
    lemma = lambda w: (
        wordnet.morphy(w, "n") or wordnet.morphy(w, "v") or wordnet.morphy(w) or w
    )  # noqa: E731

    def evaluate(rows, tau):
        repaired = [r for r in rows if r["gap"] > tau]
        subs = [r for r in rows if r["substituted"]]
        hit = [r for r in repaired if r["substituted"]]
        return {
            "tau": tau,
            "repaired": len(repaired),
            "substitutions": len(subs),
            "precision": round(len(hit) / len(repaired), 3) if repaired else None,
            "recall": round(len(hit) / len(subs), 3) if subs else None,
            "exact_restore_of_repaired_substitutions": round(
                sum(r["suggested"] == r["original"] for r in hit) / len(hit), 3
            )
            if hit
            else None,
            "lemma_restore_of_repaired_substitutions": round(
                sum(lemma(r["suggested"]) == lemma(r["original"]) for r in hit)
                / len(hit),
                3,
            )
            if hit
            else None,
            "exact_restore_of_all_substitutions": round(
                sum(r["suggested"] == r["original"] for r in hit) / len(subs), 3
            )
            if subs
            else None,
        }

    dev = [r for r in words if r["split"] == "development"]
    test = [r for r in words if r["split"] == "held_out"]
    dev_curve = [evaluate(dev, t) for t in TAUS]
    eligible = [
        c
        for c in dev_curve
        if c["precision"] is not None and c["precision"] >= MIN_PRECISION
    ]
    tau = (
        max(eligible, key=lambda c: (c["recall"], -c["tau"]))["tau"]
        if eligible
        else None
    )
    payload = {
        "rule": f"repair w -> most likely WordNet synonym when gap(w) > tau; tau = highest dev recall with dev precision >= {MIN_PRECISION}",
        "chosen_tau_bits": tau,
        "words_scored": len(words),
        "development": evaluate(dev, tau) if tau is not None else None,
        "held_out": evaluate(test, tau) if tau is not None else None,
        "all": evaluate(words, tau) if tau is not None else None,
        "development_curve": dev_curve,
        "examples": [
            {k: r[k] for k in ("file", "word", "suggested", "original", "gap")}
            for r in sorted(words, key=lambda r: -r["gap"])
            if r["substituted"]
        ][:25],
    }
    Path(out).open("x").write(json.dumps(payload, indent=1) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in payload.items()
                if k not in ("development_curve", "examples")
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1])
