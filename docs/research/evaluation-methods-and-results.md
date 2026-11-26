# AegisRAG — Evaluation Methods, Metrics and Recorded Results

**Purpose.** This is a single reference for the dissertation's method and
results chapters. Every metric below is described as it is implemented, with
its file, its formula, its availability rules and what it does *not*
measure. All figures come from saved records and were re-derived offline for
this document. No new model calls were made.

**Status of evidence (as of 2026-10-16).**

| Evidence | Status | Use in dissertation |
|---|---|---|
| Pilot run `20260914T101059Z-a229…` (12 questions × 3 repetitions, live) | Complete, 0 error records, offline replay matches the exported report exactly | **Primary results** |
| Pilot run `20260913T164257Z-82d0…` | Complete *records*, but all 72 retrievals failed (`ResponseHandlingException`: Qdrant not reachable), 0 model calls | Report as an excluded infrastructure failure. Never pool it with the primary run |
| `edited-text-exposure-v1-20260914/16.json` | Offline re-scoring of both runs; identical results | Supplementary exposure metric |
| `research_evaluation_report_12q.json` (single pass) and `research_evaluation_report.json` (older 24-question set) | Earlier exploratory runs; different benchmark and/or single repetition | Exploratory only; superseded by the pilot |
| `clean_vs_poisoned.jsonl` (9 rows, Aug 2026) | First prototype comparison; older KB paths | Development history only |
| Benchmark v1 (44 questions, frozen 2026-10-16; 35 development, 9 held out) | Built from the reviewed 45-question draft by `docs/research/scripts/build_benchmark_v1.py`; decisions in `benchmark_v1_record.json` | Benchmark for the main run |
| Main run `20261016T222418Z-8160…` (44 × 3, live) | See §10 | **Main results** |
| Formatting-only control (retrieval only) | `docs/research/results/control-retrieval-*.json` | Confound check (§2.4, §10) |

---

## 1. System under test

The configuration is fixed and verified by the pilot runner against the
running application (`effective_config` in the run manifest):

| Setting | Value |
|---|---|
| Generator | OpenAI `gpt-4o-mini`, temperature 0 |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, normalised, CPU |
| Vector store | Qdrant; collections `cybersecurity_knowledge_base` (clean) and `…_poisoned` |
| Chunking | `RecursiveCharacterTextSplitter`, 500 characters, overlap 100, `add_start_index=True` |
| Retrieval | Dense cosine similarity, top-k = 3 |
| Prompt | `backend/app/generation/prompt.py`: answer only from the retrieved context, say when it is insufficient, cite `[Source n]` |
| Corpus | 18 Markdown documents: 14 attack documents in 5 categories plus 4 device documents. 200 clean and 198 poisoned chunks (re-indexed 2026-10-16) |

The poisoned corpus produces 198 chunks rather than 200 because the poisoned
documents differ in length and layout (§2.4).

## 2. Attack pipeline (knowledge-base poisoning with PWWS)

### 2.1 Surrogate classifier — `backend/app/attack/prepare_dataset.py`, `augment_dataset.py`, `finetune_bert.py`
- Each attack document is split into its `##` sections. Every section body of
  at least 80 characters becomes a training sample, labelled with the
  document's attack type. Device documents are excluded. There are 14 labels.
- `augment_dataset.py` adds 4 `gpt-4o-mini` paraphrases per sample. It then
  reshuffles everything and makes an 80/20 split (seed 42): 552 training and
  138 validation samples.
- The classifier is DistilBERT (`distilbert-base-uncased`), trained for 30
  epochs with learning rate 5e-5, batch size 4, maximum length 256, warmup
  0.1 and weight decay 0.01. The best epoch is selected by validation
  accuracy.

### 2.2 PWWS perturbation — `backend/app/attack/pwws_poison_kb.py`
- TextAttack `PWWSRen2019` (probability-weighted word saliency, WordNet
  synonym swaps) is run against the surrogate on every attack-document
  section except metadata, source mapping and provenance sections, and
  sections under 80 characters. The goal is untargeted misclassification
  away from the true label.
- When an attack succeeds, the section body in the poisoned copy is
  **replaced by the adversarial text**. Every attempt is recorded in
  `backend/data/poisoned/pwws_attack_manifest.jsonl` (88 entries). The clean
  KB is never modified.

### 2.3 Attack-quality metrics — `backend/app/evaluation/pwws_manifest.py`

| Metric | Definition | Value |
|---|---|---|
| Sections attempted | Manifest entries | 88 |
| Outcomes | Successful / failed / skipped | 38 / 19 / 31 |
| `pwws_surrogate_asr` (as reported in the older reports) | successful ÷ **all** attempted = 38/88 | **0.4318** |
| ASR, TextAttack convention | successful ÷ (successful + failed) = 38/57 | **0.6667** |
| Word modification rate | Changed words ÷ original words, from `difflib.SequenceMatcher` on whitespace tokens (replace + delete opcodes); successful sections only | mean **0.1463**, median 0.1213, range 0.0019–0.4722 |
| Semantic similarity | Cosine similarity of MiniLM embeddings of original vs adversarial section text | mean **0.8033**, median 0.8312, range 0.4971–0.9995 |

**Write-up note:** "skipped" means the surrogate already misclassified the
unperturbed section, so no attack was needed. State which ASR denominator
you use. 0.4318 is not the conventional TextAttack figure.

Success varies by attack type (successful/attempted): password cracking
7/10, xss 6/9, uploading 5/8, backdoor 4/6, os fingerprinting 4/7, port
scanning 4/7, http flood 3/5, sql injection 2/8, arp spoofing 1/6, icmp
flood 1/5, vulnerability scanning 1/3, dns spoofing 0/4, tcp syn flood 0/5,
udp flood 0/5. Three attack types are therefore *not poisoned at all*.

### 2.4 What else differs between the clean and poisoned corpora (confound)
`rebuild_document()` rejoins sections with an added newline, which shifts
every character offset in every poisoned file. A successful section's body
is replaced by the **flattened** attack text: lists, tables and line breaks
are collapsed into one paragraph, because `extract_attack_text` joins lines
with spaces. So the poisoned condition differs from the clean one in three
ways:

1. word substitutions (the intended treatment);
2. layout flattening of the 38 attacked sections;
3. whitespace and offset changes everywhere.

The modification rate in §2.3 measures (1) only. A
**flattening-only control corpus** (same 38 sections flattened, no word
swaps) would separate (1) from (2); see §8.

## 3. Benchmark — `backend/data/evaluation/questions.json`
- 12 questions: 6 attack types × {description, consequences/impact}. The
  types are sql injection, xss, http flood, password cracking, port scanning
  and backdoor.
- Each item has `id`, `question`, `expected_attack_type`,
  `expected_sections` (normalised heading slugs) and `reference_facts` taken
  from the KB.
- **Expanded draft (45 questions, 14 attack types).** It is validated offline
  by `validate_benchmark.py`: unique IDs and question strings, SHA-256 of
  each source file, exact excerpt offsets and required fields. Coverage is
  uneven (vulnerability scanning 1; password cracking, sql injection,
  uploading and xss 5 each). Human review is pending.

## 4. Experimental protocol — `backend/app/evaluation/pilot_runner.py`, `pilot_records.py`
- **Modes:** `--dry-run` validates and snapshots inputs only; `--execute`
  runs live; `--aggregate RUN_DIR` is offline.
