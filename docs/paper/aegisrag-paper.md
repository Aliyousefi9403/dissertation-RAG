---
title: "Reading the Poison: Relative-Entropy Detection of Word-Substitution Attacks on a Cybersecurity RAG Knowledge Base"
author: "Ali Yousefi"
date: "Draft, October 2026"
---

# Abstract

Retrieval-augmented generation (RAG) makes the knowledge base part of a system's trust boundary. We study a quiet form of knowledge-base poisoning: word-level adversarial substitution (PWWS), which rewrites passages with plausible synonyms rather than injecting new text. On a cybersecurity RAG system over MITRE ATT&CK and CAPEC material, with a reviewed 44-question benchmark, paired repeated runs and a formatting-only control corpus, PWWS reduces answer correctness from 0.714 to 0.555 (Δ −0.159, 95% CI [−0.254, −0.068]), with the whole effect concentrated in questions whose source section was perturbed. We then treat detection as a relative-entropy problem. Whole-distribution divergences fail: letter-frequency KL is below chance (AUROC 0.33) and Jensen–Shannon divergence is near chance (0.47), because only a few words change in a passage. A per-word log-ratio between a word and its most probable synonym under a reference distribution q (a *synonym gap*) works, and replacing a word-frequency q by a small language model raises AUROC from 0.82 to 0.95 while falling to chance (0.53) on the formatting-only control. Deployed as a retrieval filter, this contextual detector halves the poisoned text reaching the generator (41% → 20% of questions, p = 0.012) and removes confidently wrong answers at no measurable correctness cost on clean data, but it does not restore correctness on poisoned data: filtering makes a poisoned knowledge base safe to read, not useful again. Against adaptive attackers, a frequency-matched PWWS defeats the word-frequency detector (AUROC 0.47) but not the contextual one (0.92), and an attacker that must also keep the passage as probable under the language model succeeds on none of 57 attackable sections: 98% of the swaps PWWS needs make the passage less probable, by a median of 17.9 bits. [TBD: budgeted attacker and TextFooler sentence.] All runs, records and analyses are released with checksums.

# 1 Introduction

A RAG system answers a question by retrieving passages from a knowledge base and asking a language model to answer from them [1]. Its answers are therefore only as trustworthy as the passages it reads. Knowledge-corruption attacks show that a handful of injected passages can steer answers to attacker-chosen targets [4, 5]. A less visible threat is *editing* existing passages: word-level adversarial attacks such as PWWS [3] and TextFooler [6] replace words with synonyms until a classifier changes its decision, leaving text that still reads almost normally. Recent work shows such perturbations degrade an LLM-based threat-detection framework through its knowledge base [2].

This paper asks three questions about that threat in a cybersecurity question-answering setting:

1. **How much does word-substitution poisoning hurt a RAG system, and through what mechanism?**
2. **Can an information-theoretic detector find the poisoned passages, and which reference distribution makes it work?**
3. **Does the detector survive an attacker who knows it, and what does evasion cost the attacker?**

We approach detection through relative entropy. If a passage's word distribution p is compared with a reference q of what normal text looks like, KL(p‖q) = Σ p(x) log p(x)/q(x) [13] should rise when words are swapped for unusual synonyms. We show that the full sum is the wrong tool and that one of its terms, the log-ratio between a word and its likely original under q, is the right one, provided q is good enough. This adapts frequency-guided substitution detection [9] to a domain reference and then to a language-model reference.

**Contributions.**

- A controlled, fully recorded testbed: a cybersecurity RAG system; clean, PWWS-poisoned and formatting-only control knowledge bases in separate collections; a reviewed benchmark with source anchors; paired runs with create-only, checksummed records (§3).
- A measured mechanism: PWWS poisoning works mainly by *displacing* relevant evidence and causing abstention, and only rarely by injecting misinformation that the model repeats (§5.1).
- A family of relative-entropy detectors evaluated against a formatting-only control, showing that whole-distribution divergences fail, the per-word synonym gap works, and a language-model reference is both stronger and free of the layout confound (§4, §5.2).
- Live evaluations of three retrieval-time defences (drop, repair-then-rescore, contextual drop) showing a consistent safety/utility trade-off (§5.3).
- Adaptive attackers at increasing knowledge, with a swap-level explanation of why fooling the classifier while staying probable under a language model is hard in this setting (§5.4).

# 2 Related work

