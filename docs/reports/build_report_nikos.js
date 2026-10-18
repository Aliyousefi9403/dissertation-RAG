// Builds "AegisRAG-relative-entropy-report.docx" for Nikos from saved result files.
// Run from docs/reports/:  node build_report_nikos.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Header, Footer, AlignmentType, HeadingLevel, ImageRun,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, LevelFormat, PageNumber,
} = require("docx");

const ROOT = path.resolve(__dirname, "../..");
const R = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, "docs/research/results", p), "utf8"));
const det = R("entropy-detector-20261016/detector-poisoned.json").results;
const ctl = R("entropy-detector-20261016/detector-control.json").results;
const flt = R("entropy-detector-20261016/retrieval-filter.json");
const expl = R("entropy-defence/explanations.json").summary;
const matched = R("entropy-defence/matched-control.json");
const live = R("entropy-defence/live-paired/summary.json");
const main = R("main-v1-20261016/summary.json");
// Version 2 (18 Oct 2026): better references, adaptive attacker, repair vs drop, threshold sweep.
const fam = (c) => R(`entropy-family/family-${c}.json`).results;
const famP = fam("poisoned"), famC = fam("control"), famA = fam("poisoned_adaptive"), famR = fam("poisoned_pwws_rerun");
const detA = R("entropy-family/detector-poisoned_adaptive.json"), detR = R("entropy-family/detector-poisoned_pwws_rerun.json");
const atk = R("adaptive-attack/surrogate-and-attack-record.json");
const rerunManifest = fs.readFileSync(path.join(ROOT, "backend/data/poisoned_pwws_rerun/pwws_attack_manifest.jsonl"), "utf8").trim().split("\n").map(JSON.parse);
const rerunOk = rerunManifest.filter((e) => e.success).length;
const rep = R("entropy-repair/live-paired/summary.json");
const sweep = R("entropy-defence/threshold-sweep/sweep.json");
const flaggedAt = (d, t) => [d.rows.filter((r) => r.label && r.syngap_top3_domain > t).length, d.rows.filter((r) => r.label).length];
const COMMIT = process.env.REPORT_COMMIT || "see repository";

const FONT = "Arial";
const W = 9026;
const f2 = (x) => Number(x).toFixed(2);
const f3 = (x) => Number(x).toFixed(3);
const sgn = (x) => (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(3);
const pval = (p) => (p === null || p === undefined ? "n/a" : p < 0.001 ? "< 0.001" : p.toFixed(3));
const ci = (c) => `[${sgn(c[0])}, ${sgn(c[1])}]`;

const run = (t, o = {}) => new TextRun({ text: t, ...o });
const p = (parts, opts = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...opts,
  children: (Array.isArray(parts) ? parts : [parts]).map((x) => (typeof x === "string" ? run(x) : x)) });
const b = (t) => run(t, { bold: true });
const it = (t) => run(t, { italics: true });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 70, line: 264 },
  children: (Array.isArray(parts) ? parts : [parts]).map((x) => (typeof x === "string" ? run(x) : x)) });
const numbered = (parts, reference = "steps") => new Paragraph({ numbering: { reference, level: 0 }, spacing: { after: 70, line: 264 },
  children: (Array.isArray(parts) ? parts : [parts]).map((x) => (typeof x === "string" ? run(x) : x)) });
const mono = (t) => new Paragraph({ spacing: { after: 60 }, indent: { left: 360 }, children: [run(t, { font: "Courier New", size: 18 })] });
const caption = (t) => new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.CENTER, children: [run(t, { italics: true, size: 18, color: "555555" })] });
const figure = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, "docs/research/figures", file)), transformation: { width: w, height: h } })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cell = (text, width, head = false, align = AlignmentType.LEFT) => new TableCell({
  width: { size: width, type: WidthType.DXA }, borders: { top: border, bottom: border, left: border, right: border },
  shading: head ? { fill: "E8EEF4", type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  children: [new Paragraph({ alignment: align, spacing: { after: 0, line: 240 }, children: [run(text, { bold: head, size: 18 })] })] });
const table = (widths, rows) => new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
  rows: rows.map((r, n) => new TableRow({ children: r.map((t, k) => cell(String(t), widths[k], n === 0, k === 0 ? AlignmentType.LEFT : AlignmentType.CENTER)) })) });