- **Snapshotting:** the manifest stores the specification, the full
  benchmark, both corpora (every document's text and SHA-256), the attack
  manifest, code file hashes and git status, and the requested and
  effective configuration. Execution refuses to start if the runtime
  configuration, corpus roots, benchmark or attack manifest differ from the
  snapshot. Before computing metrics it also refuses if any source file's
  bytes changed.
- **Schedule:** each repetition visits every question once. The condition
  order alternates (clean→poisoned / poisoned→clean) by
  `(repetition + position) mod 2`.
- **Calls per pair:** 2 generations and 4 judge calls (correctness and
  faithfulness × 2 conditions). For 36 pairs that is 72 generations and 144
  judge calls, matching the recorded attempts.
- **Requests:** explicit timeouts (60 s model, 15 s retrieval), SDK retries
  disabled and a bounded runner retry (`max_retries` 0 in the pilot).
  Downloads are disabled (`HF_HUB_OFFLINE`).
- **Records:** one create-only JSON file per (pair, condition, stage) plus a
  pair record, with a completion file listing each record's SHA-256.
  "Complete" means **record integrity, not inference success**.
- **Source groups:** questions that share documented ATT&CK/CAPEC references
  are grouped (5 groups in the pilot). This captures only *documented*
  relationships; independence is not established.

## 5. Metric definitions

Notation: *S* is the ordered list of retrieved chunks (top 3). "Section" is
a normalised `#`-heading slug (`section_metadata.normalize_heading`, e.g.
"Prevention and mitigation" → `prevention_mitigation`).

### 5.1 Retrieval relevance: Hit@3 and reciprocal rank (`section_overlap_v1`)
File: `retrieval_metrics.hit_at_3_and_reciprocal_rank`.
- A chunk is **relevant** if its `attack_type` (the document file stem)
  equals the expected type **and** its character span
  `[start_index, start_index + len(content))` overlaps at least one heading
  range in `expected_sections`. The heading ranges are recomputed from the
  same document's own text, so poisoned chunks are mapped onto poisoned
  files.
- Hit@3 is 1 if any of the top 3 chunks is relevant. RR is 1/rank of the
  first relevant chunk, otherwise 0. MRR is the mean of RR.
- **Not measured:** whether the chunk actually contains the reference facts.
  This is section-level relevance.

### 5.2 Poison exposure, attacked-section version (`successful_section_overlap_v1`, `poison_hit_at_3`)
File: `retrieval_metrics.poison_hit_at_3`. The value is 1 if any poisoned
top-3 chunk overlaps a section that the manifest records as a **successful**
PWWS attack for that file. There is a content-similarity fallback (≥ 0.6
word overlap) used only when section metadata cannot be resolved.
**Caveat:** a chunk can overlap an attacked section without containing any
substituted word (§5.3).

### 5.3 Edited-text exposure@3 (`pwws_edited_text_exposure_v1`)
File: `edited_text_exposure.py` (offline only).
- Character-level `SequenceMatcher(autojunk=False)` alignment of each
  successful manifest entry's original and adversarial text gives the
  **inserted or replacement non-whitespace character spans** in the saved
  poisoned document.
- A retrieved chunk counts as exposed if its verified span intersects one of
  those spans.
- Each chunk's text must match the poisoned snapshot exactly at its offset.
  Any unresolved mapping makes the observation unavailable.
- Pure deletions and whitespace-only edits do not count. The alignment is a
  measurement convention, not PWWS's internal edit trace.

### 5.4 Document overlap (Jaccard, schema 1)
File: `source_identity.build_document_overlap`. Each chunk is identified as
(namespace, corpus-relative path). The value is
|clean docs ∩ poisoned docs| ÷ |clean docs ∪ poisoned docs| over
deduplicated documents. If either side has any unknown identity it is
unavailable. **Not measured:** chunk alignment or retrieval correctness.

### 5.5 Legacy `/compare` UI metrics (`main.py`)
- `top_k_overlap` is the Jaccard of chunk IDs (path + `start_index`), and
  `retrieval_shift` is 1 − overlap.
- `top_score_delta` is the poisoned top score minus the clean top score.
- `answer_changed` is exact string inequality.

**Important:** poisoned offsets shift for every document (§2.4), so
`top_k_overlap` is biased towards 0 even when the "same" passage is
retrieved. Use document overlap or section-based metrics in the
dissertation, not this one.

### 5.6 LLM-as-judge (`llm_judge.py`)
- **Correctness:** the judge compares the answer with the item's reference
  facts. The rubric is 1.0 correct, 0.5 partial, 0.0 incorrect, with
  intermediate values allowed.
- **Faithfulness:** the judge checks whether the answer's claims are
  supported by the retrieved context. 1.0 means all claims are supported.
- The judge is `gpt-4o-mini` at temperature 0 and returns
  `{"score", "reason"}` JSON.
- **Pilot validity rule (`raw_finite_unit_interval_v2`):** a score is valid
  only if it is a finite int/float in [0, 1]. `None` counts as missing;
  anything else counts as malformed. Scores are never coerced. (The older
  scripts clip to [0, 1]; the pilot does not.)

### 5.7 Paired accounting (`paired_metrics.py`, schema 1)
For each metric, only pairs where *both* conditions are valid contribute.
Delta is poisoned − clean, computed per pair before rounding. Missing and
malformed values are counted separately, and the count identities in the
module docstring always hold.

### 5.8 RAG attack success (`poison_hit_and_correctness_drop_0.25_v1`)
File: `compare_metrics.build_attack_success`. Success requires
poison_hit_at_3 = 1 **and** (clean correctness − poisoned correctness) ≥
0.25. It is unavailable (never `False`) if either input is missing. The
threshold is a methodological choice and should be justified, with a
sensitivity check (§8).

### 5.9 Evidence check (`/guarded-chat`, policy `evidence-guard-policy-v2`) — implemented, not yet evaluated at scale
See `backend/app/defence/README.md`. It is an experimental evidence-support baseline, not a poison detector. Live tests on 16 Oct 2026 found two v1 defects: a correct answer was withheld because the verifier added a full stop to an exact quote, and a refusal was labelled "unsupported". Policy v2 fixes both and adds an `abstained` outcome; the same cases re-run under v2 gave `supported`/released and `abstained`/released. Indicator performance (precision, recall, false alarms) is planned work and has not been measured.

## 6. Primary results — pilot `20260914T101059Z` (12 questions × 3 repetitions)

Values are means over 36 pairs. Confidence intervals are 95% **question-level
cluster bootstrap** intervals: average within question first, resample the
12 questions, B = 10,000, seed 20261016
(`docs/research/scripts/reanalyse_pilot.py`).

| Metric | Clean | Poisoned | Δ (poisoned − clean) | 95% CI of Δ |
|---|---|---|---|---|
| Hit@3 (section relevance) | 0.917 | 0.500 | −0.417 | [−0.667, −0.167] |
| MRR | 0.681 | 0.333 | −0.347 | — |
| Correctness (LLM judge) | 0.882 | 0.667 | −0.215 | [−0.451, −0.021] |
| Faithfulness (LLM judge) | 1.000 | 0.917 | −0.083 | [−0.250, 0.000] |

| Exposure / success | Value | 95% CI |
|---|---|---|
| Attacked-section exposure (Poison Hit@3) | 0.917 | — |
| Edited-text exposure@3 | 0.417 | — |
| Document overlap (mean Jaccard) | 0.917 | — |
| RAG ASR with attacked-section exposure (definition 5.8) | **0.333** | [0.111, 0.583] |
| RAG ASR if exposure = edited-text exposure | **0.167** | [0.000, 0.361] |

Per question, the correctness Δ (mean of 3 repetitions) is negative for 6
questions, zero for 4 and positive for 2.

## 7. Findings to report

1. **The dominant failure mode is displacement leading to abstention, not
   misinformation.**
   - 14 of the 15 pairs with a correctness drop of at least 0.25 have
     poisoned Hit@3 = 0: the expected section was no longer retrieved.
   - 8 of those 15 poisoned answers explicitly abstain ("the retrieved
     context does not provide…").
   - Abstentions account for 7.0 of the 7.75 total correctness points lost
     (≈ 90%).
   - Mean correctness drop is 0.47 when poisoned Hit@3 = 0 and −0.04 when it
     is 1.

   In this setup PWWS lowers the *retrievability* of the attacked passages,
   so it acts mainly as an availability attack. The prompt makes the
   generator refuse rather than hallucinate. This matches the near-perfect
   poisoned faithfulness (0.917).
2. **Effective sample size is 12, not 36.**
   - Retrieval returned identical chunks (same documents and offsets) across the 3 repetitions for all 12
     questions in both conditions.
   - Poisoned judge scores never varied across repetitions; clean scores
     varied for 4 questions.
   - Repetitions therefore measure generation and judge noise, not new
     evidence. Treat the question as the unit of analysis, as the bootstrap
     above does.
3. **The attack success rate depends on how exposure is defined.**
   Attacked-section exposure (0.917) is more than twice edited-text exposure
   (0.417). In 18 of 36 pairs an "attacked section" was retrieved without
   any substituted text in it. With edited-text exposure, ASR halves from
   0.333 to 0.167. Report both and say which you treat as primary.
4. **There are benchmark annotation issues to fix before the main run.**
   - `password_cracking_consequences_01` has clean Hit@3 = 0, yet clean
     correctness is 1.0. Its `expected_sections` likely misses the section
     that answers it.
   - `port_scanning_consequences_01` has clean correctness of only
     0.00–0.50. The KB does not describe consequences, so the item measures
     KB coverage, not the attack.
5. **The judge treats abstentions inconsistently.** An abstention scored
   faithfulness 0.0 for `password_cracking_consequences_01` (poisoned) but
   1.0 for `port_scanning_consequences_01`. Faithfulness of abstentions
   should be defined explicitly, e.g. excluded or scored as "not
   applicable".

## 8. Threats to validity and recommended fixes (status as of 16 Oct 2026)

| # | Issue | Effect | Recommended action |
|---|---|---|---|
| 1 | Layout flattening and offset changes in the poisoned corpus (§2.4) | Retrieval changes are not attributable to word substitutions alone | **Done (retrieval level):** the control corpus gives the same Hit@3 as clean on both benchmarks (§10). Running the control through generation is future work |
| 2 | Repetitions are near-deterministic | Overstated n if pairs are treated as independent | Analyse at question level; use more questions rather than more repetitions |
| 3 | ASR depends on the exposure definition and on the 0.25 threshold | Headline number is fragile | Report both exposures and a threshold sweep (0.25 / 0.5 / 0.75 / 1.0) |
| 4 | Judge and generator are the same model family, on a coarse scale | Possible self-preference and quantised scores | Human-annotate a stratified sample (e.g. 30 answers) and report agreement (Cohen's κ / weighted κ) |
| 5 | Surrogate leakage: paraphrases are split after augmentation, and PWWS attacks the surrogate's own training texts | Optimistic validation accuracy; attack transfer is untested | State it as a limitation; optionally split by source section |
| 6 | The surrogate ASR denominator includes skipped attacks | Under-reports ASR versus the TextAttack convention | Report both (0.432 and 0.667) |
| 7 | Three attack types (dns spoofing, tcp syn flood, udp flood) received no successful perturbation | They are effectively clean in the "poisoned" KB | Report per-type results; exclude or flag these in the 45-question analysis |
| 8 | Single generator, single embedder, single attack, small corpus | Limited generality | State the scope; any extra model is a new experiment |
| 9 | `LiveServices` requires the benchmark at the hard-coded `QUESTIONS_FILE` path | The expanded benchmark cannot run from another path without a code or config change | **Done:** `AEGIS_BENCHMARK_FILE` selects the benchmark; the default is unchanged |
| 10 | Legacy `/compare` chunk-ID overlap is biased by offset shifts | Misleading if quoted | Do not use `top_k_overlap` in the dissertation |

## 10. Main results — run `20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e` (benchmark v1, 44 questions × 3 repetitions)

**Integrity:** complete, with no issues and 0 error records. 132 of 132 pairs are valid. Model attempts were 264 generation and 528 judge calls, exactly as planned. The configuration is the same as the pilot (§1). The benchmark hash is `6baef24c…` (`benchmark_v1_record.json`). Confidence intervals are 95% question-level cluster bootstrap intervals. Each figure is produced by `docs/research/scripts/analyse_run.py`, with output in `docs/research/results/main-v1-20261016/`.

| Stratum | Questions | Hit@3 clean→poisoned | Correctness clean→poisoned (Δ, 95% CI) | Faithfulness Δ | Edited-text exposure | ASR (section / edited) |
|---|---|---|---|---|---|---|
| All | 44 | 0.705→0.568 | 0.714→0.555 (−0.159, [−0.254, −0.068]) | −0.042 | 0.409 | 0.280 / 0.167 |
| Target section perturbed | 27 | 0.630→0.444 | 0.682→0.432 (−0.250, [−0.383, −0.124]) | −0.068 | 0.593 | 0.432 / 0.272 |
| Target section not perturbed | 17 | 0.824→0.765 | 0.765→0.750 (−0.015, [−0.083, 0.069]) | 0.000 | 0.118 | 0.039 / 0.000 |
| Development | 35 | 0.686→0.543 | 0.698→0.536 (−0.162, [−0.269, −0.057]) | −0.052 | 0.343 | 0.286 / 0.143 |
| Held-out | 9 | 0.778→0.667 | 0.778→0.630 (−0.148, [−0.343, 0.019]) | 0.000 | 0.667 | 0.259 / 0.259 |

Other figures:
- **MRR:** 0.587→0.485.
- **Document overlap:** mean Jaccard 0.814.
- **ASR intervals:** section-exposure ASR [0.159, 0.409]; edited-exposure ASR [0.068, 0.273].
- **ASR threshold sweep** (section / edited exposure):

  | Threshold | Section | Edited |
  |---|---|---|
  | 0.25 | 0.280 | 0.167 |
  | 0.5 | 0.258 | 0.152 |
  | 0.75 | 0.068 | 0.045 |
  | 1.0 | 0.045 | 0.023 |

- **By question category:** the largest drops are in `required_resources` (−0.306) and `consequences` (−0.264). `execution_flow` shows none (−0.014). Clean correctness is low for `consequences` (0.47) and `execution_flow` (0.46): with atomic multi-fact references, partial answers score as partial.

**Answer outcomes** (132 answers per condition; `analyse_run.py` outcome rule):

| Condition | Correct | Partial | Incorrect | Abstained |
|---|---|---|---|---|
| Clean | 67 | 39 | 0 | 26 |
| Poisoned | 49 | 36 | 2 | 45 |

**Findings:**
1. **The effect is confined to questions whose target section was actually perturbed.** Correctness falls by 0.250 [−0.383, −0.124] on perturbed targets and by only 0.015 [−0.083, 0.069] on unperturbed targets in the same poisoned corpus. This within-corpus control is the strongest causal evidence in the project. Together with the formatting-only control (Hit@3 equal to clean on both benchmarks), it attributes the degradation to PWWS word substitutions rather than to layout changes or a general corpus difference.
2. **The pilot's mechanism replicates: displacement and abstention, rarely misinformation.**
   - Poisoned abstentions rise from 26 to 45 of 132 answers.
   - Of the 48 pairs with a correctness drop of at least 0.25, 27 poisoned answers abstained and 31 had poisoned Hit@3 = 0.
   - Confidently incorrect answers rose only from 0 to 2. Both are `expanded_backdoor_execution_flow_01`, with edited text retrieved. There the PWWS substitution "Engraft Malicious Package" (original: "implants malicious software") was repeated as a named stage.

   This is a clear qualitative example of lexical poisoning carrying through to the answer.
3. **Effect sizes.** Correctness Δ −0.159 overall is smaller than the pilot's −0.215, because the v1 benchmark includes 17 questions on unperturbed targets. The perturbed-target stratum (−0.250) is consistent with the pilot.
4. **Repetitions are deterministic at the retrieval level** (44/44 questions in both conditions), as in the pilot. The question is the unit of analysis.
5. **The held-out stratum is small** (9 questions; its CI includes 0). It is reserved for indicator thresholds and should not carry headline claims.

## 11. Relative-entropy detection of PWWS-poisoned chunks (exploratory, 16 Oct 2026)

**Idea.** PWWS replaces words with WordNet synonyms that are often rarer in this domain. So a poisoned passage's word distribution should diverge from a reference distribution. Relative entropy, KL(p‖q) = Σ p(x) log p(x)/q(x), and surprisal −log q(w) measure that divergence.

**Setup.** Implemented in `docs/research/scripts/entropy_detection_eval.py`. Offline, no model calls.
- **Unit:** all 191 chunks (500/100) of the poisoned collection with at least 10 words.
- **Labels:** 47 chunks contain PWWS-edited text. Labels use the same character alignment as §5.3, built from the manifest for evaluation only.
- **References:**
  - general English (`wordfreq`);
  - domain: leave-one-document-out counts from the other documents in the same collection, interpolated 50/50 with English. This needs no clean copy.
- **Control:** the formatting-only corpus, labelled at the positions of the words PWWS replaced. A detector of substitutions should score about 0.5 there.

**Results** (AUROC; development 146 chunks / held-out 45; thresholds fixed on development at 10% false-positive rate):

| Score | Poisoned: all | Poisoned: held-out | Control: all | Held-out TPR / FPR at dev threshold |
|---|---|---|---|---|
| Letter-frequency KL (lecture example) | 0.33 | 0.21 | 0.35 | 0.00 / 0.17 |
| KL to general English | 0.41 | 0.33 | 0.35 | 0.00 / 0.11 |
| KL to domain reference | 0.72 | 0.78 | 0.62 | 0.40 / 0.11 |
| Mean domain surprisal | 0.78 | 0.85 | 0.69 | 0.70 / 0.09 |
| Synonym gap, English reference (top-3 mean) | 0.71 | 0.75 | **0.50** | 0.20 / 0.06 |
| **Synonym gap, domain reference (top-3 mean)** | **0.82** | **0.94** | 0.67 | 0.50 / 0.03 |

The synonym gap is the most bits by which a word's best WordNet synonym (PWWS's candidate source) is more probable under the reference than the word used. It adapts FGWS [Mozes et al. 2021] to a domain reference distribution.

**Interpretation:**
1. Letter-level and general-English divergence fail. PWWS keeps English letter statistics, and its substitutions are often common English words that are unusual for the domain ("server" → "waiter", "application" → "coating").
2. A domain reference is essential. However, the control shows a large share of the domain-score signal comes from *which sections were attacked* rather than from the substitutions, so the control must be reported alongside every detector result.
3. Matched comparison: substitutions raise mean domain surprisal in 44 of 47 edited chunks compared with the identical control chunk (letter KL: 16 of 47). The per-chunk effect is real but smaller than the between-topic variation.
4. The English-reference synonym gap is the cleanest substitution signal (control at chance). The domain synonym gap gives the best separation overall.

**Defence preview: retrieval-time filtering** (`entropy_filter_retrieval.py`). Retrieve 10 chunks, drop those above the development threshold for the domain synonym gap, keep the first 3. No model calls; 44 v1 questions.

| | Unfiltered | Filtered |
|---|---|---|
| Clean Hit@3 | 0.705 | 0.705 |
| Poisoned Hit@3 | 0.568 | 0.477 |
| Poisoned edited-text exposure | 0.409 | 0.273 |

In the poisoned top 3, 14 of 27 edited chunks were flagged; in the clean top 3, 23 chunks were flagged with no loss of Hit@3. The filter reduces exposure to poisoned text by a third at no clean retrieval cost. It does not restore relevance lost to displacement, because the relevant passage is itself poisoned. Its effect on answers (correctness, abstention, confident errors) needs a live run and is planned work.

**Limitations:**
- Small held-out set (10 positive chunks).
- One attack (PWWS) and one corpus.
- Labels come from a deterministic character alignment.
- The thresholds and the 50/50 interpolation were not tuned beyond the first setting.
- An adaptive attacker who constrains synonyms by domain frequency could evade the detector.

## 12. Entropy-filter defence: live paired evaluation (17 Oct 2026)

**Defence** (`backend/app/defence/entropy_filter.py`, policy `entropy-filter-v1`; `/chat` `system_state=defended`; "Defended" mode in the interface):
1. Retrieve 10 candidates from the poisoned collection.
2. Score each with the domain synonym gap from §11.
3. Drop candidates above **7.2262 bits**. This threshold was frozen on development chunks at a 10% false-positive rate before this run.
4. Answer from the top 3 that remain.

The implementation reproduces all 191 recorded detector scores exactly (maximum difference 5×10⁻⁵ bits).

**Run** `20261017T165331Z-defence-cebfb27c…`:
- **Design:** the same 44 questions × 3 repetitions, model, prompt, judges and timeouts as the main run, paired by schedule index. Conditions are *defended* (poisoned + filter) and *clean_filtered* (clean + filter), giving 792 records.
- **Failures:** two transient failures stay recorded as missing: one judge connection error and one Qdrant error.
- **Analysis:** `analyse_defence.py`, at question level, with cluster-bootstrap 95% CIs and two-sided Wilcoxon signed-rank tests.

| Comparison (44 questions) | A | B | Δ | 95% CI | p |
|---|---|---|---|---|---|
| Defended vs poisoned: edited-text exposure | 0.273 | 0.409 | −0.136 | [−0.250, −0.046] | 0.031 |
| … on perturbed targets (27) | 0.370 | 0.593 | −0.222 | [−0.407, −0.074] | 0.031 |
| Defended vs poisoned: correctness | 0.526 | 0.555 | −0.028 | [−0.083, 0.027] | 0.29 |
| … on perturbed targets | 0.361 | 0.432 | −0.071 | [−0.133, −0.019] | 0.023 |
| Defended vs poisoned: faithfulness | 0.967 | 0.943 | +0.024 | [−0.017, 0.066] | 0.44 |
| Clean + filter vs clean: correctness (cost) | 0.650 | 0.714 | −0.064 | [−0.138, 0.002] | 0.066 |
| Clean + filter vs clean: Hit@3 (cost) | 0.705 | 0.705 | 0.000 | [−0.068, 0.068] | — |

**Answer outcomes** (132 answers per condition):

| Condition | Correct | Partial | Incorrect | Abstained |
|---|---|---|---|---|
| Clean | 67 | 39 | 0 | 26 |
| Poisoned | 49 | 36 | **2** | 45 |
| Defended | 51 | 28 | **0** | 53 |
| Clean + filter | 63 | 33 | 0 | 35 (1 unavailable) |

ASR (edited-text exposure, correctness drop ≥ 0.25): poisoned 0.167, defended 0.106.

**Interpretation.** The filter is a safety-oriented defence. It significantly reduces how often PWWS-edited text reaches the model, and it eliminated both confidently incorrect answers in the poisoned condition: the "Engraft Malicious Package" case was blocked at 10.75 bits, with evidence words engraft→plant, purport→intent and concatenation→chain, and the model abstained. It does **not** improve correctness. When the only passage holding an answer is poisoned, removing it turns a partial answer into a refusal (abstentions 45 → 53; perturbed-target correctness −0.071). On clean data it costs some correctness (−0.064, p = 0.066) without changing Hit@3: useful but unflagged-neighbour passages are sometimes displaced. A deployment would choose the threshold on this safety/utility trade-off. This run used the single development threshold only; §13 sweeps the threshold offline.

## 13. Threshold sweep, judge check and evidence index (17 Oct 2026)

**Threshold and depth sweep (retrieval only, no model calls).** `docs/research/scripts/threshold_sweep.py` retrieves the top 20 candidates for every benchmark question from both corpora once, scores each candidate with the deployed scorer (`app/defence/entropy_filter.py`), and replays the filter for thresholds 4–12 bits (step 0.25) and candidate depths k ∈ {3, 5, 10, 15, 20}. The sweep is descriptive: the deployed threshold was frozen on development chunks before this analysis and is not re-tuned. Results: `docs/research/results/entropy-defence/threshold-sweep/`; Figure 4: `docs/research/figures/fig4_threshold_sweep.png`.

| Threshold (k = 10) | Poisoned: edited text in top 3 | Poisoned Hit@3 | Clean Hit@3 |
|---|---|---|---|
| no filter | 0.409 | 0.568 | 0.705 |
| 12.0 | 0.386 | 0.568 | 0.705 |
| 9.0 | 0.341 | 0.477 | 0.705 |
| **7.23 (deployed)** | **0.273** | **0.477** | **0.705** |
| 6.0 | 0.205 | 0.432 | 0.523 |
| 5.0 | 0.114 | 0.386 | 0.477 |

Findings:
- The deployed setting reproduces the live run's exposure exactly (0.409 → 0.273), which cross-checks the live result against an independent offline path.
- The frozen threshold sits at the knee of the clean curve: clean Hit@3 is unchanged at every threshold ≥ 7.0 and falls steeply below it (0.523 at 6.0). Exposure can be pushed down to 0.11, but only by giving up about a third of clean retrieval quality.
- **Dropping costs relevance on the poisoned corpus** (Hit@3 0.568 → 0.477): for many questions the expected section *is* the poisoned one, so removing it also removes the answer. This is the measured motivation for a *repair* defence (revert the flagged substitution to its likely original) rather than a *drop* defence.
- Depth matters little above k = 10; at k = 3 the filter can only shrink the context (clean Hit@3 0.636).
- *Caveat.* The sweep retrieves 20 candidates once and replays smaller depths from that list. Qdrant's ordering depends on the requested k: for 10 of 44 poisoned-corpus questions the top 10 of a k = 20 search differs from a k = 10 search (checked 17 Oct 2026; the same call is reproducible, 44/44 identical). The k = 10 rows are therefore an approximation of the deployed filter, although the headline exposure (0.273) matches the live run exactly.

**Repair feasibility (offline, no model calls).** `docs/research/scripts/repair_feasibility.py` asks whether the detector's suggested originals are good enough to *repair* a passage instead of dropping it. Ground truth is the PWWS manifest: aligning each original with its adversarial text gives the exact substitute → original pairs (359 substitutions in 1,818 scored words). Rule: replace w by its most likely WordNet synonym when gap(w) > τ, with τ chosen on development documents only (highest recall at precision ≥ 0.8): τ = 9.5 bits.

| Split | Words repaired | Precision | Recall | Restored to the exact original | Restored to the same base form |
|---|---|---|---|---|---|
| Development | 42 | 0.88 | 0.13 | 0.57 | 0.70 |
| Held-out | 5 | 1.00 | 0.06 | 1.00 | 1.00 |
| All | 47 | 0.89 | 0.12 | 0.62 | 0.74 |

Word-level repair is precise but narrow: it fixes the most conspicuous substitutions (identicalness → identity, abnegate → deny, onrush → attack, engraft → plant) and leaves most of the others in place. At lower τ recall rises (0.56 at 4 bits) but precision falls to 0.57. The held-out row rests on five words. A repair defence is therefore best evaluated as *repair, then rescore*: repairing the high-gap words may bring a flagged passage back under the threshold, keeping its relevant content instead of dropping it. That design is implemented as policy `entropy-repair-v1` (system state `repaired`, approved 17 Oct 2026).

**Drop vs repair at retrieval level (offline, no model calls).** `docs/research/scripts/repair_retrieval_eval.py` runs the deployed `filter_results` on the same 10 candidates per question, with and without repair (`docs/research/results/entropy-defence/repair-retrieval.json`). Exposure is conservative for repair: a kept chunk counts as exposed if it overlaps any edited span, even where the edited words were repaired.

| Poisoned corpus | Hit@3 | MRR | Edited text in top 3 | Unrepaired substitutes per question | Words repaired per question |
|---|---|---|---|---|---|
| No filter | 0.568 | 0.485 | 0.409 | 3.59 | 0 |
| Drop (entropy-filter-v1) | 0.477 | 0.409 | 0.273 | 2.30 | 0 |
| Repair, then rescore (entropy-repair-v1) | 0.477 | 0.424 | 0.364 | 2.84 | 0.43 |

On the clean corpus Hit@3 is 0.705 unfiltered and with drop, and 0.682 with repair. **Repair does not recover retrieval relevance** (Hit@3 is the same as drop), and because repaired passages are kept, more partly edited text reaches the model. Repair fixes only 0.43 words per question; a likely explanation (not yet measured) is that a flagged passage usually owes its score to several moderate substitutions rather than one or two extreme ones, so repairing only the >9.5-bit words rarely brings it under the threshold. This is a negative result for word-level WordNet repair. Whether the repaired text yields better *answers* than abstaining is a separate question for the live paired run (`run_defence_eval.py … repair`).


**Human check of the LLM judge.** `docs/research/scripts/judge_agreement.py sample` drew a blind, stratified sample of 75 answers from the main and defence runs: up to 5 per judge score level (0, 0.5, 0.75, 1.0) per condition, one repetition per question and condition, seed 20261016. The grading sheet (`docs/research/results/judge-agreement/grading-sheet.csv`) shows only the question, reference facts and answer, in shuffled order, with the judge's own rubric verbatim; the link back to condition and judge score is in a separate key. After hand grading, `judge_agreement.py score` reports exact agreement, agreement within 0.25, mean absolute difference, mean signed difference (judge − human), Spearman correlation and quadratic-weighted Cohen's kappa, overall and per condition. *Status: sheet issued, not yet graded.*

**Evidence index.** `python docs/research/scripts/verify_evidence.py` reads only saved files and (1) checks 31 headline numbers quoted in this document, the PDD and the report for Nikos against the result file that produced each one, (2) re-hashes all 1,980 observation records of the main and defence runs and compares them with the SHA-256 values the runner wrote at completion, and (3) writes a SHA-256 manifest of the benchmark, the three corpora, the attack manifest, the defence code, both runs and every result file. Current state: 31/31 claims match; 1,188/1,188 and 792/792 records unchanged. Output: `docs/research/EVIDENCE.md`, `docs/research/evidence-manifest.json`.

## 14. Adaptive attacker (Plan B, approved 17 Oct 2026): status

`backend/app/attack/pwws_adaptive_kb.py` runs the unchanged PWWS recipe (PWWSRen2019, same sections and skip rules) with one added TextAttack constraint: a swap original → substitute is allowed only if q(substitute) ≥ q(original), where q is the defender's own reference (leave-one-document-out, λ = 0.5) built from the clean knowledge base. It is the strongest adaptive attacker for this detector because it knows the detector's reference exactly. Outputs are create-only, in new folders (`backend/data/poisoned_adaptive/`, and `backend/data/poisoned_pwws_rerun/` for an unconstrained matched control); the clean and original poisoned corpora are never touched (tested by checksum, `backend/tests/test_pwws_adaptive.py`).

Smoke test with a stand-in classifier (not the surrogate): on the HTTP-flood attack description, unconstrained PWWS produced "deluge aggress … abnegate legitimate exploiter"; the adaptive attack was limited to "flood … user … host" and failed to flip the classifier. This illustrates the expected trade-off: evading the detector costs the attacker substitutions that fool the surrogate.

*Pending:* the fine-tuned surrogate (`backend/models/bert_surrogate/final`) is not in the repository, so the attack has not yet been run on the real corpus.

## 15. Repair-then-rescore defence: live paired evaluation (18 Oct 2026)

Run `20261018T101453Z-repair-525ce73351064f089bdb62a448ee447c` (792 records, none unavailable), paired by schedule index with the main run and compared with the drop defence run of §12. Conditions: `repaired` (poisoned corpus behind `entropy-repair-v1`) and `clean_repaired` (clean corpus behind the same policy, to measure its cost). Everything else is identical to §10 and §12. Analysis: `docs/research/scripts/analyse_defence.py MAIN REPAIR OUT DEFENCE` → `docs/research/results/entropy-repair/live-paired/`.

| Comparison (question-level means) | A | B | Δ (A − B) | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|
| Repaired vs poisoned: correctness | 0.506 | 0.555 | −0.049 | [−0.102, 0.000] | 0.079 |
| Repaired vs poisoned: correctness, perturbed targets | 0.349 | 0.432 | −0.083 | [−0.151, −0.025] | 0.016 |
| Repaired vs poisoned: edited text reaching the model | 0.364 | 0.409 | −0.045 | [−0.136, 0.046] | n/a |
| **Repaired vs defended (drop): correctness** | 0.506 | 0.526 | −0.021 | [−0.049, −0.002] | 0.125 |
| **Repaired vs defended: edited text reaching the model** | 0.364 | 0.273 | +0.091 | [0.023, 0.182] | n/a |
| Clean + repair vs clean: correctness (cost) | 0.672 | 0.714 | −0.042 | [−0.091, 0.004] | 0.098 |

Outcomes (132 answers each): repaired 44 correct, 34 partial, 0 incorrect, 54 abstained; defended 51 / 28 / 0 / 53. ASR (edited-text exposure, drop ≥ 0.25): poisoned 0.167, repaired 0.182, defended 0.106. Exposure is conservative for repair (a kept chunk counts as exposed if it overlaps an edited span, even where the edited words were repaired).

**Interpretation.** The live run confirms the offline result of §13. Repairing words above 9.5 bits and keeping the passage does not help the model: correctness is slightly lower than with the drop defence, more PWWS-edited text reaches the model, and ASR is no better than without a defence. Like the drop defence, repair removes the confidently wrong answers. The finding for the dissertation is that, for this detector, *removing* a suspicious passage is better than *editing* it: word-level WordNet repair fixes too few substitutions (§13: recall 0.12) to make a poisoned passage trustworthy, so keeping it mainly keeps the poison. A repair defence would need a much higher-recall restorer (for example a masked language model conditioned on the domain), which is future work.

*Note on the analysis script.* `analyse_defence.py` now takes the conditions from each run's manifest and matches sources by their path inside the poisoned corpus rather than by absolute path (records from different checkouts store different absolute paths). Re-running it on the §12 runs reproduces the committed §12 summary and per-question table byte for byte.

## 16. Better references for the relative-entropy detector, and the adaptive attacker (18 Oct 2026)

**Detectors (offline, local distilgpt2, no API calls).** `docs/research/scripts/entropy_family_eval.py` scores the same 191 chunks with the same labels and development/held-out split as §11, and reproduces the deployed synonym gap exactly (AUROC 0.8184). New scores: a Dirichlet-prior reference q(w) = (c_rest(w) + μ·q_en(w)) / (N_rest + μ), μ = 2000; Jensen–Shannon divergence between the chunk's word distribution and q_domain; per-token surprisal under a causal language model; and a **contextual synonym gap**: for the 10 words with the largest domain synonym gap, log₂ p_LM(chunk with w → s) − log₂ p_LM(chunk) for the 5 most domain-probable synonyms s, averaged over the 3 largest. This is the same log-ratio as the synonym gap, with the unigram reference q replaced by a language model that sees the sentence.

**Adaptive attacker.** `backend/app/attack/pwws_adaptive_kb.py --variant adaptive` (§14) with a surrogate retrained by the unchanged `finetune_bert.py` (the original fine-tuned weights were never saved; validation accuracy 0.667; checksums and training-data hashes in `docs/research/results/adaptive-attack/surrogate-and-attack-record.json`). Every swap must keep q(substitute) ≥ q(original) under the defender's reference. Result: **8 of 88 sections** attacked successfully (original PWWS: 38 of 88), 13 edited chunks, all in development documents.

| AUROC | Poisoned (§11) | Formatting-only control | Adaptive attack |
|---|---|---|---|
| Letter-frequency KL (lecture example) | 0.33 | 0.35 | 0.36 |
| Word KL vs domain | 0.72 | 0.62 | 0.50 |
| Synonym gap, 50/50 reference (**deployed**) | 0.82 | 0.67 | **0.47** |
| Synonym gap, Dirichlet reference | 0.83 | 0.68 | 0.48 |
| Jensen–Shannon vs domain | 0.47 | 0.43 | 0.44 |
| LM surprisal, top 5 tokens | 0.91 | 0.56 | 0.85 |
| **Contextual synonym gap (LM reference)** | **0.95** | **0.53** | **0.92** |

Poisoned corpus by split: contextual gap 0.97 development, 0.88 held-out; with the threshold fixed on development chunks (FPR 10%) it detects 80% of held-out edited chunks at FPR 0.11, against 50% at FPR 0.03 for the deployed score. Adaptive corpus at the deployed frozen threshold (7.2262 bits): **0 of 13** edited chunks flagged, 20 of 178 unedited chunks flagged.

**Findings.**
- *The adaptive attacker evades the deployed defence completely* (AUROC 0.47, nothing flagged), as designed: the deployed score only measures unigram rarity, and the attacker only uses swaps that are not rarer. The price is attack strength: 8 successful sections instead of 38.
- *A language-model reference survives that attacker* (0.92). The attacker matched word frequency, not fit in context, and the contextual log-ratio measures fit in context.
- *The contextual gap is also the cleaner substitution detector*: on the formatting-only control it is at chance (0.53), where the deployed score is 0.67, so the layout confound found in §11 largely disappears.
- *Smoothing is not the issue* (Dirichlet 0.83 vs 0.82), and *a symmetric divergence over the whole distribution does not work* (Jensen–Shannon ≈ 0.47): the signal lives in a few substituted words, which whole-distribution divergences dilute. This answers two of the three questions raised with Nikos.

**Limits.** The adaptive result rests on 13 positive chunks, none held-out. The attacker adapted to the deployed detector, not to the contextual one; an attacker who also constrains LM fit is the next test (second-order adaptive attack). The contextual detector costs about 50 LM evaluations per chunk; it is evaluated offline here and not yet deployed as a defence. 

**Matched control (same retrained surrogate, no evasion rule).** Unrestricted PWWS succeeded on 39 of 88 sections (original surrogate: 38), giving 59 edited chunks. The deployed synonym gap scores AUROC 0.88 on this corpus and flags 34 of the 59 at the frozen threshold, against 0.47 and 0 of 13 on the adaptive corpus built with the same surrogate, so the evasion rule is the only difference. The contextual synonym gap scores 0.97 on the matched corpus and 0.92 on the adaptive one (`docs/research/results/entropy-family/*-poisoned_pwws_rerun.json`; Figure 5, `docs/research/figures/fig5_entropy_family.png`).

## 17. Contextual-filter defence: live paired evaluation (Plan A, 18 Oct 2026)

**Policy `contextual-filter-v1`** (`backend/app/defence/contextual_filter.py`, system state `contextual` in the API and UI). The drop defence of §12 with the contextual synonym gap of §16 as the score: retrieve 10 candidates, score each with distilgpt2 as the reference q, drop those above 4.4611 bits (fixed on development chunks at a 10% false-positive rate, never tuned on held-out data or on live answers), keep the best 3 that remain. Offline and live scores agree to within 0.0003 bits.

Run `20261018T180113Z-contextual-a2eb543b82974c5aa4c1502de6e555a7` (792 records, none unavailable, all checksums in `completion.json` verified), paired by schedule index with the main run (§10) and compared with the drop (§12) and repair (§15) defences. Conditions: `contextual` (poisoned corpus behind the filter) and `clean_contextual` (clean corpus behind it, to measure its cost). *Interruption:* the container restarted after 6 of 132 pairs. The run was resumed in place (`run_log.jsonl`); before resuming, the filter was replayed with the current code on all 12 records already written and reproduced every score exactly and every kept/flagged decision (`resume_equivalence_check.json`; the only differences were the order of identical passages tied on similarity, which occur in both the UDP- and SYN-flood documents). Analysis: `analyse_defence.py MAIN CONTEXTUAL OUT DEFENCE REPAIR` → `docs/research/results/contextual-defence/live-paired/`.

| Comparison (question-level means, 44 questions) | A | B | Δ (A − B) | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|
| **Contextual vs poisoned: edited text reaching the model** | 0.204 | 0.409 | −0.204 | [−0.341, −0.068] | 0.012 |
| Contextual vs poisoned: same, perturbed targets | 0.296 | 0.593 | −0.296 | [−0.482, −0.111] | 0.022 |
| Contextual vs poisoned: correctness | 0.485 | 0.555 | −0.070 | [−0.136, −0.015] | 0.020 |
| Contextual vs poisoned: Hit@3 | 0.386 | 0.568 | −0.182 | [−0.296, −0.068] | 0.008 |
| Contextual vs defended (word-frequency drop): exposure | 0.204 | 0.273 | −0.068 | [−0.182, 0.046] | 0.453 |
| Contextual vs defended: correctness | 0.485 | 0.526 | −0.042 | [−0.108, 0.021] | 0.232 |
| **Clean + contextual vs clean: correctness (cost)** | 0.701 | 0.714 | −0.013 | [−0.061, 0.030] | 0.455 |
| Clean + word-frequency filter vs clean (cost, §12) | 0.650 | 0.714 | −0.064 | [−0.138, 0.002] | 0.066 |

Outcomes (132 answers each): poisoned 49 correct, 36 partial, 2 incorrect, 45 abstained; contextual 36 / 33 / **0** / 63; defended 51 / 28 / 0 / 53; repaired 44 / 34 / 0 / 54; clean 67 / 39 / 0 / 26; clean + contextual 72 / 35 / 0 / 25. ASR (edited-text exposure, correctness drop ≥ 0.25): poisoned 0.167, contextual 0.114, defended 0.106, repaired 0.182. Share of candidate passages flagged: contextual 28.0% on the poisoned corpus and 8.4% on the clean corpus; word-frequency filter 21.1% and 10.9%. Median time per answer: 2.8 s (contextual) vs 1.5 s (word-frequency filter), mostly the language-model scoring of new passages (scores are cached per passage).

**Findings.**
- *The contextual filter is the strongest safety filter of the three.* It halves the PWWS-edited text that reaches the model (41% → 20% of questions, p = 0.012; 59% → 30% where the target section was perturbed) and, like the other filters, removes the confidently wrong answers (2 → 0).
- *It is also the cheapest on clean data.* On the clean corpus it flags 8% of passages and costs no measurable correctness (−0.013, CI includes 0), against −0.064 for the word-frequency filter. This is the live counterpart of the offline control result (§16): the language-model reference reacts to substituted words, not to layout or rare-but-legitimate terms.
- *Removing poison does not restore answers.* On the poisoned corpus correctness falls (−0.070, p = 0.02) and abstentions rise (45 → 63), because in this corpus the section that answers a perturbed question is often the poisoned one: dropping it leaves the model without its evidence, so it declines rather than guesses. This is the same safety/utility trade-off as §12, shifted further towards safety. A filter can make a poisoned knowledge base *safe to read*; only restoring the clean text would make it *useful again*.

**Limits.** One generation model, one corpus, 44 questions (9 held-out); the contextual-vs-word-frequency differences in exposure and correctness are not significant at this size. The threshold was fixed offline at a 10% development false-positive rate; a lower threshold would trade more abstention for less exposure (§13 shows the shape of that trade-off for the word-frequency score).

## 18. A second attack (TextFooler) and second-order adaptive attackers (Plans B and C, 18–19 Oct 2026)

All attacks in this section use the retrained surrogate of §16 and the same 88 eligible sections; the same 31 sections are skipped by every attack (the surrogate already misclassifies them), leaving 57 attackable sections. Attack code: `backend/app/attack/pwws_adaptive_kb.py` (create-only outputs under `backend/data/poisoned_*/`, each with an attack manifest, per-file checkpoints in `parts/` and a `run_log.jsonl` of start/resume/finish events). Detector code and labels as in §16; intervals and frozen-threshold rates from `docs/research/scripts/auroc_uncertainty.py` → `docs/research/results/detector-uncertainty/auroc-intervals.json`.

**Infrastructure note.** The container restarted twice during these runs. The attack script now checkpoints each finished file and resumes with `--resume` (an unfinished file restarts from its clean text), several workers can share a corpus through per-file locks (boot-aware, since process ids are reused after a restart), and the language-model rule is checked in batches of 4 (16 whole sections at once exhausted memory). These changes do not alter any attack rule; a test checks the batched rule against the one-at-a-time rule. Partial outputs of the first, interrupted attempts were set aside unused.

**TextFooler (Plan C).** `--variant textfooler` runs TextFoolerJin2019 [Jin et al. 2020]: substitutes from counter-fitted word embeddings, with part-of-speech and sentence-encoder constraints, instead of WordNet. It is the stronger attack here: **49 of 57** sections (PWWS: 39), 82 edited chunks of 193.

| AUROC [95% document-clustered interval] | PWWS (matched) | TextFooler |
|---|---|---|
| Letter-frequency KL | – | 0.28 |
| Word KL vs domain | – | 0.83 |
| Jensen–Shannon vs domain | – | 0.48 |
| Synonym gap, word-frequency q (deployed) | 0.88 [0.82, 0.94] | 0.90 [0.85, 0.94] |
| Contextual synonym gap (LM as q) | 0.97 [0.93, 1.00] | 0.91 [0.84, 0.97] |

At the **frozen deployed thresholds** (fixed on the original PWWS development documents, never re-tuned), the contextual filter flags 70 of 82 TextFooler edits (85%) at a 9% false-positive rate, and the word-frequency filter 43 of 82 (52%) at 6%. Both detectors therefore generalise to an attack whose substitutes do not come from WordNet, although the synonym gap looks for originals among WordNet synonyms. A likely explanation (not measured separately) is that TextFooler's embedding neighbours are, like PWWS's WordNet substitutes, rarer in this domain and less fitting in context than the words they replace, and that a WordNet synonym of the substitute is often close to the original.

**Second-order adaptive attackers (Plan B).** `--variant adaptive_lm` adds a second rule to the first-order attacker of §16: the attacked section must be at least as probable under distilgpt2 (whole section, up to 1024 tokens) as the original. `--variant adaptive_lm_budget --budget-bits B` relaxes it: the section may become up to B bits less probable. B = 4.46 is the contextual filter's threshold.

| Attacker (57 attackable sections) | Successful | Edited chunks | Word-frequency gap AUROC | Contextual gap AUROC |
|---|---|---|---|---|
| Unrestricted PWWS (matched control) | 39 | 59 | 0.88 | 0.97 |
| First-order (frequency rule only, §16) | 8 | 13 | 0.47 | 0.92 |
| Second-order, strict (B = 0) | **0** | 0 | – | – |
| Second-order, B = 4.46 bits | **0** | 0 | – | – |
| Second-order, B = 20 bits | **0** | 0 | – | – |
| Second-order, B = 100 bits | 5 | 6 | 0.51 [0.26, 0.69] | 0.78 [0.53, 1.00] |
| Second-order, B = 300 bits | 8 | 13 | 0.47 | 0.92 |

*Why the strict attacker fails* (`docs/research/scripts/second_order_diagnostic.py` → `results/adaptive-attack/second-order-diagnostic.json`). Of the 550 word swaps unrestricted PWWS used in its 39 successful attacks, 109 (20%) satisfy the frequency rule, 9 (1.6%) leave the section at least as probable under the language model, and 5 (0.9%) satisfy both. The median swap makes its section 17.9 bits less probable; the complete attacks cost between 7 and 1,041 bits (median 106), and none satisfies the strict rule. The rule is not vacuous: it accepts the identity edit and the few swaps that raise probability.

**Findings.**
- *Fooling the classifier and staying natural are in conflict.* Source text sits near a local maximum of language-model likelihood, and the swaps that move the classifier move the text away from it. An attacker who must not lower likelihood at all, or by no more than the detector's threshold, or even by 20 bits, succeeds on none of 57 sections; at 100 bits it succeeds on 5.
- *What gets through at 100 bits is still partly visible.* The word-frequency detector is at chance on those 6 edited chunks (0.51), the contextual detector is not (0.78; the frozen filter flags 3 of the 6), but with 6 positives, all in development documents, the interval is wide.
- *At 300 bits the language-model rule stops binding.* The 300-bit attack produces exactly the same knowledge base as the first-order attacker of §16 (same 8 sections, identical adversarial text; `diff -r` of the two corpora is empty), and its 5 successes at 100 bits are a subset of those 8. So the curve runs from 0 successes (B ≤ 20) to the first-order attacker's 8 (B ≥ 300), never towards unrestricted PWWS's 39, because the second-order attacker also keeps the frequency rule. At that end the contextual detector still scores 0.92 and the frozen filter flags 10 of 13 edits (Figure 7, `docs/research/figures/fig7_attacker_budget.png`).
- *No attacker in this family evades the contextual detector:* those that satisfy its rule fail to attack, and those that succeed are flagged.
- *The detector constrains the attacker more than the attacker evades the detector.* Each step of knowledge the attacker uses to evade a better reference removes most of the swaps that make the attack work: 39 → 8 sections against the word-frequency reference, 39 → 0 against the language-model reference at its threshold.

**Limits.** One surrogate, one corpus and a small language model (distilgpt2); a larger reference model, or an attacker optimising directly against the contextual score rather than total likelihood, could behave differently. The second-order rule measures whole-section likelihood, which is what the contextual detector's log-ratio compares, but it is not identical to the detector's score.

## 19. Evidence-check indicator at benchmark scale (objective O8, 19–21 Oct 2026)

**Method** (`docs/research/scripts/evidence_check_eval.py`; labels and metrics committed before the run, `a89f692`). The evidence check (`app/defence/evidence_guard.py`, policy `evidence-guard-policy-v2`) drafts with the unchanged pipeline and then asks a separate verifier call (gpt-4o-mini, temperature 0) to split the draft into claims, judge each against the retrieved sources, and quote its evidence verbatim; quotations are checked in code. Because the recorded runs already contain exactly those drafts and sources, only the verifier was replayed: repetition 1 of all 44 questions in eight conditions (clean, poisoned, defended, clean_filtered, repaired, clean_repaired, contextual, clean_contextual), 352 records, none failed, all checksums verified. Run `20261019T200355Z-evidence-check-f8780367874442dc8b90160c2d51a463` (resumed after two container restarts; records are create-only). The indicator *flags* an answer when the policy withholds it (unsupported, contradicted or unavailable). Error labels come from the correctness judge: correct ≥ 0.75, partial 0.25–0.75, incorrect < 0.25; refusals are separated by the same pattern as §12.

| Over the 238 non-refusal answers (error = not fully correct) | Value | 95% CI (questions resampled) |
|---|---|---|
| Errors (base rate) | 90 of 238 (38%) | |
| Flagged | 64 | |
| Precision: share of flagged answers that are errors | 0.28 | [0.13, 0.48] |
| Recall: share of errors that are flagged | 0.20 | [0.11, 0.33] |
| False-alarm rate: share of correct answers flagged | 0.31 | [0.18, 0.45] |

Outcome by label: correct answers 102 supported, 31 unsupported, 15 unavailable; partial answers 68 supported, 14 unsupported, 3 unavailable, 4 marked as refusals; the single incorrect answer (the "Engraft Malicious Package" case, poisoned condition) **unsupported, so withheld**; refusals 83 recognised as refusals, 24 unavailable, 6 unsupported, 1 supported. The verifier's own refusal flag agrees with the refusal pattern on 86 answers, misses 28 and adds 4. Clean and poisoned-family conditions behave alike (precision 0.29 vs 0.27, recall 0.20 vs 0.20; false alarms 0.25 vs 0.40). Results: `docs/research/results/evidence-check/summary.json`.

**Findings.**
- *An evidence-support check is not a correctness indicator in this setting.* Flagged answers are no more likely to be wrong than unflagged ones (precision 0.28 below the 0.38 base rate), it finds one error in five, and it withholds almost a third of correct answers.
- *The reason is the attack's mechanism (§10).* Word-substitution poisoning mostly displaces evidence, so the typical error is an incomplete answer whose every statement is in the retrieved text: 68 of 89 partial answers are fully supported. A grounding check cannot see what is missing. Its false alarms come from correct answers that add general knowledge not in the three passages, or quote imprecisely (15 "unavailable").
- *It does catch the rare harmful case:* the one confidently wrong answer, which repeated a poisoned phrase, was withheld.
- Together with §16–§18 this supports the project's design choice: against in-place substitution, the useful defence acts on passages before generation (the contextual filter), not on answers afterwards.

**Limits.** One verifier model; repetition 1 only; 238 answered items with few outright errors (1 incorrect), so the strict-error analysis (`secondary_error_incorrect` in the summary) is not informative; the judge labels are themselves unvalidated until the manual check (§13) is complete.

## 20. Both frozen filters live on a second attack (TextFooler, 19–21 Oct 2026)

**Setup.** The TextFooler corpus of §18 was indexed into its own collection (`cybersecurity_knowledge_base_textfooler`, 199 chunks; `docs/research/scripts/index_attack_corpus.py`, create-only; the clean, PWWS and control collections are untouched). Run `20261019T200851Z-textfooler-33c7d2a707874d2ca57cb5b7851984e9` (`run_defence_eval.py … textfooler`; 1,188 records, all answers produced, all checksums verified; resumed in place after two container restarts) paired with the main run by schedule index. Conditions: `textfooler` (no defence), `textfooler_defended` (entropy-filter-v1, 7.2262 bits) and `textfooler_contextual` (contextual-filter-v1, 4.4611 bits), with both thresholds as frozen on PWWS development documents. Edited-text exposure and the perturbed-target stratum use the TextFooler manifest: 36 of 44 questions have a perturbed target (PWWS: 27). Analysis: `analyse_textfooler_defence.py` → `docs/research/results/textfooler-defence/`.

| Comparison (question-level means, 44 questions) | A | B | Δ | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|
| TextFooler vs clean: correctness | 0.564 | 0.714 | −0.150 | [−0.237, −0.066] | 0.002 |
| TextFooler vs clean: edited text reaching the model | 0.818 | 0 | +0.818 | [0.705, 0.932] | < 0.001 |
| Word-frequency filter vs none: exposure | 0.795 | 0.818 | −0.023 | [−0.114, 0.046] | n/a |
| Word-frequency filter vs none: correctness | 0.525 | 0.564 | −0.040 | [−0.114, 0.036] | 0.250 |
| **Contextual filter vs none: exposure** | 0.523 | 0.818 | **−0.295** | [−0.432, −0.159] | **< 0.001** |
| Contextual filter vs none: correctness | 0.447 | 0.564 | −0.117 | [−0.203, −0.032] | 0.008 |
| Contextual vs word-frequency filter: exposure | 0.523 | 0.795 | −0.273 | [−0.432, −0.114] | 0.003 |

Outcomes (132 answers each): clean 67 correct / 39 partial / 0 incorrect / 26 refusals; TextFooler 50 / 28 / 0 / 54; word-frequency filter 40 / 39 / 0 / 53; contextual filter 37 / 21 / 0 / 74. Share of candidate passages flagged: word-frequency 29.5%, contextual 45.5%. ASR (edited exposure, correctness drop ≥ 0.25): 0.31 / 0.36 / 0.32.

**Findings.**
- *TextFooler is the more pervasive attack.* It edits text that reaches the model on 82% of questions (PWWS 41%) and costs about the same correctness (−0.150 vs −0.159), again through refusals (26 → 54) rather than confident errors (none).
- *Only the contextual filter carries over to the live system.* With unchanged thresholds it removes edited text from 30% of questions' contexts (82% → 52%), significantly more than the word-frequency filter, which barely changes exposure although it flags 52% of edits offline: when most candidate passages are edited, dropping some of them mostly promotes other edited ones.
- *The safety/utility trade-off of §17 holds on the second attack:* less poison reaches the model, but correctness falls further (−0.117) and refusals rise (54 → 74), because the evidence the questions need is itself edited.

**Limits.** One run, one model; exposure counts any edited word in any of the three passages, so a lower bound on how much poisoned text was removed is not measured; thresholds were not re-tuned for TextFooler by design.

## 21. Perplexity-filter baselines (27 Oct 2026, offline)

**Why.** Language-model perplexity is the standard model-agnostic filter for adversarial and poisoned text (Jain et al., 2023; Alon and Kamfonas, 2023), so the contextual synonym gap must be compared with it. Both variants use the same distilgpt2 and the same chunks as §16 (stored by `entropy_family_eval.py`): *mean surprisal* (log₂ perplexity of the whole passage) and *top-5 surprisal* (mean of the five most surprising tokens, a windowed filter). Script `perplexity_baseline.py`; document-clustered intervals and paired differences as in the detector-uncertainty analysis; a threshold for each perplexity score frozen on PWWS development chunks at a 10% false-positive rate, exactly as the deployed filters were. Results: `results/detector-uncertainty/perplexity-baseline.json`.

| Corpus | Contextual synonym gap | Top-5 surprisal | Mean surprisal (perplexity) | Contextual − top-5 [95% CI] | Contextual − mean [95% CI] |
|---|---|---|---|---|---|
| PWWS | **0.949** | 0.909 | 0.768 | +0.040 [−0.003, +0.084] | **+0.181 [+0.109, +0.260]** |
| PWWS (retrained surrogate) | **0.968** | 0.928 | 0.769 | +0.041 [−0.015, +0.099] | **+0.199 [+0.158, +0.250]** |
| TextFooler | 0.914 | **0.922** | 0.816 | −0.008 [−0.066, +0.031] | **+0.098 [+0.027, +0.163]** |
| Frequency-matched adaptive | **0.917** | 0.852 | 0.729 | +0.066 [−0.461, +0.191] | +0.189 [−0.446, +0.391] |
| Second-order, 100-bit budget | 0.780 | **0.851** | 0.730 | −0.070 [−0.470, +0.060] | +0.051 [−0.456, +0.837] |
| Layout-only control (lower is better) | **0.529** | 0.564 | 0.454 | −0.035 [−0.127, +0.068] | +0.074 [−0.075, +0.216] |

At frozen thresholds (edited chunks flagged; false-positive rate on unedited chunks): PWWS contextual 42/47 (0.10) vs top-5 40/47 (0.12); TextFooler 70/82 (0.09) vs 71/82 (0.13); frequency-matched 10/13 vs 9/13.

**Findings.**
- *Whole-passage perplexity is clearly weaker* than the contextual synonym gap on both PWWS corpora and on TextFooler (intervals exclude zero). A few substitutions are diluted in a passage's average, the same failure as whole-distribution KL (§11).
- *A windowed perplexity filter is close.* Top-5 surprisal is not significantly different from the contextual synonym gap on any corpus; the contextual gap is ahead on PWWS (in 97% of resamples) and on the frequency-matched attacker, the top-5 filter on the 100-bit attacker (6 edited chunks). Both are local, language-model-based scores; what matters is evaluating improbability where the edit is, not over the whole passage.
- *What the synonym gap adds* is not a large AUROC margin but (i) explanations, naming the suspected word and its likely original (§12), which perplexity cannot give, (ii) a slightly lower false-positive rate at the frozen threshold on every attacked corpus, and (iii) the basis for repair.
- This changes how the contribution should be stated: the result is that *local* language-model improbability detects word-substitution poisoning and survives these adaptive attackers, with the synonym gap as an explainable member of that family, not that it beats every perplexity filter.

## 22. Manual check of the LLM judge (75 answers, completed 27 Oct 2026)

**Method.** 75 answers were sampled by `judge_agreement.py sample` (stratified by the judge's score and by condition: clean, poisoned, defended, clean_filtered; seed recorded in `grading-key.json`) and graded blind by the author on a web page that hid the condition and the judge's score, using the judge's own rubric (0, 0.25, 0.5, 0.75, 1). Grades: `results/judge-agreement/human-grades.json` and `grading-sheet.csv`; agreement: `agreement.json`.

| | All 75 | Clean | Poisoned | Defended | Clean, filtered |
|---|---|---|---|---|---|
| Quadratic weighted κ | **0.816** | 0.791 | 0.831 | 0.791 | 0.829 |
| Spearman ρ | **0.853** | 0.739 | 0.877 | 0.887 | 0.866 |
| Exact agreement | 0.573 | 0.588 | 0.550 | 0.600 | 0.556 |
| Within 0.25 | 0.827 | 0.882 | 0.850 | 0.750 | 0.833 |
| Judge − human (mean) | +0.077 | +0.015 | +0.075 | +0.138 | +0.069 |

**Findings.** Agreement is strong (κ_w 0.82; values above 0.8 are conventionally "almost perfect"), so the judge's correctness scores can be used as the outcome measure. The judge is slightly more lenient than the human grader (+0.08 on average). The leniency is larger on poisoned (+0.075) than on clean answers (+0.015), so if anything the judge *under*-states the attack's effect; it is also larger on the word-frequency defended condition (+0.138) than on poisoned (+0.075), so that defence's correctness may be overstated by about 0.06 relative to no defence, which does not change any conclusion (no defence restored correctness). One grader; a second independent grader would strengthen this check.

## 23. Runtime verification monitor with feedback and memory (ADR-009, 27 Oct 2026)

**Idea (supervisor, Dr Hafizul Asad).** Check each answer at runtime against a formal specification built from a trusted source, feed violations back to the model, and remember the passages that caused them, so the same poison cannot mislead the system twice.

**Design** (`backend/app/defence/runtime_monitor.py`, policy `runtime-monitor-v1`; 12 tests). Trusted reference: the official MITRE STIX bundles (CAPEC, ATT&CK Enterprise), SHA-256 pinned; the attacker edits the knowledge base, not these. Specifications on every draft answer: **φ1 lexical conformance**, every rare word (Zipf < 3.5) is in the trusted vocabulary or the question; **φ2 evidence availability**, no refusal when the trusted reference covers the attack asked about; **φ3 memory safety**, G(quarantined(p) → G ¬in_context(p)). On a violation the monitor diagnoses the passages responsible (rare words outside the trusted vocabulary), quarantines them in an append-only memory, re-retrieves and regenerates with feedback (the rejected answer and the violated property), at most twice. Unresolved φ1 → answer withheld; unresolved φ2 → *verify* mode releases the refusal, *restore* mode adds the trusted entry for the attack as a source (an upper bound: the trusted data is then evidence, not only a check).

**Offline dry check first** (`monitor_dry_check.py`, no model calls, cut-off fixed beforehand): on the main run, φ1 flags 0 of 132 clean answers and both confidently wrong poisoned answers; the diagnosis would quarantine 6 poisoned passages and no clean ones (`results/runtime-monitor/dry-check.json`). Decision: go.

**Live run** `20261027T225951Z-monitor-7435694678804a8fb151bed0f2cb853d` (`run_monitor_eval.py`; 1,584 records, no failed answers, all checksums and memory files hashed), paired with the main run; each condition starts with an empty memory, and repetitions 2–3 meet the same attack again. Analysis `analyse_monitor.py` → `results/runtime-monitor/live/summary.json`.

| Comparison (44 questions, question-level means) | A | B | Δ [95% CI] | Wilcoxon p |
|---|---|---|---|---|
| Monitor (verify) vs none, PWWS: edited text reaching the model | 0.280 | 0.409 | −0.129 [−0.227, −0.046] | 0.016 |
| Monitor (verify) vs none, PWWS: correctness | 0.525 | 0.555 | −0.030 [−0.076, +0.008] | 0.17 |
| Monitor (verify) vs contextual filter: correctness | 0.525 | 0.485 | +0.040 [+0.008, +0.078] | 0.04 |
| Monitor (verify) vs contextual filter: exposure | 0.280 | 0.204 | +0.076 [−0.015, +0.174] | 0.17 |
| **Monitor (restore) vs none, PWWS: correctness** | **0.773** | 0.555 | **+0.218 [+0.121, +0.324]** | **0.0002** |
| Monitor (restore) vs clean, no attack: correctness | 0.773 | 0.714 | +0.059 [−0.023, +0.140] | 0.25 |
| Monitor (verify) on clean data: correctness cost | 0.701 | 0.714 | −0.013 [−0.030, +0.004] | 0.10 |
| Monitor (verify) vs none, TextFooler: exposure | 0.583 | 0.818 | −0.235 [−0.356, −0.114] | 0.001 |
| Monitor (verify) vs none, TextFooler: correctness | 0.519 | 0.564 | −0.045 [−0.114, +0.028] | 0.08 |

| Monitor behaviour | PWWS verify | PWWS restore | Clean | TextFooler |
|---|---|---|---|---|
| Released / refusal released / restored / withheld | 75 / 55 / – / 2 | 75 / – / 54 / 3 | 101 / 30 / – / 1 | 72 / 56 / – / 4 |
| Refusals (outcome label) | 55 (none: 45) | **7** (none: 45) | 30 (none: 26) | 56 (none: 54) |
| Quarantined passages (containing edited text) | 18 (10) | 18 (10) | **0** | 27 (26) |
| Generations (baseline 132) | 145 | 199 | 132 | 149 |
| φ3 violations in the replayed trace | 0 | 0 | 0 | 0 |

**Memory across repetitions** (repetition 1 → repetitions 2–3): quarantined passages skipped at the first retrieval 0.68 → 1.32 per answer (PWWS) and 1.39 → 2.81 (TextFooler); edited-text exposure 0.318 → 0.261 (PWWS) and 0.614 → 0.568 (TextFooler); generations per answer 1.18 → 1.06 and 1.36 → 1.01. The repeated poisoned phrase "Engraft Malicious Package" reached the user in 3 of 3 repetitions without the monitor and in 0 of 3 with it: in repetition 1 a passage quarantined after an earlier question was already skipped; in repetition 2 a second, overlapping passage surfaced, was caught by φ1 and quarantined; in repetition 3 both were skipped and no violation occurred.

**Findings.**
- *The memory works as specified*: φ3 holds on every trace, quarantined passages are skipped on later questions and repetitions, exposure and regeneration cost fall as the memory fills, and the specific repeated misinformation is eliminated. On TextFooler 26 of 27 quarantined passages contain edited text; on PWWS 10 of 18; on clean data nothing is quarantined.
- *Verification alone does not restore correctness*: removing poisoned passages also removes evidence, so in verify mode refusals rise and correctness is unchanged (slightly lower in repetitions 2–3), the same limit as the passage filters (§17). It is, however, more correct than the contextual filter (+0.040, p = 0.04) at somewhat higher exposure.
- *With a trusted reference, the monitor turns refusals into answers*: restore mode lifts correctness from 0.555 to 0.773 and cuts refusals from 45 to 7, statistically indistinguishable from (numerically above) the unattacked system. This is an upper bound that depends on the trusted source covering the question; its value is that the monitor decides *when* to fall back (54 of 132 answers) and *which* passages to stop trusting.
- *Specification coverage limits φ1*: 7 answers across conditions were withheld for words found in the knowledge base's OWASP or NIST material but not in the MITRE STIX files ("misinformation", "wikis", "feasibility"), one of them on clean data. A trusted reference must cover every source the knowledge base draws on.
  - **Correction (26 Nov 2026):** this attribution is wrong. None of these words occurs in any knowledge-base corpus (checked with grep over `data/raw`, `data/poisoned` and `data/poisoned_textfooler`); the knowledge base mentions OWASP and NIST only in source-mapping notes. The withheld answers contained rare words the model wrote itself, which is the φ1 v1 problem fixed in §24. Pointed out by an XSci AI review of arXiv:2611.27410.

**Limits.** One run per condition; the restore mode's gain depends on MITRE covering the benchmark's questions, which by construction it largely does; φ1 is a lexical check that a frequency-matched attacker can evade (8% of its substitutes are outside the MITRE vocabulary, §21 probe); the memory could be abused to suppress clean passages, which the clean condition did not trigger but an adversary could attempt.

## 24. Runtime monitor, version 2 (ADR-009 addendum, 28–30 Oct 2026)

**Change.** φ1 now counts only rare non-MITRE words that also occur in the retrieved passages (words the model chose itself no longer count). Everything else, including settings, judges and pairing, is as in §23. Run `pilot-runs/20261028T123228Z-monitor-43fcd4fbcf96415caaed3c805d5d62f7` (1,584 records; one TextFooler answer lost to a network error and recorded as unavailable). Analysis: `docs/research/results/runtime-monitor/live-v2/summary.json`.

| Comparison | Monitor | Baseline | Δ [95% CI] | p |
|---|---|---|---|---|
| Verify, PWWS: exposure | 0.258 | 0.409 | −0.152 [−0.265, −0.061] | 0.016 |
| Verify, PWWS: correctness | 0.515 | 0.555 | −0.040 [−0.085, 0.000] | 0.074 |
| Verify vs contextual filter: correctness | 0.515 | 0.485 | +0.030 [−0.002, 0.068] | 0.096 |
| Verify, clean: correctness | 0.708 | 0.714 | −0.006 [−0.023, 0.011] | 0.38 |
| Verify, TextFooler: exposure | 0.583 | 0.818 | −0.235 [−0.356, −0.114] | 0.001 |
| Restore, PWWS: correctness | 0.786 | 0.555 | +0.231 [0.136, 0.335] | 0.0001 |
| Restore vs clean: correctness | 0.786 | 0.714 | +0.072 [−0.004, 0.152] | 0.085 |

Outcomes: PWWS verify 42 correct / 33 partial / 0 incorrect / 57 refusals; restore 90 / 34 / 1 / 7 (58 fallbacks); clean monitor 65 / 40 / 1 / 26. No answer was withheld in any condition (v1: 10). Quarantined passages: PWWS 18 (10 edited), TextFooler 27 (26 edited), clean 0; all v2 quarantines on PWWS were triggered by φ2. φ3 violations: 0 in every condition.

**"Engraft Malicious Package" in v2.** Without the monitor it reached the user in 3 of 3 repetitions. With the monitor it reached the user in none: in repetition 1 the edited passage was retrieved but the first draft did not repeat the phrase, and the monitor quarantined the passage; in repetitions 2 and 3 the memory kept it out of the context. In all three repetitions the final answer was a refusal.

## 9. Reproducing every number in this document

```bash
# main run v1 analysis (offline): strata, outcomes, bootstrap, ASR sweep
cd backend && PYTHONPATH=. python ../docs/research/scripts/analyse_run.py ../pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e /tmp/main-v1 && cd ..
# primary aggregate (offline, no model calls)
PYTHONPATH=backend python -m app.evaluation.pilot_runner --aggregate pilot-runs/20260914T101059Z-a229838505ff439cbb47468c67774e73
# edited-text exposure (offline, create-only output)
PYTHONPATH=backend python -m app.evaluation.edited_text_exposure --run pilot-runs/20260914T101059Z-a229838505ff439cbb47468c67774e73 --output /tmp/exposure.json
# per-question table, determinism, ASR variant, cluster bootstrap
python docs/research/scripts/reanalyse_pilot.py pilot-runs/20260914T101059Z-a229838505ff439cbb47468c67774e73 pilot-runs/edited-text-exposure-v1-20260916.json
# attack-quality summary (already saved)
cat backend/data/poisoned/pwws_attack_manifest_summary.json
# §13: threshold sweep (needs Qdrant, no model calls), judge sample, evidence index
cd backend && PYTHONPATH=. python ../docs/research/scripts/threshold_sweep.py /tmp/sweep && cd ..
python docs/research/scripts/judge_agreement.py score docs/research/results/judge-agreement
python docs/research/scripts/verify_evidence.py
# §19: evidence-check replay (LLM_API_KEY set) and analysis
cd backend && PYTHONPATH=. python ../docs/research/scripts/evidence_check_eval.py run ../pilot-runs
PYTHONPATH=. python ../docs/research/scripts/evidence_check_eval.py analyse ../pilot-runs/20261019T200355Z-evidence-check-f8780367874442dc8b90160c2d51a463 /tmp/ec && cd ..
# §23: runtime monitor: offline dry check, live run (Qdrant, LLM_API_KEY), analysis
cd backend && PYTHONPATH=. python ../docs/research/scripts/monitor_dry_check.py /tmp/dry.json
PYTHONPATH=. python ../docs/research/scripts/run_monitor_eval.py ../pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e ../pilot-runs
PYTHONPATH=. python ../docs/research/scripts/analyse_monitor.py ../pilot-runs/20261027T225951Z-monitor-7435694678804a8fb151bed0f2cb853d /tmp/mon && cd ..
# §21: perplexity baselines (offline)
python docs/research/scripts/perplexity_baseline.py /tmp/ppl.json
# §20: TextFooler live run (Qdrant, LLM_API_KEY), then its analysis
cd backend && PYTHONPATH=. python ../docs/research/scripts/index_attack_corpus.py textfooler
AEGIS_BENCHMARK_FILE=$PWD/data/evaluation/questions_v1.json PYTHONPATH=. python ../docs/research/scripts/run_defence_eval.py ../pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e ../pilot-runs textfooler
PYTHONPATH=. python ../docs/research/scripts/analyse_textfooler_defence.py ../pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e ../pilot-runs/20261019T200851Z-textfooler-33c7d2a707874d2ca57cb5b7851984e9 /tmp/tf && cd ..
# §17: live contextual-filter run (needs Qdrant and LLM_API_KEY), then its offline analysis
cd backend && AEGIS_BENCHMARK_FILE=$PWD/data/evaluation/questions_v1.json PYTHONPATH=. python ../docs/research/scripts/run_defence_eval.py ../pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e ../pilot-runs contextual
PYTHONPATH=. python ../docs/research/scripts/analyse_defence.py ../pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e ../pilot-runs/20261018T180113Z-contextual-a2eb543b82974c5aa4c1502de6e555a7 /tmp/ctx ../pilot-runs/20261017T165331Z-defence-cebfb27c1e9048cdb61fbfe15f37e50d ../pilot-runs/20261018T101453Z-repair-525ce73351064f089bdb62a448ee447c
# §18: attacks (attack environment; create-only; add --resume to continue, several workers may run at once)
python -m app.attack.pwws_adaptive_kb --variant textfooler
python -m app.attack.pwws_adaptive_kb --variant adaptive_lm
python -m app.attack.pwws_adaptive_kb --variant adaptive_lm_budget                     # 4.4611 bits
python -m app.attack.pwws_adaptive_kb --variant adaptive_lm_budget --budget-bits 20    # also 100, 300
python ../docs/research/scripts/second_order_diagnostic.py /tmp/diag.json
# detectors on any corpus (e.g. poisoned_textfooler), then intervals, frozen-threshold rates and figures
PYTHONPATH=. python ../docs/research/scripts/entropy_detection_eval.py /tmp/det.json poisoned_textfooler
PYTHONPATH=. python ../docs/research/scripts/entropy_family_eval.py /tmp/fam.json poisoned_textfooler && cd ..
python docs/research/scripts/auroc_uncertainty.py /tmp/intervals.json
python docs/research/scripts/make_figures.py
```