**Poisoning RAG.** PoisonedRAG [4] injects crafted passages that both get retrieved and induce a target answer; Zhong et al. [5] craft passages that are retrieved for many queries. Both *add* text. Ikbarieh et al. [2] perturb an existing knowledge base with TextFooler and show degraded threat detection. We study in-place substitution with PWWS and measure where along retrieval and generation the damage occurs.

**Word-substitution attacks and their detection.** PWWS [3] ranks words by saliency and replaces each with the WordNet [14] synonym that most reduces the classifier's confidence; TextFooler [6] draws substitutes from counter-fitted word embeddings with sentence-similarity constraints; both are implemented in TextAttack [7]. Frequency-Guided Word Substitutions (FGWS) [9] detects such examples by replacing infrequent words with more frequent synonyms and measuring the change in the classifier's output. Our synonym gap keeps FGWS's core observation (adversarial substitutes are often rarer than the words they replace) but scores the text itself against a reference distribution, without access to the attacked classifier, so it can run at retrieval time.

**Defending RAG.** Certifiably robust RAG [11] isolates and aggregates per-passage answers. Evidence-support checks such as RAGAS-style faithfulness [12] assess whether an answer follows from its sources, but a faithful answer can still be wrong if the source is poisoned. Sampling-based consistency checks [8] target hallucination rather than corrupted evidence. We evaluate passage-level filtering, which needs no change to generation.

**Information-theoretic text statistics.** KL divergence [13] and Jensen–Shannon divergence [16] compare distributions; smoothing choices for language-model references are studied by Zhai and Lafferty [17]. A causal language model [15] supplies a context-dependent reference.

# 3 Threat model and testbed

**System.** A FastAPI backend retrieves the top 3 passages from Qdrant (all-MiniLM-L6-v2 embeddings; 500-character chunks with 100 overlap) and answers with gpt-4o-mini at temperature 0 under a fixed prompt. A Next.js interface shows clean and poisoned answers side by side, with each defence as a selectable mode.

**Knowledge base.** 18 documents of MITRE ATT&CK and CAPEC material covering 14 attack types in 5 categories (DDoS, injection, malware, reconnaissance, spoofing), split into 200 passages.

**Attacker.** The attacker can edit eligible text in the knowledge base but not the questions, the retrieval or generation settings, or the evaluation. PWWS [3] (TextAttack [7]) attacks a DistilBERT attack-type classifier trained on the same material, used as a *surrogate*: a section is rewritten when PWWS flips the surrogate's label. Of 88 eligible sections, 31 are already misclassified and skipped; PWWS succeeds on 38 of the remaining 57 (a retrained surrogate, used for all adaptive experiments and their matched control, gives 39). Original and adversarial text are recorded in an attack manifest.

**Formatting-only control.** The poisoning script also flattens the layout of the sections it rewrites. A control corpus applies the same flattening to the same sections with the original words, so that clean, control and poisoned isolate layout from substitution. Retrieval quality on the control equals clean, so the layout change alone does not harm retrieval.

**Benchmark and protocol.** 44 reviewed questions, each with atomic reference facts and an exact source anchor (file hash, character offsets); development and held-out questions are separated by source document (35 / 9). Every question runs 3 times per condition, paired by schedule index with condition order alternated. Correctness (against reference facts) and faithfulness (against retrieved passages) are scored by an LLM judge with a fixed rubric; retrieval relevance by Hit@3 and reciprocal rank under a section-level rule; *edited-text exposure* records whether any PWWS-edited word reached the generator. Repetitions are deterministic at retrieval level, so the question is the unit of analysis: we report question-level cluster-bootstrap 95% intervals (10,000 resamples) and two-sided Wilcoxon signed-rank tests. Every run writes create-only JSON records with a SHA-256 completion manifest, and every number in this paper is checked against its source file by a script.

# 4 Relative-entropy detectors

Let a passage contain words w₁…wₙ with empirical distribution p, and let q be a reference distribution over words.

**Whole-passage divergences.** KL(p‖q), Jensen–Shannon divergence JS(p, q) [16] and mean surprisal −(1/n) Σ log₂ q(wᵢ). We also report KL over letter frequencies, the textbook illustration of relative entropy.

**Synonym gap.** For each content word w with WordNet synonyms S(w), the gap is
g(w) = max over s in S(w) of [log₂ q(s) − log₂ q(w)],
the number of bits by which the most probable synonym beats the word actually used. This is the log-ratio term of KL evaluated at the substitution itself: a PWWS substitute ("abnegate") scores high because its likely original ("deny") is far more probable. A passage's score is the mean of its three largest gaps, so a few substitutions are enough to raise it.

