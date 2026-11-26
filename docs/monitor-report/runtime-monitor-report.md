---
title: "AegisRAG Runtime Monitor"
subtitle: "Design, implementation, evaluation and results"
author: "Ali Yousefi — City St George's, University of London"
date: "October 2026"
---

# 1. Summary

This report describes the runtime verification monitor added to AegisRAG, following Dr Hafizul Asad's suggestion: check every answer against fixed rules before the user sees it, feed violations back to the model, and remember the passages that caused them.

The monitor checks each draft answer against three properties derived from the official MITRE STIX data (CAPEC and ATT&CK), which is pinned by SHA-256 so the attacker cannot change it. When a property is violated it blames the retrieved passages responsible, quarantines them in an append-only memory, retrieves again without them and regenerates with feedback, at most twice. A temporal property, written in LTL, guarantees that a quarantined passage is never used again.

Main results of the final version (v2), on the PWWS-poisoned knowledge base unless stated:

- Edited text reaching the model fell from 41% to 26% of answers (p = 0.016), and the two wrong answers disappeared.
- Correctness was not restored on its own (0.555 to 0.515, not significant), and refusals rose from 45 to 57.
- With the trusted MITRE fallback ("restore" mode), correctness rose to 0.786 and refusals fell to 7 of 132.
- On clean data the cost was negligible (−0.006) and no passage was quarantined.
- On TextFooler, exposure fell from 82% to 58% (p = 0.001), and 26 of 27 quarantined passages were really edited.
- The memory never re-admitted a quarantined passage, but its blame step is imprecise: on PWWS only 10 of 18 quarantined passages were edited.

A first version (v1) was too strict and was fixed; both runs are kept and reported.

# 2. Why a monitor was needed

The earlier entropy-based filters remove suspicious passages before generation. They worked as filters: exposure to edited text fell and the confidently wrong answers disappeared. But they have two weaknesses:

1. **They forget.** The same poisoned passage is judged again every time it is retrieved; nothing is learned.
2. **They remove evidence along with poison.** In this corpus the passage that answers an edited question is usually the edited one, so removing it leaves the model without evidence and it refuses. Correctness does not recover.

The monitor addresses the first point with a memory and tests whether a trusted source can address the second.

# 3. The trusted reference

The attacker in the threat model can edit the knowledge base, so the rules must be checked against something the attacker cannot edit: the official MITRE STIX bundles.

| File | Pinned SHA-256 (start) |
|---|---|
| `stix-capec.json` | `ee6244f4…` |
| `enterprise-attack.json` | `fc783039…` |

The class `TrustedOntology` in `backend/app/defence/runtime_monitor.py` does the following once at startup:

1. **Checks the fingerprints.** It recomputes each file's SHA-256 and refuses to start if it differs from the value written in the code (fail closed).
2. **Reads the attack entries.** Every `attack-pattern` and `course-of-action` object is read, skipping revoked and deprecated ones.
3. **Builds the trusted vocabulary.** All their text is split into words, and each word's dictionary base form (via WordNet's `morphy`) is stored in a Python `set`, so "attacks", "attacked" and "attacking" all map to "attack".
4. **Keeps one reference text per attack.** A mapping file (`source_mapping.yaml`) links each of the 14 attack types in the knowledge base to its MITRE IDs, so the monitor can find the right entry for a question.

# 4. The three properties

## φ1: lexical conformance ("no strange words")

A word in the answer violates φ1 only if all of the following hold:

1. it is rare in English: its Zipf frequency (from the `wordfreq` library) is below **3.5** (for scale, "the" is about 7, "abnegate" about 1);
2. it has at least 3 letters;
3. its base form is not in the trusted MITRE vocabulary;
4. it is not in the user's question;
5. *(v2 only)* it also occurs in the retrieved passages, i.e. the model copied it from the context.

The reasoning: PWWS and TextFooler substitutes such as "engraft" or "abnegate" are rare words that MITRE never uses, so if one appears in an answer it was most likely copied from a tampered passage.

```python
for word in answer:
    if zipf(word) >= 3.5:            continue   # common English word
    if base(word) in MITRE_vocab:    continue
    if word in question:             continue
    if word in retrieved_passages:              # v2
        flag(word)                              # φ1 violated
```

## φ2: evidence availability ("don't give up wrongly")

