---
title: "AegisRAG: Project Briefing"
subtitle: "Detecting word-substitution poisoning of a cybersecurity RAG knowledge base with relative entropy"
author: "Ali Yousefi, BSc Computer Science, IN3007 Individual Project"
date: "22 October 2026"
---

# 1. The project in one page

**Problem.** A retrieval-augmented generation (RAG) system answers questions by retrieving passages from a knowledge base and passing them to a large language model. Whoever can edit the knowledge base can influence the answers. This project studies a quiet form of tampering: *word-substitution poisoning*, where an attack algorithm (PWWS, and later TextFooler) replaces words with synonyms, so the text still reads almost normally but the system's answers get worse.

**What was built.** AegisRAG: a cybersecurity question-answering system over MITRE ATT&CK and CAPEC material, with clean, poisoned and control copies of its knowledge base, a web interface that compares them side by side, three retrieval-time defences, an answer-level evidence check, and a fully recorded evaluation framework.

**Main idea (suggested by Dr Nikos Komninos).** Use relative entropy. A substituted word is unusually improbable compared with the word it replaced. The project turned this into the *synonym gap*: for each word, how many bits more probable its best synonym is than the word itself, under a reference distribution q of normal text.

**Headline results.**

- PWWS poisoning lowers answer correctness from 0.714 to 0.555; the whole drop is on questions whose source section was attacked.
- Letter-level and whole-passage divergences do not detect the attack; the per-word synonym gap does (AUROC 0.82 with word frequencies, **0.95 with a language model as q**), and the language-model version is at chance on a layout-only control (0.53), so it reacts to the substitutions themselves.
- Deployed as a filter, the language-model version halves the poisoned text that reaches the model (41% → 20% of questions) and removes confidently wrong answers, at no measurable cost on clean data, but it cannot restore correctness.
- An attacker that knows the word-frequency reference defeats that detector but not the language-model one; an attacker that must also stay probable under the language model succeeds on **0 of 57** sections.
- Both results carry over to a second attack (TextFooler): the language-model filter cuts exposure from 82% to 52%; the word-frequency filter does not help.
- An answer-level evidence check is *not* a useful error detector against this attack (precision 0.28, recall 0.20).

**Evidence.** About 5,750 checksummed run records; 83 headline numbers checked automatically against their source files; every number reproducible from saved data.

# 2. How the project started and developed