**References.** (i) General English word frequencies; (ii) a *domain* reference: leave-one-document-out counts from the rest of the knowledge base interpolated 50/50 with English, which needs no clean copy of the poisoned document; (iii) the same with a Dirichlet prior, q(w) = (c(w) + μ q_en(w)) / (N + μ), μ = 2000 [17]; and (iv) a *contextual* reference from a small causal language model (distilgpt2 [15]). For (iv), the candidate words are the 10 with the largest domain gap, and for each of their 5 most probable synonyms s,

g_ctx(w) = log₂ p_LM(passage with w → s) − log₂ p_LM(passage),

so the reference sees the whole sentence rather than the word alone. All scores use only information a defender has; attack labels are used for evaluation only. Thresholds are fixed on development documents at a 10% false-positive rate and never tuned on held-out documents or live answers.

# 5 Results

## 5.1 The attack and its mechanism

| Stratum (44 questions) | Hit@3 clean → poisoned | Correctness clean → poisoned | Δ [95% CI] |
|---|---|---|---|
| All | 0.705 → 0.568 | 0.714 → 0.555 | −0.159 [−0.254, −0.068] |
| Target section perturbed (27) | 0.630 → 0.444 | 0.682 → 0.432 | −0.250 [−0.383, −0.124] |
| Target section not perturbed (17) | 0.824 → 0.765 | 0.765 → 0.750 | −0.015 [−0.083, 0.069] |

*Table 1. Effect of PWWS poisoning (132 paired answers per condition).*

The degradation is confined to questions whose source section was perturbed; questions answered from untouched sections of the same poisoned corpus are unaffected. Together with the formatting-only control, this attributes the effect to the substitutions. The mechanism is mostly *displacement*: abstentions rise from 26 to 45 of 132 answers, and of the 48 answers whose correctness fell by at least 0.25, 27 abstained and 31 had lost the relevant passage from the top 3. Confidently wrong answers rose only from 0 to 2; in both, the model repeated a substituted phrase ("Engraft Malicious Package", originally "implants malicious software") as if it were a named attack stage.

## 5.2 Detection

| Detector (AUROC) | PWWS | PWWS, matched rerun | Control (layout only) | Adaptive, frequency-matched |
|---|---|---|---|---|
| Letter-frequency KL | 0.33 | – | 0.35 | 0.36 |
| Word KL vs domain | 0.72 | – | 0.62 | 0.50 |
| Jensen–Shannon vs domain | 0.47 | – | 0.43 | 0.44 |
| Synonym gap, domain q (word frequency) | 0.82 [0.72, 0.90] | 0.88 [0.82, 0.94] | 0.67 [0.57, 0.77] | 0.47 [0.33, 0.72] |
| Synonym gap, Dirichlet q | 0.83 | – | 0.68 | 0.48 |
| **Contextual synonym gap (LM as q)** | **0.95 [0.87, 0.99]** | **0.97 [0.93, 1.00]** | **0.53 [0.45, 0.60]** | **0.92 [0.54, 0.96]** |

*Table 2. Detection of passages containing substituted words (191 passages; 47 edited for PWWS, 59 for the matched rerun, 13 for the adaptive attack). Brackets: 95% bootstrap intervals resampling documents. [TBD: TextFooler column.]*

Three findings follow. First, **whole-distribution divergences fail**: letters keep English statistics under word swaps, and KL or JS over the whole word distribution dilutes the handful of changed words among a passage's hundred. Second, **the per-word log-ratio works**, and the choice of q matters more than the choice of divergence or smoothing (Dirichlet vs interpolation: 0.83 vs 0.82). Third, **the contextual reference is both stronger and cleaner**: it improves AUROC over the word-frequency gap on both PWWS corpora (paired differences +0.13 [+0.03, +0.21] and +0.09 [+0.03, +0.16]) and is at chance on the control, where the word-frequency gap still scores 0.67 because part of its signal comes from which (topic-specific) sections were attacked. Detections are also self-explaining: of 47 edited passages, the word-frequency gap flags 27, and for 22 of these its explanation (the highest-gap words with their likely originals) names the exact word PWWS had replaced (abnegate → deny, meshing → network, noesis → knowledge).

## 5.3 Live defences