A regular expression recognises refusals ("does not provide", "cannot answer", "insufficient information"; the same pattern the evaluation uses). If the answer refuses **and** the trusted reference covers the attack asked about, φ2 is violated. The reasoning: when MITRE covers a topic but the model found nothing, its evidence has probably been displaced by poisoning.

## φ3: memory safety ("never trust again")

Written in Linear Temporal Logic:

$$\varphi_3 = \mathbf{G}\big(\mathit{quarantined}(p) \rightarrow \mathbf{G}\,\neg\mathit{inContext}(p)\big)$$

"Always: once passage *p* has been quarantined, it is never in the context again." φ3 holds by construction, because every search drops quarantined passages before anything reaches the model, and it was also checked after the fact on every recorded trace.

**Note on formality.** φ3 is stated in LTL. φ1 and φ2 are state checks implemented in Python on each answer; the monitor was written by hand rather than generated from formulas by a monitor-synthesis tool. Expressing all three in LTL and synthesising the monitor is a natural next step.

# 5. The monitoring loop

Function `monitored_answer()`. Fixed settings: **10** candidate passages, **3** kept, at most **2** regenerations.

1. Search the knowledge base for 10 candidates; drop any whose ID is in the quarantine memory; keep the top 3.
2. Generate an answer. Round 0 uses exactly the normal pipeline prompt; later rounds use a feedback prompt containing the rejected answer and the violated property.
3. Check φ1 and φ2.
4. No violation: stop and release the answer.
5. Violation: `diagnose()` blames passages. If φ1 fired, it blames the kept passages that contain the flagged words. If only φ2 fired, there are no flagged words, so it blames every kept passage that contains any rare non-MITRE word.
6. Quarantine the blamed passages and go back to step 1. If nothing new was blamed, or the retry limit is reached, stop.

**What happens to an unresolved violation:**

| Mode | Unresolved φ1 | Unresolved φ2 |
|---|---|---|
| **verify** | answer withheld | the refusal is released |
| **restore** | answer withheld | the trusted MITRE entry for the attack is added as an extra source and the model answers again |

Each answer is labelled `released`, `released_refusal`, `restored` or `withheld`, and its full round-by-round trace is recorded.

# 6. The quarantine memory

Class `QuarantineMemory`:

- **Passage ID:** SHA-256 of the passage's source file, its position and its exact text. Any edit to a passage gives it a new ID.
- **Storage:** a JSON Lines file, one line per quarantined passage, recording the time, question, round, suspicious words, the property that fired and the source file. Lines are only ever appended.
- **Lookup:** the file is loaded into a Python `set` at startup, so membership checks are instant and the memory survives restarts.

# 7. Integration in the application

- **Backend API.** `POST /chat` accepts a new mode, `"verified"`, and a `trusted_fallback` flag that switches on restore mode. Other modes are unchanged.
- **Memory endpoints.** `GET /monitor/memory` lists the quarantined passages. `POST /monitor/memory/reset` archives the file under a timestamped name instead of deleting it, so evidence is never destroyed.
- **Interface.** "Verified" mode shows a teal gate emblem with φ₁ φ₂ φ₃ nodes (pass, fixed or fail), the monitor's trace for the answer, and the quarantine memory panel. A toggle enables the trusted fallback.

# 8. Testing

## Unit tests (17)

`backend/tests/test_runtime_monitor.py` (13):

- base forms merge inflections and adverbs
- a hash mismatch fails closed
- φ1 flags rare words absent from the trusted reference
- words in the question are allowed
- φ2 fires only when the trusted reference covers the attack
- the attack is taken from the question, then from the passages
- diagnosis points at the passage that contains the flagged word
- the memory is append-only and survives reload
- a violation quarantines, regenerates, and the repeated question is clean
- round 0 uses the unchanged pipeline prompt
- an unresolved φ1 violation withholds the answer
- v2 flags only rare words copied from the context
- restore adds the trusted reference only in restore mode

`backend/tests/test_monitor_api.py` (4): the verified chat mode returns the trace while other modes are unchanged; the memory endpoints list and archive without deleting; the verified answer runs on the poisoned collection; the optional rate limit is off by default.

The full backend suite passes (302 passed, 1 skipped).

## Offline dry check

