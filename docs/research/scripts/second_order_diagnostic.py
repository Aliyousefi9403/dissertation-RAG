"""Why the second-order adaptive attack failed: which PWWS swaps each evasion rule allows.

Takes the swaps that unrestricted PWWS actually used (matched control corpus,
poisoned_pwws_rerun: same surrogate, same sections) and asks, swap by swap, whether
the adaptive attackers' rules would have allowed it:

  frequency rule  q(substitute) >= q(original) under the defender's domain reference
  LM rule         the section with only this swap is at least as probable under
                  distilgpt2 (whole section, up to 1024 tokens) as the original section

It also checks the rules are not vacuous: the LM rule must accept the identity edit
and the reverse of a swap it rejects (restoring the original word) must pass it.
Offline; no API calls; no corpus is modified.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/second_order_diagnostic.py OUT.json
"""

import json
import sys
from pathlib import Path

from app.attack import pwws_poison_kb as base
from app.defence.contextual_filter import LanguageModel
from app.defence.entropy_filter import DomainReference

ROOT = Path(__file__).resolve().parents[3] / "backend"


def word_swaps(original, adversarial):
    from textattack.shared import AttackedText

    a, b = AttackedText(original), AttackedText(adversarial)
    if len(a.words) != len(b.words):
        return None, a
    return [
        (i, a.words[i], b.words[i])
        for i in range(len(a.words))
        if a.words[i] != b.words[i]
    ], a


def main(out_path):
    reference = DomainReference(base.CLEAN_KB)
    lm = LanguageModel(max_tokens=1024)
    manifest = ROOT / "data/poisoned_pwws_rerun/pwws_attack_manifest.jsonl"
    rows, sections = [], []
    for line in manifest.read_text().splitlines():
        e = json.loads(line)
        if not e.get("success"):
            continue
        swaps, attacked = word_swaps(e["original_text"], e["adversarial_text"])
        if swaps is None:
            sections.append(
                {"file": e["file"], "section": e["section"], "aligned": False}
            )
            continue
        base_lp = lm.log2_prob([e["original_text"]])[0]
        single = [attacked.replace_word_at_index(i, new).text for i, _, new in swaps]
        lps = [
            p for k in range(0, len(single), 4) for p in lm.log2_prob(single[k : k + 4])
        ]
        both = lm.log2_prob([e["adversarial_text"]])[0]
        for (i, old, new), lp in zip(swaps, lps):
            freq_ok = reference.probability(
                new.lower(), e["file"]
            ) >= reference.probability(old.lower(), e["file"])
            rows.append(
                {
                    "file": e["file"],
                    "section": e["section"],
                    "original": old,
                    "substitute": new,
                    "frequency_rule": freq_ok,
                    "lm_delta_bits": round(lp - base_lp, 3),
                    "lm_rule": lp >= base_lp,
                }
            )
        sections.append(
            {
                "file": e["file"],
                "section": e["section"],
                "aligned": True,
                "swaps": len(swaps),
                "whole_attack_lm_delta_bits": round(both - base_lp, 3),
            }
        )
    # sanity: identity passes; restoring the original word after a rejected swap passes
    probe = next(r for r in rows if not r["lm_rule"])
    e = next(
        json.loads(l)
        for l in manifest.read_text().splitlines()
        if json.loads(l).get("success")
        and json.loads(l)["section"] == probe["section"]
        and json.loads(l)["file"] == probe["file"]
    )
    identity_ok = (
        lm.log2_prob([e["original_text"]])[0] >= lm.log2_prob([e["original_text"]])[0]
    )
    n = len(rows)
    summary = {
        "successful_unrestricted_sections": len(sections),
        "aligned_sections": sum(s["aligned"] for s in sections),
        "swaps": n,
        "pass_frequency_rule": sum(r["frequency_rule"] for r in rows),
        "pass_lm_rule": sum(r["lm_rule"] for r in rows),
        "pass_both_rules": sum(r["frequency_rule"] and r["lm_rule"] for r in rows),
        "median_lm_delta_bits": sorted(r["lm_delta_bits"] for r in rows)[n // 2],
        "sections_whose_full_attack_passes_lm_rule": sum(
            s.get("whole_attack_lm_delta_bits", -1) >= 0 for s in sections
        ),
        "sanity_identity_passes_lm_rule": identity_ok,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as handle:
        json.dump(
            {"summary": summary, "sections": sections, "swaps": rows}, handle, indent=1
        )
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