Each defence retrieves 10 candidates, scores them and passes 3 to the generator: *drop* removes candidates above the threshold (word-frequency gap, 7.23 bits); *repair* first replaces words with a gap above 9.5 bits by their likely original and keeps the passage if it then scores under the threshold; *contextual* drops using the contextual gap (4.46 bits). Each was run live on the full benchmark against both corpora (792 records per run).

| Defence on the poisoned corpus | Edited text reaching the model | Correctness | Confidently wrong | Abstained | Correctness cost on clean |
|---|---|---|---|---|---|
| None | 0.409 | 0.555 | 2 | 45 | – |
| Drop (word frequency) | 0.273 (p = 0.031) | 0.526 | 0 | 53 | −0.064 [−0.138, 0.002] |
| Repair, then rescore | 0.364 | 0.506 | 0 | 54 | −0.042 [−0.091, 0.004] |
| **Drop (contextual)** | **0.204 (p = 0.012)** | 0.485 (p = 0.020) | **0** | 63 | **−0.013 [−0.061, 0.030]** |

*Table 3. Live defences (44 questions × 3 repetitions; p: Wilcoxon vs no defence).*

All three defences remove the confidently wrong answers. The contextual filter halves the poisoned text that reaches the model and is the cheapest on clean data (it flags 8.4% of clean candidates against 10.9% for the word-frequency filter), consistent with its control result. None restores correctness on the poisoned corpus: when the passage that answers a question is the poisoned one, removing it leaves the model without evidence, and it declines rather than guesses. Repair does not help either, because word-level WordNet repair restores too few substitutions (recall 0.12 at precision 0.89) to make a passage trustworthy, so keeping repaired passages mainly keeps the poison. **Filtering makes a poisoned knowledge base safe to read; it does not make it useful again.**

## 5.4 Adaptive attackers

| Attacker (same retrained surrogate, 57 attackable sections) | Successful sections | Edited passages | Word-frequency gap | Contextual gap |
|---|---|---|---|---|
| Unrestricted PWWS (matched control) | 39 | 59 | 0.88 | 0.97 |
| First-order: every swap at least as frequent under the defender's q | 8 | 13 | **0.47** (0 of 13 flagged) | **0.92** |
| Second-order, strict: also at least as probable under the LM | **0** | 0 | – | – |
| [TBD] Second-order, budget 4.46 bits | [TBD] | [TBD] | [TBD] | [TBD] |

*Table 4. Adaptive attackers. The surrogate and sections are identical across rows, so the evasion rule is the only difference.*

A first-order attacker that knows the word-frequency reference evades that detector completely, as designed, but the contextual detector still finds its edits: the attacker matched how common its words are, not whether they fit the sentence. Being sneaky is expensive: success falls from 39 to 8 sections.

An attacker that must also keep each passage at least as probable under the detector's language model succeeds on none. A swap-level diagnostic explains why. Of the 550 swaps unrestricted PWWS used in its 39 successful attacks, 109 (20%) satisfy the frequency rule but only 9 (1.6%) leave the passage at least as probable, and 5 (0.9%) satisfy both; the median swap makes its passage 17.9 bits less probable, and none of the 39 complete attacks satisfies the rule. Natural source text sits close to a local maximum of language-model likelihood, and the substitutions that move a classifier are, almost by definition, ones that move the text away from it. [TBD: budgeted attacker result and interpretation.]

## 5.5 A second attack

[TBD: TextFooler (counter-fitted embeddings, sentence-encoder constraint) with the same surrogate and sections: successful sections, detector AUROCs with intervals.]

# 6 Discussion

**Why the log-ratio and not the sum.** KL(p‖q) is a sum of log-ratio terms weighted by p. Word substitution changes a handful of terms; in a 500-character passage with about 80 words, their weight is small and is swamped by the passage's topic, which also differs from q. The synonym gap evaluates the log-ratio only where the attack acts, comparing each word with the specific alternative the attacker would have replaced, which removes most of the topic variation.

**Why a better q beats a better divergence.** Smoothing (Dirichlet vs interpolation) and symmetry (JS vs KL) leave the result essentially unchanged, while moving from a unigram q to a contextual q changes it substantially. A unigram reference can only say a word is rare; a contextual reference says the word is unlikely *here*. That is also why the contextual detector ignores the layout confound and survives a frequency-matched attacker.

**Detection is not restoration.** In this corpus the passage that answers a perturbed question is usually the perturbed one, so any filter that removes poison also removes evidence. A defence that restores utility must restore the original text, for example with a masked language model conditioned on the domain; WordNet repair is too narrow.

