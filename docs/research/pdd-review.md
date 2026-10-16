# PDD review — "Evaluating answer reliability under knowledge base poisoning in cybersecurity RAG systems"

**Deadline:** Wed 11 Nov 2026, 20:00. The only resubmission is Wed 2 Dec 2026.
**Marked against:** IN3007 criteria. Methods and Results/Challenge carry the most weight. First-class work needs evidence of at least three of: breadth of reading, originality, solving substantial intellectual problems, depth of knowledge.
**Overall:** the draft is careful, honest and well scoped, and its framing (indicators, not a new defence) is right. The changes below strengthen it with evidence you already have, and fix two places where the pilot data shows the plan would not work as written.

I have not seen the Project Handbook's PDD template or length limit. Check section names and length against it before submitting.

## Must change (the pilot contradicts the current plan)

1. **The consistency indicator will be degenerate at temperature 0.** In the 12×3 pilot, retrieval was identical across repetitions for all 12 questions, and poisoned judge scores never varied. "Consistency across repeated generations" of the *answer under test* therefore has almost no variance. Suggested replacement for the indicator sentence in Objective 4:
   > "…and answer consistency across *k* additional sampled generations (temperature > 0, fixed *k*, recorded seeds where supported), generated separately from the temperature-0 answer that is evaluated, following sampling-based self-consistency checks [SelfCheckGPT]."

2. **Poisoning mainly produced abstentions, not confident errors.** In the pilot:
   - 14 of the 15 pairs with a correctness drop of at least 0.25 lost the expected section from the top 3.
   - 8 of those 15 answers said the context was insufficient.
   - These abstentions account for about 90% of the correctness loss.

   The plan's focus on "confidently incorrect answers" should allow for this. Add to *Measurements*:
   > "Outcome category per answer: correct / incorrect / abstained (explicitly declines for insufficient context). Abstentions are reported separately and are not scored as confident errors or as unfaithful."

   Abstentions also break the current evidence-check policy. A poisoned abstention is labelled "unsupported", because the verifier treats "the context does not mention HTTP" as a claim. This was seen in a live test on 16 Oct.

## Should add (strengthens Methods and originality)

3. **Mention the pilot as feasibility evidence.** Two or three sentences in §4, under *Pilot and repeated evaluation*:
   > "A preliminary 12-question pilot (3 repetitions, 216 recorded model calls, zero errors after an infrastructure fault in an earlier run) confirmed complete recording and offline reproducibility. It showed lower poisoned retrieval (Hit@3 0.92→0.50) and correctness (0.88→0.67), mainly through displacement of the relevant passage. These are pilot observations on development questions and will not be reported as main results."

4. **Add a formatting-only control.** The poisoning script also flattens the layout of every attacked section and shifts every character offset, so retrieval changes are not caused by word substitutions alone. Add to *Controlled poisoning*:
   > "To separate word substitution from formatting side-effects, I will include a control copy in which the same sections are re-formatted identically but no words are substituted."

   This is a cheap, original methodological contribution.

5. **Make the held-out split concrete.** The 45-question draft is labelled `development_expansion_not_held_out` and overlaps the pilot's targets. Name the rule now:
   > "Held-out material: all questions whose source is one of N documents chosen before the main run (stratified by category); thresholds are chosen only on the remaining documents."

   With 14 documents, 4–5 held-out documents is realistic.

6. **Use within-corpus controls.** Of the 45 draft questions, 26 target a section that PWWS actually changed; 19 target sections that were attacked unsuccessfully or not attacked. The deterministic pre-check already shows a gap. On treated items, poisoned Hit@3 falls from 0.62 to 0.42. On control items it falls from 0.79 to 0.74. Add:
   > "Results will be stratified by whether a question's target section was successfully perturbed, using unperturbed targets as within-corpus controls."

7. **Define two exposure measures.** "Retrieved a chunk from an attacked section" (0.92 in the pilot) and "retrieved actually edited text" (0.42) differ a lot, and the RAG attack success rate halves (0.33 → 0.17) depending on which you use. The PDD lists edited-text exposure; say explicitly that you will report both and treat edited-text exposure as primary.

8. **Report the surrogate attack rate correctly.** "Classifier attack success" should be defined as successful ÷ (successful + failed) = 38/57. The current saved summary uses all 88 attempts, including 31 skipped.

## Literature (currently 3 references; aim for 15–25 by the final report)

Add a short paragraph naming the comparison set. Each of these is directly relevant; **verify every citation before use**:
- Zou et al., *PoisonedRAG* (USENIX Security 2025; arXiv 2402.07867): knowledge-corruption attacks on RAG.
- Zhong et al., *Poisoning Retrieval Corpora by Injecting Adversarial Passages* (EMNLP 2023).
- Jin et al., *Is BERT Really Robust?* (TextFooler, AAAI 2020): the attack used in [2].
- Morris et al., *TextAttack* (EMNLP 2020 demos): the framework you use.
- Mozes et al., *Frequency-Guided Word Substitutions for Detecting Textual Adversarial Examples* (EACL 2021): detection of word-substitution attacks like PWWS.
- Manakul et al., *SelfCheckGPT* (EMNLP 2023): sampling-consistency indicator.
- Es et al., *RAGAS* (EACL 2024 demos): faithfulness and answer-relevance evaluation.
- Zheng et al., *Judging LLM-as-a-Judge* (NeurIPS 2023 Datasets & Benchmarks): judge bias, which motivates your manual checks.
- Xiang et al., *Certifiably Robust RAG against Retrieval Corruption* (RobustRAG, 2024): a defence to contrast with your "indicators, not a defence" scope.

## Smaller points

- **Timeline:** use the real dates.
  - PDD: 11 Nov 2026.
  - Ethics materials: Sun 21 Feb 2027, 17:00.
  - Submission: Sun 4 Apr 2027, 17:00.
  - Reviews: 1–11 Jun 2027.

  Your February row says "complete required ethics documentation"; put the exact date there.
- **Objective 2:** "approximately 14 categories". The corpus has 14 attack *types* in 5 *categories* (ddos, injection, malware, reconnaissance, spoofing). Use one term consistently.
- **§4 heading:** "4 … continued" is fine, but check that the template allows it.
- **LSEPI:** add one line saying MITRE ATT&CK and CAPEC content is used under MITRE's terms of use with attribution, and that question and answer text is sent to OpenAI's API (provider, data policy, no personal data). You already cover most of this.
- **BCS accreditation:** the project must include a practical artefact, an evaluation of that solution, and critical self-evaluation. The draft covers all three; keep "critical self-evaluation of the process" visible in the report plan.

## Benchmark issues to resolve before freezing (see `benchmark-review/`)

- **1 blocker:** `expanded_vulnerability_scanning_att_ck_adversary_context_01` uses slug `att_ck_adversary_context`, which can never match. The project's slug is `attck_adversary_context`.
- **13 clean-retrieval misses:** the target section isn't in the clean top 3. Reword the question to name the concept, or keep it and report it in a separate stratum.
- **6 references need splitting into atomic facts:** long execution flows, and raw CAPEC consequence dictionaries.
- **1 reference is too thin:** dns spoofing prerequisites, "On/In Path Device".
- **Near-duplicate flood prerequisites:** the four DDoS prerequisite references differ only in the protocol name.