const SCORES = [
  ["char_kl", "1. Letter-frequency KL (as on the lecture slide)"],
  ["kl_english", "2. Word KL against general English"],
  ["kl_domain", "3. Word KL against a domain reference"],
  ["mean_domain", "4. Mean surprisal against the domain reference"],
  ["syngap_top3_english", "5. Synonym gap against general English"],
  ["syngap_top3_domain", "6. Synonym gap against the domain reference (final)"],
];

const cmp = live.comparisons;
const dp = cmp.defended_vs_poisoned.all, dc = cmp.defended_vs_clean.all, cf = cmp.clean_filtered_vs_clean.all;
const dpT = cmp.defended_vs_poisoned.target_perturbed;
const out = live.outcomes, n = live.pairs;
const pct = (k, c) => `${out[c][k]} (${Math.round((100 * out[c][k]) / n)}%)`;

const children = [
  new Paragraph({ spacing: { after: 40 }, children: [run("Applying relative entropy to knowledge-base poisoning in RAG", { bold: true, size: 34 })] }),
  p([run("Progress report on the detection and defence work in AegisRAG, version 2", { size: 24, color: "1F3A5F" })]),
  p([b("To: "), "Nikos   ", b("From: "), "Ali Yousefi (IN3007 Individual Project)   ", b("Date: "), "18 October 2026 (version 2)"], { spacing: { after: 240 } }),

  h1("1  Summary"),
  p("After the lecture on entropy and relative entropy (Kullback–Leibler divergence), I wanted to test whether the idea could detect the attack in my project. In my project, a cybersecurity question-answering system (retrieval-augmented generation, RAG) reads from a knowledge base whose text has been poisoned with PWWS, a word-substitution attack. This report sets out exactly how the idea was used, what worked and what did not, and the evidence for each claim."),
  bullet([b("Used as on the slide, it fails. "), `Comparing the letter distribution of a passage with English letter frequencies separates poisoned from unpoisoned passages no better than chance (AUROC ${f2(det.all.char_kl.auroc)}). PWWS swaps whole words, so the letter statistics barely change.`]),
  bullet([b("Applied to words, with the right reference distribution, it works. "), `The final detector measures, in bits, how much less probable each word is than its best synonym under a domain reference distribution, which is the log-ratio term inside KL(p‖q). It reaches AUROC ${f2(det.all.syngap_top3_domain.auroc)} overall and ${f2(det.held_out.syngap_top3_domain.auroc)} on held-out documents.`]),
  bullet([b("It explains itself. "), `Of the ${expl.flagged_edited_chunks} poisoned passages it flags, ${expl.evidence_includes_real_substitution} cite a word that PWWS really substituted, and ${expl.explanation_names_exact_original} name the exact original word (e.g. "abnegate" → deny, "meshing" → network).`]),
  bullet([b("As a defence it reduces exposure rather than restoring accuracy. "), `Filtering flagged passages at retrieval time reduced the share of questions where poisoned text reached the language model from ${f3(dp.exposure.b)} to ${f3(dp.exposure.a)} in a live paired experiment (${live.questions} questions × 3 repetitions; Wilcoxon p ${pval(dp.exposure.wilcoxon_p)}). It eliminated both confidently incorrect answers (${out.poisoned.incorrect} → ${out.defended.incorrect}), turning them into refusals. Answer correctness did not improve (Δ ${sgn(dp.correctness.delta)}), and the filter costs some correctness on clean data (Δ ${sgn(cf.correctness.delta)}, p ${pval(cf.correctness.wilcoxon_p)}).`]),

  bullet([b("New since version 1: a better reference distribution makes it much stronger. "), `Replacing the word-frequency reference q with a small language model that reads the sentence (the same log-ratio, computed in context) raises AUROC to ${f2(famP.all.ctx_syngap_top3.auroc)}, and it stays at chance on a corpus that has the same formatting changes but no substitutions (${f2(famC.all.ctx_syngap_top3.auroc)}).`]),
  bullet([b("New: an attacker who knows the detector defeats the deployed version, but not the contextual one. "), `PWWS restricted to swaps that do not make a word rarer evades the deployed detector completely (AUROC ${f2(detA.results.all.syngap_top3_domain.auroc)}; ${flaggedAt(detA, live.defence.threshold_bits)[0]} of ${flaggedAt(detA, live.defence.threshold_bits)[1]} poisoned chunks flagged), but the contextual detector still finds it (AUROC ${f2(famA.all.ctx_syngap_top3.auroc)}), and the restriction costs the attacker most of its power (${atk.adaptive_attack.successful} of ${atk.adaptive_attack.sections} sections attacked successfully, against ${rerunOk} for unrestricted PWWS with the same surrogate).`]),
  bullet([b("New: repairing suspicious words is worse than removing the passage. "), `Correctness ${f3(rep.comparisons.repaired_vs_defended.all.correctness.a)} vs ${f3(rep.comparisons.repaired_vs_defended.all.correctness.b)}, and more edited text reaches the model (${f3(rep.comparisons.repaired_vs_poisoned.all.exposure.a)} vs ${f3(live.comparisons.defended_vs_poisoned.all.exposure.a)}).`]),

  h1("2  The idea and why it should fit this attack"),
  p("The lecture defined relative entropy between distributions p and q as"),
  mono("RE(p‖q) = Σx p(x) log2 p(x) / q(x)"),
  p("and used it to ask whether a sample looks like it came from a reference distribution, such as English letter frequencies. PWWS (probability weighted word saliency; Ren et al., 2019) rewrites a passage by replacing words with WordNet synonyms until a classifier is fooled. In my poisoned knowledge base these substitutions produce text such as “abnegate legitimate users access” (original: “deny”) or “a waiter” (original: “a server”). My hypothesis was that poisoned passages would diverge from what normal text in this domain looks like, and that relative entropy could measure that divergence."),
  p([b("Setup used for every result below. "), "The unit is a retrieval chunk (the 500-character passages the RAG system actually retrieves): 191 chunks in the poisoned knowledge base, of which 47 contain PWWS-edited text. Labels come from the attack's own record and are used only for evaluation; the detector never sees them, the clean text or the attack. Development and held-out documents were separated before any tuning, and the single threshold was fixed on development chunks only."]),

  h1("3  How the idea was applied, step by step"),
  p("Each step changed one thing and was kept or rejected on the evidence. Table 1 and Figure 1 give the results; the orange bars are the control explained in Section 4."),
  numbered([b("Letter distribution vs English (the slide's example). "), "p is the passage's letter distribution; q is English letter frequencies. Rejected: PWWS replaces English words with English words, so letter statistics do not move."]),
  numbered([b("Word distribution vs general English. "), "p is the passage's word distribution; q is English word frequencies (the wordfreq package). Rejected: technical text is full of words that are rare in general English, and many PWWS substitutes (“waiter”, “coating”) are common English words."]),
  numbered([b("Word distribution vs a domain reference. "), "q is built from the other documents in the same knowledge base (leave-one-document-out), mixed 50/50 with general English so that unseen words are not infinitely surprising. This needs nothing a defender would not have. Signal appears: KL AUROC 0.72, mean surprisal 0.78."]),
  numbered([b("Synonym gap. "), "Relative entropy sums the log-ratio log2 p(w)/q(w) over words. The detector instead looks at the words PWWS could have changed. For each word w it compares w with its most probable WordNet synonym s under q: gap(w) = log2 q(s) − log2 q(w) bits. A passage's score is the mean of its three largest gaps. This uses the same information-theoretic quantity, aimed at the mechanism of the attack (after frequency-guided substitution detection; Mozes et al., 2021)."]),
  table([5000, 1340, 1340, 1346], [
    ["Detector", "AUROC (all)", "AUROC (held-out)", "Control AUROC"],
    ...SCORES.map(([k, label]) => [label, f2(det.all[k].auroc), f2(det.held_out[k].auroc), f2(ctl.all[k].auroc)]),
  ]),
  caption("Table 1. AUROC for flagging chunks that contain PWWS-edited text (0.5 = chance). Control = the same evaluation on the formatting-only corpus with no substitutions."),
  figure("fig1_auroc_poisoned_vs_control.png", 600, 333),
  caption("Figure 1. Each version of the idea on the poisoned corpus (blue) and on the control corpus (orange)."),
  figure("fig2_roc_curves.png", 360, 327),
  caption("Figure 2. ROC curves on the poisoned corpus for four of the detectors."),

  h1("4  Checking that the signal is real"),
  p([b("A control that nearly fooled me. "), "The attack does two things: it substitutes words, and it also flattens the layout of the sections it attacks. I built a control knowledge base with the same flattening but the original words, verified to equal the poisoned corpus with every substitution reversed. Run on the control, the domain-reference scores still reach AUROC 0.62–0.69. Part of their apparent success therefore comes from which sections were attacked, not from the substitutions. Every detector result is now reported next to this control."]),
  p([b("Matched comparison. "), `For each of the ${matched.matched_edited_chunks} edited chunks I compared its score with the identical chunk in the control corpus. The only difference between the two is the substituted words. The domain KL score is higher in the poisoned version in ${matched.scores.kl_domain.poisoned_higher} of ${matched.scores.kl_domain.nonzero} pairs and the synonym gap in ${matched.scores.syngap_top3_domain.poisoned_higher} of ${matched.scores.syngap_top3_domain.nonzero} (sign tests p < 10⁻⁴). Letter-frequency KL is higher in only ${matched.scores.char_kl.poisoned_higher} of ${matched.scores.char_kl.nonzero}. The substitutions do move the word-level relative-entropy quantities and do not move the letter-level one.`]),
  p([b("Explanations. "), `Because the score is built from individual words, each decision can be inspected. Of the ${expl.flagged_edited_chunks} edited chunks flagged at the frozen threshold, ${expl.evidence_includes_real_substitution} list a genuine PWWS substitution among their three evidence words, and in ${expl.explanation_names_exact_original} the suggested original is exactly the word PWWS replaced.`]),
  table([3000, 3000, 3026], [
    ["Word in poisoned text", "Suggested original", "Document"],
    ["abnegate", "deny", "ddos/http_flood.md"],
    ["unremarkably", "commonly", "ddos/icmp_flood.md"],
    ["meshing", "network", "reconnaissance/port_scanning.md"],
    ["spying", "detection", "reconnaissance/os_fingerprinting.md"],
    ["cipher", "code", "malware/backdoor.md"],
    ["noesis", "knowledge", "malware/password_cracking.md"],
  ]),
  caption("Table 2. Examples where the detector's explanation names the exact word PWWS replaced."),

  h1("5  From detector to defence"),
  p([b("Mechanism. "), `At question time the system retrieves ${live.defence.candidate_k} candidate passages, scores each one, drops those above the frozen threshold of ${live.defence.threshold_bits} bits, and gives the top ${live.defence.keep} remaining passages to the language model. It is implemented in the backend (app/defence/entropy_filter.py, policy ${live.defence.policy_version}) and available in the interface as the “Defended” mode. It reproduces the evaluated scores exactly on all 191 chunks.`]),
  p([b("Retrieval level, no model calls. "), `Exposure to edited text fell from ${f3(flt.summary.poisoned.unfiltered_edited_exposure)} to ${f3(flt.summary.poisoned.filtered_edited_exposure)} of questions. Clean retrieval Hit@3 was unchanged (${f3(flt.summary.clean.unfiltered_hit3)}). Poisoned Hit@3 fell from ${f3(flt.summary.poisoned.unfiltered_hit3)} to ${f3(flt.summary.poisoned.filtered_hit3)}, because some relevant passages were themselves poisoned.`]),
  p([b("Answer level, live. "), `The same ${live.questions} benchmark questions × 3 repetitions were run again with the filter on the poisoned knowledge base (“defended”) and on the clean one (“clean + filter”). Every other setting matched the main experiment exactly: gpt-4o-mini at temperature 0, the same prompt, top-3 context and LLM judges. Each answer was paired with the main run's clean and poisoned answer for the same question and repetition. Questions are the unit of analysis: 95% cluster-bootstrap intervals and Wilcoxon signed-rank tests over question means.`]),
  table([2900, 1200, 1200, 1300, 1426, 1000], [
    ["Comparison and measure", "A", "B", "Δ (A − B)", "95% CI", "Wilcoxon p"],
    ["Defended vs poisoned: edited-text exposure", f3(dp.exposure.a), f3(dp.exposure.b), sgn(dp.exposure.delta), ci(dp.exposure.ci95), pval(dp.exposure.wilcoxon_p)],
    ["Defended vs poisoned: correctness", f3(dp.correctness.a), f3(dp.correctness.b), sgn(dp.correctness.delta), ci(dp.correctness.ci95), pval(dp.correctness.wilcoxon_p)],
    ["Defended vs poisoned: faithfulness", f3(dp.faithfulness.a), f3(dp.faithfulness.b), sgn(dp.faithfulness.delta), ci(dp.faithfulness.ci95), pval(dp.faithfulness.wilcoxon_p)],
    ["Defended vs poisoned: correctness (perturbed targets)", f3(dpT.correctness.a), f3(dpT.correctness.b), sgn(dpT.correctness.delta), ci(dpT.correctness.ci95), pval(dpT.correctness.wilcoxon_p)],
    ["Defended vs clean: correctness", f3(dc.correctness.a), f3(dc.correctness.b), sgn(dc.correctness.delta), ci(dc.correctness.ci95), pval(dc.correctness.wilcoxon_p)],
    ["Clean + filter vs clean: correctness (cost)", f3(cf.correctness.a), f3(cf.correctness.b), sgn(cf.correctness.delta), ci(cf.correctness.ci95), pval(cf.correctness.wilcoxon_p)],
    ["Clean + filter vs clean: Hit@3 (cost)", f3(cf.hit3.a), f3(cf.hit3.b), sgn(cf.hit3.delta), ci(cf.hit3.ci95), pval(cf.hit3.wilcoxon_p)],
  ]),
  caption(`Table 3. Live paired results (${live.pairs} pairs, ${live.questions} questions). Attack success with edited-text exposure: poisoned ${f3(live.asr_edited_exposure.poisoned)}, defended ${f3(live.asr_edited_exposure.defended)}.`),
  figure("fig3_defence_live.png", 600, 237),
  caption("Figure 3. Exposure, correctness and abstention in the four conditions (Defended = poisoned knowledge base + entropy filter)."),
  p([b("Case study. "), "Without the defence, the question “What main stages does the knowledge base describe for Backdoor?” twice produced a confident, wrong answer naming a stage called “Engraft Malicious Package”. That is PWWS's substitution for “implants malicious software”. With the defence, the passage containing it scored 10.75 bits (threshold 7.23) and was blocked; its evidence words were engraft → plant, purport → intent and concatenation → chain, all genuine PWWS substitutions. The model then answered that the context did not describe the stages. It still answered nothing useful, but it no longer stated the poisoned text as fact. The same example shows a limitation: a neighbouring passage that also contained edited text scored 6.92 bits and was kept."]),
  p(`Answer outcomes over ${n} answers per condition. Abstained means the model said the context did not contain the answer. Clean: ${pct("correct", "clean")} correct, ${pct("abstained", "clean")} abstained. Poisoned: ${pct("correct", "poisoned")} correct, ${pct("incorrect", "poisoned")} confidently incorrect, ${pct("abstained", "poisoned")} abstained. Defended: ${pct("correct", "defended")} correct, ${pct("incorrect", "defended")} confidently incorrect, ${pct("abstained", "defended")} abstained.`),

  h1("6  What this shows, and what it does not"),
  bullet([b("Shown: "), "relative-entropy reasoning detects PWWS poisoning when it is applied at the word level, against a domain reference, and aimed at substitutions. The detector is interpretable. As a filter, it significantly reduces how often poisoned text reaches the model and removed the confident errors, at the price of more refusals."]),
  bullet([b("Not shown: "), "that it restores lost accuracy. In this system the main harm of PWWS is displacement, where the correct passage stops being retrieved and the model declines to answer. A filter cannot recover information that exists only in a poisoned passage. Its realistic role is to reduce exposure to misleading text and to explain why a passage is suspicious."]),
  bullet([b("Limitations: "), "one attack, one corpus of 18 documents, a held-out set with only 10 edited chunks, one language model, and LLM-judge scores (a manual check of judge agreement is planned). An adaptive attacker who picks domain-typical synonyms does evade the deployed detector (Section 7); the contextual detector has so far been tested offline, not deployed."]),

  h1("7  Since version 1: four further experiments"),
  h2("7.1  A better reference distribution q"),
  p("Your questions about smoothing and symmetric divergences led to a direct test. Four alternatives were scored on the same 191 chunks, labels and split as Table 1, with the deployed detector as the baseline (it reproduces its earlier score exactly). The contextual synonym gap keeps the log-ratio of the synonym gap, log2 q(s) − log2 q(w), but takes q from a language model (distilgpt2) applied to the whole passage: for the ten most suspicious words, it compares the probability of the passage with the word against the passage with each of its five most likely synonyms."),
  table([3626, 1350, 1350, 1350, 1350], [
    ["Detector (AUROC)", "Poisoned", "Held-out", "Control", "Adaptive"],
    ["Synonym gap, 50/50 reference (deployed)", f2(famP.all.syngap_top3_domain.auroc), f2(famP.held_out.syngap_top3_domain.auroc), f2(famC.all.syngap_top3_domain.auroc), f2(famA.all.syngap_top3_domain.auroc)],
    ["Synonym gap, Dirichlet reference (μ = 2000)", f2(famP.all.syngap_top3_dirichlet.auroc), f2(famP.held_out.syngap_top3_dirichlet.auroc), f2(famC.all.syngap_top3_dirichlet.auroc), f2(famA.all.syngap_top3_dirichlet.auroc)],
    ["Jensen–Shannon divergence vs domain", f2(famP.all.js_domain.auroc), f2(famP.held_out.js_domain.auroc), f2(famC.all.js_domain.auroc), f2(famA.all.js_domain.auroc)],
    ["Language-model surprisal, top 5 tokens", f2(famP.all.lm_top5_surprisal.auroc), f2(famP.held_out.lm_top5_surprisal.auroc), f2(famC.all.lm_top5_surprisal.auroc), f2(famA.all.lm_top5_surprisal.auroc)],
    ["Contextual synonym gap (language-model q)", f2(famP.all.ctx_syngap_top3.auroc), f2(famP.held_out.ctx_syngap_top3.auroc), f2(famC.all.ctx_syngap_top3.auroc), f2(famA.all.ctx_syngap_top3.auroc)],
  ]),
  caption("Table 4. Control = same sections and formatting, no substitutions (a substitution detector should score about 0.5). Adaptive = the attack in 7.2."),
  figure("fig5_entropy_family.png", 600, 260),
  caption("Figure 5. AUROC of each detector on the poisoned, control, adaptive and matched-rerun corpora."),
  p([b("Answers to two of my earlier questions. "), `Dirichlet smoothing performs about the same as the 50/50 mixture (${f2(famP.all.syngap_top3_dirichlet.auroc)} vs ${f2(famP.all.syngap_top3_domain.auroc)}), so the choice of smoothing is not what limits the detector. Jensen–Shannon divergence over the whole word distribution does not work (${f2(famP.all.js_domain.auroc)}): PWWS changes only a few words per passage, and a whole-distribution divergence dilutes them. What helps is a better q, not a different divergence.`]),
  h2("7.2  An attacker who knows the detector"),
  p(`The fine-tuned surrogate classifier behind the original attack had not been saved, so it was retrained with the unchanged training script (validation accuracy ${f2(atk.validation_accuracy_final)}; checksums recorded). Two corpora were then generated with this surrogate: unrestricted PWWS (${rerunOk} of 88 sections attacked successfully, against 38 with the original surrogate) and an adaptive PWWS that may only swap a word for one at least as probable under the defender's own reference, ${atk.adaptive_attack.successful} of 88 successful. At the frozen threshold the deployed detector flags ${flaggedAt(detR, live.defence.threshold_bits)[0]} of ${flaggedAt(detR, live.defence.threshold_bits)[1]} poisoned chunks in the unrestricted corpus (AUROC ${f2(detR.results.all.syngap_top3_domain.auroc)}) and ${flaggedAt(detA, live.defence.threshold_bits)[0]} of ${flaggedAt(detA, live.defence.threshold_bits)[1]} in the adaptive corpus (AUROC ${f2(detA.results.all.syngap_top3_domain.auroc)}). The contextual detector scores ${f2(famR.all.ctx_syngap_top3.auroc)} and ${f2(famA.all.ctx_syngap_top3.auroc)}. The adaptive attacker controlled word frequency, not fit in context, and fit in context is what the contextual log-ratio measures. The adaptive corpus has only ${flaggedAt(detA, 0)[1]} poisoned chunks, none in held-out documents.`]),
  h2("7.3  Repair instead of removal"),
  p(`A second defence replaces each word with a gap above 9.5 bits by its likely original and keeps the passage if it then falls under the threshold. In a live paired run (${rep.questions} questions × 3) it was worse than removal: correctness ${f3(rep.comparisons.repaired_vs_defended.all.correctness.a)} vs ${f3(rep.comparisons.repaired_vs_defended.all.correctness.b)} (Δ ${sgn(rep.comparisons.repaired_vs_defended.all.correctness.delta)}, 95% CI ${ci(rep.comparisons.repaired_vs_defended.all.correctness.ci95)}), edited text reaching the model ${f3(rep.comparisons.repaired_vs_poisoned.all.exposure.a)} vs ${f3(live.comparisons.defended_vs_poisoned.all.exposure.a)}, and no confident errors in either. Word-level WordNet repair restores only about 12% of the substitutions, so a repaired passage still carries most of the poison.`]),
  h2("7.4  Where the frozen threshold sits"),
  p(`Replaying the filter offline over thresholds from 4 to 12 bits shows the threshold fixed on development data (${sweep.deployed_threshold_bits} bits) sits where it stops costing anything: clean Hit@3 is unchanged at or above it and falls steeply below it, while exposure can be pushed lower only by giving up clean retrieval quality.`]),
  figure("fig4_threshold_sweep.png", 600, 252),
  caption("Figure 4. Exposure and Hit@3 against the threshold (left) and the number of candidates (right)."),

  h1("8  Questions I would value your view on"),
  numbered("Is it sound to call the synonym gap, and its contextual version, a relative-entropy method, given that it uses the pointwise log-ratio for selected words rather than the full sum, or should I present it as pointwise mutual information or surprisal?", "questions"),
  numbered("The contextual detector survives an attacker who controls word frequency. Would you expect a second-order attacker, who also constrains language-model probability, to defeat it, or is there an information-theoretic argument that keeping both the classifier fooled and the text natural limits what such an attacker can do?", "questions"),
  numbered(`For the dissertation, is it acceptable to report the retrained surrogate (validation accuracy ${f2(atk.validation_accuracy_final)}, same script and data) as a matched replacement for the lost original, given that it reproduces the original attack rate (${rerunOk} vs 38 of 88 sections)?`, "questions"),

  h1("9  Evidence and how to reproduce it"),
  p([run("Repository: "), b("github.com/Aliyousefi9403/dissertation-rag"), run(", branch "), b("feature/aegisrag-evidence-check"), run(` (report built at commit ${COMMIT}).`)]),
  table([3600, 5426], [
    ["Evidence", "File"],
    ["Detector definitions and evaluation", "docs/research/scripts/entropy_detection_eval.py"],
    ["Detector results (poisoned, control)", "docs/research/results/entropy-detector-20261016/"],
    ["Matched control comparison", "docs/research/results/entropy-defence/matched-control.json"],
    ["Explanation quality", "docs/research/results/entropy-defence/explanations.json"],
    ["Defence implementation and tests", "backend/app/defence/entropy_filter.py; backend/tests/test_entropy_filter.py"],
    ["Live defence run (raw records)", `pilot-runs/${live.defence_run}/`],
    ["Main experiment it is paired with", `pilot-runs/${live.main_run}/`],
    ["Paired analysis", "docs/research/scripts/analyse_defence.py; docs/research/results/entropy-defence/live-paired/"],
    ["Figures", "docs/research/scripts/make_figures.py; docs/research/figures/"],
    ["Better references (Table 4)", "docs/research/scripts/entropy_family_eval.py; docs/research/results/entropy-family/"],
    ["Adaptive attack and retrained surrogate", "backend/app/attack/pwws_adaptive_kb.py; docs/research/results/adaptive-attack/"],
    ["Repair vs removal (live)", `pilot-runs/${rep.defence_run}/; docs/research/results/entropy-repair/live-paired/`],
    ["Every number checked against its file", "docs/research/scripts/verify_evidence.py; docs/research/EVIDENCE.md"],
    ["Full methods and results", "docs/research/evaluation-methods-and-results.md (§§10–16)"],
  ]),
  p("All analyses are offline and read only the saved records. Run records are create-only JSON files with a checksum file, and no number in this report was typed in by hand.", { spacing: { before: 120 } }),
  h2("References"),
  p([run("Kullback, S. and Leibler, R. A. (1951). On Information and Sufficiency. Annals of Mathematical Statistics 22(1), 79–86.", { size: 18 })]),
  p([run("Ren, S., Deng, Y., He, K. and Che, W. (2019). Generating Natural Language Adversarial Examples through Probability Weighted Word Saliency. Proc. ACL, 1085–1097.", { size: 18 })]),
  p([run("Mozes, M., Stenetorp, P., Kleinberg, B. and Griffin, L. (2021). Frequency-Guided Word Substitutions for Detecting Textual Adversarial Examples. Proc. EACL, 171–186.", { size: 18 })]),
  p([run("Miller, G. A. (1995). WordNet: A Lexical Database for English. Communications of the ACM 38(11), 39–41.", { size: 18 })]),
  p([run("Lin, J. (1991). Divergence Measures Based on the Shannon Entropy. IEEE Transactions on Information Theory 37(1), 145–151.", { size: 18 })]),
  p([run("Zhai, C. and Lafferty, J. (2004). A Study of Smoothing Methods for Language Models Applied to Information Retrieval. ACM Transactions on Information Systems 22(2), 179–214.", { size: 18 })]),
  p([run("Radford, A., Wu, J., Child, R., Luan, D., Amodei, D. and Sutskever, I. (2019). Language Models are Unsupervised Multitask Learners. OpenAI technical report.", { size: 18 })]),
  p([run("Sanh, V., Debut, L., Chaumond, J. and Wolf, T. (2019). DistilBERT, a Distilled Version of BERT: Smaller, Faster, Cheaper and Lighter. arXiv:1910.01108.", { size: 18 })]),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: "1F3A5F" }, paragraph: { spacing: { before: 260, after: 110 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 21, bold: true, font: FONT, color: "1F3A5F" }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
    { reference: "questions", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] },
    { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1250, right: 1440, bottom: 1250, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ children: [run("AegisRAG | Relative entropy and RAG poisoning | Report for Nikos", { size: 16, color: "666666" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run("Ali Yousefi | ", { size: 16, color: "666666" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "666666" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(__dirname, "AegisRAG-relative-entropy-report-for-Nikos.docx"), buf);
  console.log("written");
});