**Detection constrains the attacker.** The adaptive results show a trade-off from the attacker's side: each additional constraint needed to evade a better reference removes most of the swaps that make the attack work. Against the contextual detector, the strict attacker has no successful attack at all in our setting.

# 7 Limitations

One knowledge base (18 documents), one generation model, one embedding model and 44 questions, of which 9 are held out; held-out detection results rest on few positive passages, and the adaptive results rest on 13 edited passages. The attack targets a surrogate classifier, not the RAG pipeline itself; transfer to retrieval and answers is measured, not optimised. Correctness and faithfulness are scored by an LLM judge; a blind manual check of a stratified sample of 75 answers is prepared but not yet graded. The contextual detector uses a small language model (distilgpt2); a larger or domain-tuned model may change both detection and the attacker's budget. Thresholds were fixed once on development data; the safety/utility balance depends on them.

# 8 Ethics

The attack edits text in a local copy of public MITRE material; no system is attacked and no malware is executed. Retrieved content is treated as data with no authority to run commands. No personal data is used; question and passage text is sent to a commercial LLM API. Detection scores are evidence for review, not proof that a passage is clean or an answer true.

# 9 Reproducibility

Code, corpora, attack manifests, run records (create-only JSON with SHA-256 completion manifests) and analysis scripts are in the project repository. A verification script recomputes every headline number in this paper from saved files and re-hashes all run records. Runs interrupted by infrastructure restarts were resumed in place with recorded equivalence checks.

**Acknowledgements.** The relative-entropy framing was suggested by Nikos [surname]. AI tools assisted with coding, analysis and drafting; the author checked all code, numbers and references.

# References

[1] Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 33.

[2] Ikbarieh, S., Aryal, K. and Gupta, M. (2025). RAG-targeted Adversarial Attack on LLM-based Threat Detection and Mitigation Framework. arXiv:2511.06212.

[3] Ren, S., Deng, Y., He, K. and Che, W. (2019). Generating Natural Language Adversarial Examples through Probability Weighted Word Saliency. Proc. ACL, 1085–1097.

[4] Zou, W., Geng, R., Wang, B. and Jia, J. (2025). PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models. USENIX Security.

[5] Zhong, Z., Huang, Z., Wettig, A. and Chen, D. (2023). Poisoning Retrieval Corpora by Injecting Adversarial Passages. Proc. EMNLP, 13764–13775.

[6] Jin, D., Jin, Z., Zhou, J. T. and Szolovits, P. (2020). Is BERT Really Robust? A Strong Baseline for Natural Language Attack on Text Classification and Entailment. Proc. AAAI 34(5), 8018–8025.

[7] Morris, J. et al. (2020). TextAttack: A Framework for Adversarial Attacks, Data Augmentation, and Adversarial Training in NLP. Proc. EMNLP: System Demonstrations, 119–126.

[8] Manakul, P., Liusie, A. and Gales, M. (2023). SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. Proc. EMNLP, 9004–9017.

[9] Mozes, M., Stenetorp, P., Kleinberg, B. and Griffin, L. (2021). Frequency-Guided Word Substitutions for Detecting Textual Adversarial Examples. Proc. EACL, 171–186.

[10] Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 36, Datasets and Benchmarks Track.

[11] Xiang, C., Wu, T., Zhong, Z., Wagner, D., Chen, D. and Mittal, P. (2024). Certifiably Robust RAG against Retrieval Corruption. arXiv:2405.15556.

[12] Es, S., James, J., Espinosa Anke, L. and Schockaert, S. (2024). RAGAs: Automated Evaluation of Retrieval Augmented Generation. Proc. EACL: System Demonstrations, 150–158.

[13] Kullback, S. and Leibler, R. A. (1951). On Information and Sufficiency. The Annals of Mathematical Statistics, 22(1), 79–86.

[14] Miller, G. A. (1995). WordNet: A Lexical Database for English. Communications of the ACM, 38(11), 39–41.

[15] Radford, A., Wu, J., Child, R., Luan, D., Amodei, D. and Sutskever, I. (2019). Language Models are Unsupervised Multitask Learners. OpenAI technical report.

[16] Lin, J. (1991). Divergence Measures Based on the Shannon Entropy. IEEE Transactions on Information Theory, 37(1), 145–151.

[17] Zhai, C. and Lafferty, J. (2004). A Study of Smoothing Methods for Language Models Applied to Information Retrieval. ACM Transactions on Information Systems, 22(2), 179–214.