| When | What happened |
|---|---|
| Summer 2026 | Topic chosen: reliability of RAG answers when the knowledge base is poisoned. Inspired by work showing that adversarially perturbed knowledge bases degrade an LLM-based threat-detection framework (Ikbarieh, Aryal and Gupta, 2025), which used TextFooler; this project chose PWWS as its main attack. |
| 2 Aug 2026 | First version committed: PWWS proof of concept, knowledge-base builder from MITRE ATT&CK and CAPEC, LLM generation layer. |
| Aug–Sep 2026 | Surrogate classifier trained; poisoned knowledge base generated; first prototype comparisons of clean and poisoned answers (recorded in the repository's early evaluation files). |
| 13–14 Sep 2026 | Pilot runs (12 questions × 3 repetitions). One pilot failed because the vector database was unreachable (kept and reported as an infrastructure failure, never pooled). The successful pilot showed poisoning works mainly by displacing evidence and causing refusals. |
| 16 Oct 2026 | Evidence check added; benchmark expanded, reviewed and frozen (44 questions); formatting-only control built; main run (44 × 3). First relative-entropy detector, following Dr Komninos's suggestion. |
| 17 Oct 2026 | Word-frequency filter deployed live and evaluated; threshold sweep; repair feasibility; report for Dr Komninos. |
| 18 Oct 2026 | Repair defence evaluated live; better references (Dirichlet, Jensen–Shannon, language model); first adaptive attacker; language-model filter deployed as the Contextual mode. |
| 18–19 Oct 2026 | Second attack (TextFooler); second-order adaptive attackers at five likelihood budgets; uncertainty intervals; PDD rebuilt to the handbook. |
| 19–21 Oct 2026 | Evidence check evaluated at scale; both filters run live on the TextFooler corpus; paper draft. |

# 3. System architecture

```
question
   │
   ▼
retrieval (Qdrant, all-MiniLM-L6-v2 embeddings)  ──►  [optional defence: score candidates, drop or repair]
   │  top 3 passages
   ▼
generation (gpt-4o-mini, temperature 0, fixed prompt: answer only from context, cite sources)
   │
   ▼
answer + sources (+ optional evidence check)  ──►  web interface / evaluation records
```

## 3.1 Fixed configuration

| Setting | Value | Why |
|---|---|---|
| Generator | OpenAI gpt-4o-mini, temperature 0 | Cheap enough for thousands of calls; temperature 0 removes randomness so conditions are comparable |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Standard, small, runs on CPU |
| Vector store | Qdrant, one collection per corpus | Each condition is isolated; nothing is ever overwritten |
| Chunking | 500 characters, 100 overlap, start offsets kept | Small passages make it possible to tell exactly which text reached the model |
| Retrieval | Top 3 by cosine similarity | A typical RAG setting; small enough that one poisoned passage matters |
| Prompt | Answer only from the context, say when it is insufficient, cite [Source n] | Makes failures visible as refusals rather than invented facts |

## 3.2 Code map (backend, Python)

| Module | What it does |
|---|---|
| `app/main.py` | FastAPI application. Endpoints: `/health`, `/chat` (one answer in a chosen mode), `/compare` (clean vs poisoned side by side), `/guarded-chat` (answer with evidence check), `/history` (saved comparisons and statistics). |
| `app/config.py` | All settings in one place: model, embeddings, chunking, retrieval depth, the corpus folder and collection for each system state. |
| `app/kb_builder/` | Builds the knowledge base from MITRE ATT&CK and CAPEC using a mapping file (`source_mapping.yaml`) that names, for each attack type, its primary CAPEC entry and supporting ATT&CK techniques. |
| `app/ingestion/` | Loads the Markdown documents, attaches metadata (attack type, system state), splits them into passages and maps passages to section headings. |
| `app/vectorstore/`, `app/retrieval/` | Creates embeddings and searches a collection. |
| `app/generation/` | The RAG chain: retrieve, build the prompt, call the model, return answer and sources. A `retrieval_fn` hook lets a defence replace retrieval without touching anything else. |
| `app/attack/` | Surrogate classifier pipeline (`prepare_dataset`, `augment_dataset`, `finetune_bert`), the PWWS attack on the knowledge base (`pwws_poison_kb`), and the adaptive, second-order and TextFooler variants (`pwws_adaptive_kb`). |
| `app/defence/entropy_filter.py` | Word-frequency synonym-gap detector, the drop defence and the repair defence. |
| `app/defence/contextual_filter.py` | Language-model synonym-gap detector and the contextual drop defence. |
| `app/defence/evidence_guard.py` | Answer-level evidence check: verifier call, strict JSON validation, verbatim quote checking, release policy, audit record. |
| `app/evaluation/` | Pilot runner (create-only, checksummed records), LLM judge, retrieval metrics, edited-text exposure, paired metrics, attack success, source identity. |
| `app/history/` | SQLite history of comparisons made in the interface. |

## 3.3 Interface (Next.js, `frontend-next/`)

Modes: **Clean**, **PWWS Poisoned**, **Compare** (side by side), **Defended** (word-frequency filter, with a shield animation), **Repaired**, **Contextual** (language-model filter), and an **Evidence check** toggle. Each source card shows its filter verdict: score in bits, threshold, and the words that drove it with their likely originals (for example abnegate → deny).

## 3.4 Research scripts (`docs/research/scripts/`)

Offline analysis and live runners: benchmark building, control corpus, detector evaluations, the defence runner (`run_defence_eval.py`, with drop, repair, contextual and TextFooler modes, resumable), analyses with bootstrap intervals, uncertainty intervals, figures, the evidence-check replay, and `verify_evidence.py`, which re-checks every headline number.

## 3.5 Quality

| Check | Result |
|---|---|
| Backend tests (15 files, about 2,300 lines) | 285 passed, 1 skipped (attack tests run in their own environment, 14 passed) |
| Browser end-to-end tests (7 files, 26 tests) | All pass against the real backend |
| Lint and type checks | Clean |
| Evidence check | 83 of 83 claims match their source files; no run record changed since its run finished |

# 4. Data, attack and controls

## 4.1 Knowledge base

18 Markdown documents built from MITRE ATT&CK and CAPEC: 14 attack types in 5 categories (DDoS: HTTP, ICMP, TCP SYN and UDP flood; injection: SQL injection, XSS, file upload; malware: backdoor, password cracking; reconnaissance: OS fingerprinting, port scanning, vulnerability scanning; spoofing: ARP and DNS) plus 4 device documents. 200 passages.

## 4.2 The attack: PWWS against a surrogate classifier

PWWS (probability weighted word saliency; Ren et al., 2019, via TextAttack) needs a classifier to attack. A RAG system has no classifier, so the project trains a *surrogate*: a DistilBERT model that labels a section with its attack type (14 labels). Training data: every section of at least 80 characters, augmented with 4 paraphrases each, 552 training and 138 validation samples, 30 epochs.

For each eligible section, PWWS ranks words by how much they matter to the classifier and swaps them for WordNet synonyms until the classifier's label changes. A successful section replaces the original in the poisoned copy; every attempt is recorded in an attack manifest (original and adversarial text).

| Attack outcome (88 eligible sections) | Count |
|---|---|
| Skipped (classifier already wrong, nothing to attack) | 31 |
| Failed | 19 |
| Successful | **38** (of 57 attackable: 67%) |

Mean share of words changed: 15%. Mean semantic similarity of original and attacked text: 0.80.

**Why a surrogate?** It reproduces the threat realistically: an attacker who wants a passage to read differently to machines but normally to people. The attack's success against the surrogate is reported separately from its effect on the RAG system.

## 4.3 Formatting-only control

The attack script also flattens the layout of the sections it rewrites (lists and line breaks become one paragraph). A third copy of the knowledge base applies the same flattening to the same sections with the **original** words. Comparing clean, control and poisoned separates the effect of the substitutions from the effect of layout. Retrieval on the control equals retrieval on clean, so layout alone does not cause the damage.

## 4.4 Benchmark

44 reviewed questions (from a 45-question draft), each with atomic reference facts taken from the knowledge base and an exact source anchor (file hash and character offsets). Questions cover description, prerequisites, consequences, required resources and execution flow. Split by source document into 35 development and 9 held-out questions; held-out documents were never used to design or tune anything. Frozen before the main run (benchmark hash recorded).

## 4.5 Experimental protocol

- Every question runs **3 times per condition**, paired by schedule index, with the order of conditions alternated.
- Every call writes a **create-only JSON record** (prompt, retrieved passages, answer, judge scores, timings, errors); at the end the runner writes a completion file with the SHA-256 of every record.
- Failures stay in the record and count as **missing**, never as zero.
- Retrieval turned out to be deterministic across repetitions, so the **question** is the unit of analysis.
- Statistics: question-level means, 95% bootstrap intervals (10,000 resamples), two-sided Wilcoxon signed-rank tests.
- Thresholds for detectors are fixed on development documents **before** any answer-level evaluation and never re-tuned.

# 5. Metrics: what each measures and why it is there

| Metric | Definition | Why it was added |
|---|---|---|
| **Correctness** | An LLM judge compares the answer with the question's reference facts: 1.0 correct, 0.5 partial, 0.0 incorrect (intermediate values allowed). | The main measure of answer quality. Reference facts make it checkable. |
| **Faithfulness** | An LLM judge checks whether the answer's claims are supported by the retrieved passages. | Separates "the model invented something" from "the sources were wrong": a faithful answer can still be wrong if its sources are poisoned. |
| **Outcome category** | correct (≥ 0.75), partial, incorrect (< 0.25), or refusal (the answer says the sources are insufficient). | Shows *how* answers fail. This revealed the main mechanism: refusals, not misinformation. |
| **Hit@3** | 1 if any of the top 3 passages overlaps the expected section of the expected document. | Measures retrieval: did the system find the right evidence? |
| **Reciprocal rank (MRR)** | 1 / rank of the first relevant passage. | Retrieval quality with position taken into account. |
| **Edited-text exposure** | 1 if any retrieved passage contains a word the attack actually changed (character-level alignment of original and attacked text). | The most precise measure of whether poisoned text reached the model. It is the primary exposure measure because a passage can lie in an attacked section without containing any changed word. |
| **Attacked-section exposure** | 1 if any retrieved passage overlaps a section that was successfully attacked. | A looser exposure measure, reported for comparison; it roughly doubles the edited-text figure. |
| **Attack success rate (ASR)** | Exposure = 1 and correctness falls by at least 0.25 against the clean answer. | Counts questions the attack actually damaged; the 0.25 threshold is swept (0.25 to 1.0) to show it is not fragile. |
| **Surrogate attack success** | Successful ÷ (successful + failed) attacks on the classifier. | Separates the attack on the classifier from its effect on the RAG system. |
| **AUROC** | Probability that a randomly chosen poisoned passage scores higher than a randomly chosen clean one (0.5 chance, 1.0 perfect). | Threshold-free measure of how well a detector separates poisoned from clean passages. |
| **Detection rate at the frozen threshold** | Share of edited passages flagged (true-positive rate) and of unedited passages flagged (false-positive rate) at the threshold fixed on development data. | What the deployed filter actually does, without re-tuning. |
| **Bootstrap intervals** | Resample questions (or, for detectors, whole documents) 10,000 times. | Honest uncertainty: passages from one document, and repetitions of one question, are not independent. |
| **Wilcoxon signed-rank test** | Paired test over questions. | Whether a paired difference is larger than chance, without assuming normality. |
| **Precision, recall, false-alarm rate** | For the evidence check: share of flagged answers that are wrong; share of wrong answers flagged; share of correct answers flagged. | Whether an answer-level indicator is useful to a user. |
| **Judge agreement** | Exact agreement, agreement within 0.25, Spearman correlation and weighted Cohen's kappa between a blind manual grading of 75 answers and the LLM judge. | The judge is an LLM; its scores must be validated by a human. |

# 6. The detectors: how they work

## 6.1 From relative entropy to the synonym gap

Relative entropy compares a passage's word distribution p with a reference q of normal text: KL(p‖q) = Σ p(x) log₂ p(x)/q(x). Three versions were tried in order:

1. **Letter frequencies** (the lecture example): fails (AUROC 0.33). Word swaps keep English letter statistics.
2. **Word distribution against a domain reference**: some signal (0.72), but a few changed words are diluted among about 80 normal ones, and the score partly reflects the topic of the passage.
3. **The synonym gap**: evaluate the log-ratio only where the attack acts. For each content word w, take its WordNet synonyms and the most probable one under q:

   gap(w) = log₂ q(best synonym) − log₂ q(w)   (bits)

   A passage's score is the mean of its three largest gaps. "abnegate" scores high because "deny" is far more probable. This is a single term of KL divergence; Dr Komninos confirmed that, in information-theory terms, this is what the method is called.

## 6.2 The reference q

- **Word-frequency reference:** q(w) = 0.5 × (frequency of w in the *other* documents of the knowledge base) + 0.5 × (frequency in general English, from `wordfreq`). Leaving the document itself out stops a poisoned document vouching for its own words. Uses no clean copy and no attack labels.
- **Dirichlet-smoothed version:** almost identical (0.83 vs 0.82). Smoothing is not the issue.
- **Jensen–Shannon divergence** over the whole distribution: fails (0.47). A symmetric divergence does not help.
- **Language-model reference (contextual synonym gap):** distilgpt2 reads the whole passage: gap = log₂ p(passage with the word swapped back) − log₂ p(passage). To keep it cheap, only the 10 words with the largest frequency gaps are tried, each with its 5 most probable synonyms; scores are cached per passage. This judges whether a word fits *this sentence*, not just whether it is rare.

## 6.3 Detection results (AUROC; 95% intervals resampling documents)

| Detector | PWWS | PWWS (retrained surrogate) | TextFooler | Layout-only control | Frequency-matched attacker |
|---|---|---|---|---|---|
| Letter-frequency KL | 0.33 | – | 0.28 | 0.35 | 0.36 |
| Word KL vs domain | 0.72 | – | 0.83 | 0.62 | 0.50 |
| Jensen–Shannon | 0.47 | – | 0.48 | 0.43 | 0.44 |
| Synonym gap, word frequency | 0.82 [0.72, 0.90] | 0.88 | 0.90 | 0.67 | 0.47 |
| **Synonym gap, language model** | **0.95** [0.87, 0.99] | **0.97** | **0.91** | **0.53** | **0.92** |

The language model beats word frequency by +0.13 AUROC on PWWS (95% interval [+0.03, +0.21]). At the frozen threshold it flags 42 of 47 PWWS edits, 70 of 82 TextFooler edits and 10 of 13 adaptive edits, while flagging 9–14% of unedited passages. Detections explain themselves: of 27 passages the word-frequency detector flags, 22 name the exact replaced word.

# 7. The defences

All three work the same way: retrieve 10 candidates instead of 3, score each, and pass the 3 best that remain to the model. Thresholds were frozen on development documents at a 10% false-positive rate.

| Defence | How | Threshold |
|---|---|---|
| **Drop (word frequency)** — "Defended" mode | Drop passages scoring above the threshold | 7.2262 bits |
| **Repair** — "Repaired" mode | Replace words with a gap above 9.5 bits by their likely original, re-score, keep if now under the threshold | 7.2262 bits |
| **Drop (language model)** — "Contextual" mode | As drop, with the contextual score | 4.4611 bits |

If WordNet, `wordfreq` or the language model is missing, the defence stops with an error rather than letting everything through (it fails closed).

# 8. Results

## 8.1 What the poisoning does (main run, 44 questions × 3)

| | Clean | Poisoned | Difference [95% CI] |
|---|---|---|---|
| Correctness, all questions | 0.714 | 0.555 | −0.159 [−0.254, −0.068] |
| Correctness, attacked source section (27 questions) | 0.682 | 0.432 | −0.250 [−0.383, −0.124] |
| Correctness, untouched source section (17) | 0.765 | 0.750 | −0.015 [−0.083, 0.069] |
| Hit@3 | 0.705 | 0.568 | |
| Refusals (of 132) | 26 | 45 | |
| Confidently wrong answers | 0 | 2 | |

The damage is confined to questions whose source was attacked. The mechanism is **displacement**: the poisoned passage loses its retrieval rank or no longer contains what the question needs, so the model refuses. Only twice did the model repeat poisoned text as fact ("Engraft Malicious Package", originally "implants malicious software").

## 8.2 Defences live (poisoned corpus)

| Defence | Poisoned text reaching the model | Correctness | Confidently wrong | Refusals | Cost on clean data |
|---|---|---|---|---|---|
| None | 41% | 0.555 | 2 | 45 | – |
| Drop, word frequency | 27% (p = 0.031) | 0.526 | 0 | 53 | −0.064 |
| Repair | 36% | 0.506 | 0 | 54 | −0.042 |
| **Drop, language model** | **20%** (p = 0.012) | 0.485 | **0** | 63 | **−0.013** |

Filtering makes a poisoned knowledge base *safe to read*, not *useful again*: when the passage a question needs is the poisoned one, removing it leaves the model without evidence.

## 8.3 Attackers who know the detector (same surrogate, 57 attackable sections)

| Attacker | Successful sections | Word-frequency AUROC | Language-model AUROC |
|---|---|---|---|
| Plain PWWS | 39 | 0.88 | 0.97 |
| First-order: swap only to words at least as frequent | 8 | 0.47 (0 of 13 flagged) | 0.92 (10 of 13 flagged) |
| Second-order: also as probable under the language model | **0** | – | – |
| …may lose up to 4.46 bits | 0 | – | – |
| …up to 20 bits | 0 | – | – |
| …up to 100 bits | 5 | 0.51 | 0.78 |
| …up to 300 bits | 8 (identical to first-order) | 0.47 | 0.92 |

Of the 550 word swaps plain PWWS used, only 9 keep a passage as probable under the language model; the median swap costs 17.9 bits. Fooling the classifier and staying natural are in conflict, so no attacker in this family evades the contextual detector: those that obey its rule fail to attack, those that succeed are flagged.

## 8.4 A second attack: TextFooler, live

| | Poisoned text reaching the model | Correctness | Refusals |
|---|---|---|---|
| No defence | 82% | 0.564 | 54 |
| Word-frequency filter | 80% (no change) | 0.525 | 53 |
| **Language-model filter** | **52%** (p < 0.001) | 0.447 | 74 |

TextFooler (substitutes from word embeddings) is stronger (49 of 57 sections) and more pervasive. Only the language-model filter carries over to the live system, with unchanged thresholds.

## 8.5 Answer-level evidence check

Replayed on 352 recorded answers: precision 0.28, recall 0.20, false-alarm rate 0.31. Errors here are mostly incomplete answers whose every statement is in the sources (68 of 89 partial answers pass), so a grounding check cannot see them. It did catch the one confidently wrong answer. This supports the design choice: act on passages before generation, not on answers afterwards.

## 8.6 Runtime verification monitor (Dr Asad's idea)

A fourth defence that checks every answer against a specification built from the **official MITRE STIX data** (trusted, hash-pinned, separate from the knowledge base the attacker edits): rare words must exist in the trusted vocabulary (catches "engraft"); the system must not refuse when the trusted reference covers the attack; and a quarantined passage is never used again (a temporal property, verified on the trace). On a violation it finds the passages responsible, quarantines them, and regenerates with the monitor's feedback.

| | Result |
|---|---|
| Repeated misinformation ("Engraft Malicious Package") | reached the user 3/3 times without the monitor, **0/3** with it |
| Poisoned text reaching the model (verify mode) | 41% → 28% (p = 0.016) |
| Correctness with trusted fallback (restore mode) | **0.555 → 0.773** (p = 0.0002); refusals 45 → 7 |
| Clean data | no passage quarantined; correctness cost −0.013 (not significant) |
| Memory | quarantined passages skipped more often in repeats; fewer regenerations; never re-admitted |
| Limitation | 7 false withholds: the MITRE files lack the knowledge base's OWASP/NIST wording |

# 9. Achievements and outputs

| Output | Status |
|---|---|
| AegisRAG software (backend, interface, three defences, evidence check) | Complete, tested |
| Knowledge base, poisoned corpora (PWWS, TextFooler, adaptive variants), control corpus, attack manifests | Complete, versioned |
| Reviewed, frozen 44-question benchmark | Complete |
| Recorded runs: pilots, main, three defence runs, TextFooler live run, evidence check | Complete, checksummed |
| Results write-up (20 sections), figures, evidence index | Complete |
| Project Definition Document (to the handbook) | Complete |
| Paper draft | Drafted; to be extended for publication |
| Judge agreement check | Complete: weighted κ 0.82 with blind manual grades of 75 answers |
| Runtime verification monitor (fourth defence) | Complete, tested, evaluated live |

# 10. Limitations (stated in every write-up)

- One knowledge base (18 documents), 44 questions (9 held out), one generator, one embedding model, a small reference language model.
- The attacks target a surrogate classifier, not the RAG system directly.
- The correctness judge is an LLM; the manual agreement check is in progress.
- Adaptive results rest on few edited passages (13 and 6).
- The second-order attacker constrains whole-passage likelihood, not the detector's exact score.

# 11. Dr Komninos's feedback and the next research step

On the email of 18 October, Dr Komninos commented:

1. **"KL should/could apply to sentences; it would be more accurate."** Instead of single words, compare sentences.
2. **"A sentence-based approach will work, especially when there is a separation between positive and negative statements."**
3. **"Build q according to true statements (sentences). Can you retrieve knowledge from Wikipedia?"**
4. Calling the method relative-entropy based is correct in information-theory terms.

**Planned response (publication extension).** Build the reference from *trusted statements* rather than word frequencies: for each retrieved sentence, retrieve the closest sentences from a trusted source (Wikipedia, and the official MITRE pages), and measure the divergence of the sentence from what trusted statements say, at sentence level. This could also catch attacks that the word-level detector cannot see, such as edits that flip a statement from positive to negative ("can" → "cannot") while every word stays probable. It would be evaluated exactly like the current detectors: same corpora, control, adaptive attackers and frozen thresholds.

# 12. What remains, and the plan

## 12.1 Dissertation (deadline 4 April 2027)

| Chapter (handbook §6.2) | Source material already available |
|---|---|
| 1 Introduction | PDD; sections 1 and 2 of this briefing |
| 2 Outputs summary (≤ 2 pages) | Section 9 |
| 3 Context | PDD references; paper related work; literature on RAG poisoning, word-substitution attacks and their detection, perplexity filters |
| 4 Method | Sections 3–7; results write-up §1–5 |
| 5 Results (about half) | Section 8; results write-up §6–20; figures |
| 6 Conclusions and LSEPI | Section 10; PDD LSEPI section |
| Appendices A (PDD), B (reuse summary), C (use of AI) | A done; B and C to prepare |

Also required: the 15-minute demo video (plan ready: `docs/demo/demo-video-plan.md`) and the in-person final review (15% of the mark).

## 12.2 Publication

Target suggested by Dr Komninos: IEEE Transactions on Dependable and Secure Computing (template received). To reach that standard: more data (full ATT&CK/CAPEC plus a public RAG benchmark), standard baselines (a perplexity filter, a density-estimation detector, and a RAG defence such as TrustRAG or RobustRAG), a masked-language-model attack (BERT-Attack or BAE), more generator models, an attacker that optimises against the detector's score directly, and Dr Komninos's sentence-level reference.

# 13. Questions your supervisor is likely to ask

**Why PWWS?** It is a standard, well-documented word-substitution attack (Ren et al., 2019) available in TextAttack, it changes text without making it obviously wrong, and related work had used TextFooler; using PWWS first and TextFooler second shows the findings are not tied to one attack.

**Why a surrogate classifier when a RAG system has no classifier?** The attack needs a target that decides when a passage has been changed "enough". A classifier of attack types is a realistic stand-in for "a machine reading the passage". Its effect on the RAG system is then measured separately.

**How do you know the damage is caused by the word swaps?** Two controls: the formatting-only corpus (same layout changes, original words) gives the same retrieval as clean; and within the poisoned corpus, questions whose source section was not attacked do not get worse.

**Why the synonym gap instead of plain KL?** KL sums over all words, so a few substitutions are diluted and the topic of the passage dominates. The synonym gap evaluates the log-ratio only where an attack acts, comparing each word with the specific word an attacker would have replaced.

**How was the threshold chosen? Is it overfitted?** Fixed once on development documents at a 10% false-positive rate, before any answer-level test, never re-tuned. Held-out documents and the second attack use the same value.

**Why does correctness not recover?** Because the questions' evidence is in the poisoned passage itself. A filter can remove poison but cannot restore lost information; that would need the original text back.

**Couldn't an attacker just avoid your detector?** That was tested at five levels of attacker knowledge and budget. An attacker that matches word frequencies beats the simple detector; an attacker that must also stay natural under the language model cannot complete an attack at all within the detector's threshold.

**Why trust the LLM judge?** A blind manual grading of 75 stratified answers measures its agreement with a human (in progress). All raw judge outputs are recorded.

**How is the evidence kept honest?** Create-only records with checksums, a script that checks every headline number against its source file, failures kept as missing, and negative results reported (letter KL, Jensen–Shannon, repair, the evidence check).

**What is new compared with existing work?** A detector that needs no access to the attacked model and runs at retrieval time, explains its decisions, is evaluated live end to end, and is tested against adaptive attackers, with the finding that the language-model reference makes evasion and attack success conflict.

# References

Ikbarieh, S., Aryal, K. and Gupta, M. (2025) 'RAG-targeted adversarial attack on LLM-based threat detection and mitigation framework', arXiv:2511.06212.

Jin, D., Jin, Z., Zhou, J.T. and Szolovits, P. (2020) 'Is BERT really robust?', Proceedings of AAAI, 34(5), pp. 8018–8025.

Kullback, S. and Leibler, R.A. (1951) 'On information and sufficiency', The Annals of Mathematical Statistics, 22(1), pp. 79–86.

Mozes, M., Stenetorp, P., Kleinberg, B. and Griffin, L. (2021) 'Frequency-guided word substitutions for detecting textual adversarial examples', Proceedings of EACL, pp. 171–186.

Ren, S., Deng, Y., He, K. and Che, W. (2019) 'Generating natural language adversarial examples through probability weighted word saliency', Proceedings of ACL, pp. 1085–1097.