Before any live run, the rules were applied to answers already recorded in the main experiment, with the rarity cut-off fixed in advance. φ1 flagged **no clean answer** and **3 poisoned answers**, including both wrong ones.

## Live evaluation design

- 44 questions × 3 repetitions × 4 conditions = **528 answers, 1,584 records** (answer plus two judge scores each).
- Conditions: PWWS + verify; PWWS + restore; clean + verify; TextFooler + verify.
- Each condition starts with an empty memory, so repetitions 2 and 3 show what the memory adds.
- Paired by schedule index with the main run; same model (gpt-4o-mini, temperature 0), retrieval settings and judge.
- Statistics: question-level cluster bootstrap 95% intervals (10,000 resamples, seed 20261016) and two-sided Wilcoxon tests.

# 9. Version 1, the problem found, and version 2

**Version 1** flagged under φ1 any rare word outside the MITRE vocabulary, including words the model chose itself (for example "emphasizing"). In its live run it withheld **10 answers**, one of them on clean data, because of rare words the model wrote itself (for example "misinformation" and "feasibility"), which appear neither in the knowledge base nor in the MITRE files. (Corrected 26 Nov 2026: an earlier version said these words came from OWASP and NIST material in the knowledge base; they do not.)

**The fix.** φ1 now counts only rare words that also occur in the retrieved passages. A tampered word that the model repeats is the actual signal of poisoning; a word the model chose itself is not. The full live run was repeated with v2. Both runs are kept, and the change is recorded in `DECISIONS.md` (ADR-009 addendum).

# 10. Results (version 2)

| Comparison | Monitor | Baseline | Δ [95% CI] | p |
|---|---|---|---|---|
| Verify, PWWS: exposure | 0.258 | 0.409 | −0.152 [−0.265, −0.061] | 0.016 |
| Verify, PWWS: correctness | 0.515 | 0.555 | −0.040 [−0.085, 0.000] | 0.074 |
| Verify vs contextual filter: exposure | 0.258 | 0.204 | +0.053 [−0.030, 0.144] | 0.38 |
| Verify vs contextual filter: correctness | 0.515 | 0.485 | +0.030 [−0.002, 0.068] | 0.096 |
| Verify, clean: correctness | 0.708 | 0.714 | −0.006 [−0.023, 0.011] | 0.38 |
| Verify, TextFooler: exposure | 0.583 | 0.818 | −0.235 [−0.356, −0.114] | 0.001 |
| Verify, TextFooler: correctness | 0.542 | 0.564 | −0.023 [−0.087, 0.047] | 0.25 |
| Restore, PWWS: correctness | 0.786 | 0.555 | +0.231 [0.136, 0.335] | 0.0001 |
| Restore vs clean: correctness | 0.786 | 0.714 | +0.072 [−0.004, 0.152] | 0.085 |

**Answer outcomes (132 per condition):**

| Condition | Correct | Partial | Wrong | Refusal |
|---|---|---|---|---|
| Clean, no monitor | 67 | 39 | 0 | 26 |
| Clean, monitor | 65 | 40 | 1 | 26 |
| PWWS, no monitor | 49 | 36 | 2 | 45 |
| PWWS, verify | 42 | 33 | 0 | 57 |
| PWWS, restore | 90 | 34 | 1 | 7 |
| TextFooler, monitor* | 48 | 30 | 0 | 53 |

\*One TextFooler answer was lost to a network error and is recorded as unavailable.

**Monitor behaviour:**

| | PWWS verify | PWWS restore | Clean | TextFooler |
|---|---|---|---|---|
| Passages quarantined | 18 | 18 | 0 | 27 |
| … of which really edited | 10 | 10 | — | 26 |
| Answers withheld | 0 | 0 | 0 | 0 |
| Fell back to MITRE | — | 58 | — | — |
| φ3 violations in traces | 0 | 0 | 0 | 0 |

**Memory across repetitions (repetition 1 → repetitions 2–3):**

| | PWWS | TextFooler |
|---|---|---|
| Quarantined passages skipped at first retrieval, per answer | 0.73 → 1.38 | 1.25 → 2.81 |
| Generations per answer | 1.23 → 1.03 | 1.32 → 1.01 |
| Exposure | 0.27 → 0.25 | 0.60 → 0.57 |
| Correctness | 0.53 → 0.51 | 0.59 → 0.52 |

# 11. Interpretation

**What worked.**

- The monitor reduced how often edited text reached the model on both attacks, and on PWWS it left no wrong answers.
- φ3 held in every trace: the memory never re-admitted a quarantined passage.
- On clean data it quarantined nothing and withheld nothing.
- With the trusted fallback, correctness recovered to the level of the unattacked system and refusals fell to 7.

**What did not, and the details that matter.**

1. **Verification alone does not restore correctness.** Quarantining poisoned passages removes evidence, and refusals rise; this is the same trade-off as the filters.
2. **It is not better than the contextual filter.** The differences in exposure and correctness are not significant.
3. **"Engraft Malicious Package" never reached the user with the monitor, but the answer became a refusal.** Without a defence the phrase reached the user in 3 of 3 repetitions. With the monitor, in repetition 1 the edited passage was retrieved but the first draft did not repeat the phrase; the monitor quarantined the passage, and in repetitions 2 and 3 the memory kept it out of the context. In all three repetitions the final answer was a refusal, not a correct answer. The plain filters also removed the phrase.
4. **The memory helps efficiency more than accuracy.** Later repetitions skip more quarantined passages and need fewer regenerations, but exposure falls only slightly, and correctness is a little lower because more passages have been removed.
5. **The blame step is imprecise.** In v2 every quarantine was triggered by φ2 (a refusal), not by φ1. Without a flagged word, `diagnose()` blames any passage containing rare non-MITRE words, so an ordinary word such as "ingested" was enough to quarantine an unedited passage. On PWWS only 10 of 18 quarantined passages were edited (26 of 27 on TextFooler).
6. **Restore mode is an upper bound.** It beats the clean system numerically (0.786 vs 0.714, not significant) only because it receives trusted MITRE text that the clean system never sees. It shows what a trusted source can add; the monitor's contribution is deciding when to fall back and which passages to stop using.

# 12. Limitations

- φ1 can be evaded by an attacker who chooses substitutes inside the MITRE vocabulary or common enough to fall above the rarity cut-off.
- The trusted reference covers only MITRE; OWASP and NIST content cannot be checked against it.
- An adversary could try to get clean passages quarantined through the blame step; this happened by accident on PWWS.
- One knowledge base, one generator model, 44 questions; correctness is scored by an LLM judge (validated against 75 manual grades, κ = 0.82).

# 13. Next steps

1. Blame passages more precisely, for example only when the contextual synonym gap also flags them, to stop clean passages being quarantined.
2. Check answers sentence by sentence against trusted MITRE sentences (Dr Komninos's suggestion of sentence-level comparison against true statements).
3. Add trusted references for OWASP and NIST content.
4. Write all three properties in LTL and generate the monitor from them.
5. Test an attacker who deliberately chooses substitutes inside the trusted vocabulary.

# 14. Where everything is recorded

| What | Location |
|---|---|
| Monitor code | `backend/app/defence/runtime_monitor.py` |
| API and memory endpoints | `backend/app/defence/monitor_router.py`, `backend/app/main.py` |
| Tests | `backend/tests/test_runtime_monitor.py`, `backend/tests/test_monitor_api.py` |
| Interface | `frontend-next/components/defence/`, `frontend-next/components/living-core/DefenceEmblems.tsx` |
| Evaluation scripts | `docs/research/scripts/monitor_dry_check.py`, `run_monitor_eval.py`, `analyse_monitor.py` |
| Raw run v1 | `pilot-runs/20261027T225951Z-monitor-7435694678804a8fb151bed0f2cb853d` |
| Raw run v2 | `pilot-runs/20261028T123228Z-monitor-43fcd4fbcf96415caaed3c805d5d62f7` |
| Analysis v1 / v2 | `docs/research/results/runtime-monitor/live/`, `…/live-v2/` |
| Dry check | `docs/research/results/runtime-monitor/dry-check.json` |
| Design decisions | `DECISIONS.md`, ADR-009 and addendum |
| Evidence check | `docs/research/scripts/verify_evidence.py` → `docs/research/EVIDENCE.md` (0 problems) |
| Paper | `docs/paper/arxiv/main.tex`, Section V-G and Table V |

Every run writes each record once as its own JSON file and never overwrites it; a completion file holds the SHA-256 of every record, and the evidence script re-hashes all runs and checks the reported numbers against the result files.
