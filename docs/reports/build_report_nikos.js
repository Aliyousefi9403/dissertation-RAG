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
const numbered = (parts) => new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 70, line: 264 },
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
  p([run("Progress report on the detection and defence work in AegisRAG", { size: 24, color: "1F3A5F" })]),
  p([b("To: "), "Nikos   ", b("From: "), "Ali Yousefi (IN3007 Individual Project)   ", b("Date: "), "17 October 2026"], { spacing: { after: 240 } }),

  h1("1  Summary"),
  p("After the lecture on entropy and relative entropy (Kullback–Leibler divergence), I wanted to test whether the idea could detect the attack in my project. In my project, a cybersecurity question-answering system (retrieval-augmented generation, RAG) reads from a knowledge base whose text has been poisoned with PWWS, a word-substitution attack. This report sets out exactly how the idea was used, what worked and what did not, and the evidence for each claim."),
  bullet([b("Used as on the slide, it fails. "), `Comparing the letter distribution of a passage with English letter frequencies separates poisoned from unpoisoned passages no better than chance (AUROC ${f2(det.all.char_kl.auroc)}). PWWS swaps whole words, so the letter statistics barely change.`]),
  bullet([b("Applied to words, with the right reference distribution, it works. "), `The final detector measures, in bits, how much less probable each word is than its best synonym under a domain reference distribution, which is the log-ratio term inside KL(p‖q). It reaches AUROC ${f2(det.all.syngap_top3_domain.auroc)} overall and ${f2(det.held_out.syngap_top3_domain.auroc)} on held-out documents.`]),
  bullet([b("It explains itself. "), `Of the ${expl.flagged_edited_chunks} poisoned passages it flags, ${expl.evidence_includes_real_substitution} cite a word that PWWS really substituted, and ${expl.explanation_names_exact_original} name the exact original word (e.g. "abnegate" → deny, "meshing" → network).`]),
  bullet([b("As a defence it reduces exposure rather than restoring accuracy. "), `Filtering flagged passages at retrieval time reduced the share of questions where poisoned text reached the language model from ${f3(dp.exposure.b)} to ${f3(dp.exposure.a)} in a live paired experiment (${live.questions} questions × 3 repetitions; Wilcoxon p ${pval(dp.exposure.wilcoxon_p)}). Answer correctness did not improve (Δ ${sgn(dp.correctness.delta)}), and the filter has a measurable cost on clean data (Δ ${sgn(cf.correctness.delta)}).`]),

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
  caption("Figure 3. Exposure, correctness and abstention in the four conditions."),
  p(`Answer outcomes over ${n} answers per condition. Abstained means the model said the context did not contain the answer. Clean: ${pct("correct", "clean")} correct, ${pct("abstained", "clean")} abstained. Poisoned: ${pct("correct", "poisoned")} correct, ${pct("incorrect", "poisoned")} confidently incorrect, ${pct("abstained", "poisoned")} abstained. Defended: ${pct("correct", "defended")} correct, ${pct("incorrect", "defended")} confidently incorrect, ${pct("abstained", "defended")} abstained.`),

  h1("6  What this shows, and what it does not"),
  bullet([b("Shown: "), "relative-entropy reasoning detects PWWS poisoning when it is applied at the word level, against a domain reference, and aimed at substitutions. The detector is interpretable, and it reduces how often poisoned text reaches the model."]),
  bullet([b("Not shown: "), "that it restores lost accuracy. In this system the main harm of PWWS is displacement, where the correct passage stops being retrieved and the model declines to answer. A filter cannot recover information that exists only in a poisoned passage. Its realistic role is to reduce exposure to misleading text and to explain why a passage is suspicious."]),
  bullet([b("Limitations: "), "one attack, one corpus of 18 documents, a held-out set with only 10 edited chunks, one language model, and LLM-judge scores (a manual check of judge agreement is planned). An adaptive attacker who picks domain-typical synonyms could evade the detector."]),

  h1("7  Questions I would value your view on"),
  numbered("Is the 50/50 mixture of domain and general-English frequencies a reasonable way to avoid zero probabilities, or would you expect a principled smoothing method (e.g. Good–Turing or a Dirichlet prior) to behave better here?"),
  numbered("Would a symmetric measure such as Jensen–Shannon divergence be more appropriate than KL for comparing a short passage with a large reference?"),
  numbered("Is it sound to call the synonym gap a relative-entropy method, given that it uses the log-ratio term per word rather than the full sum, or should I present it as surprisal-based?"),

  h1("8  Evidence and how to reproduce it"),
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
    ["Full methods and results", "docs/research/evaluation-methods-and-results.md (§§10–12)"],
  ]),
  p("All analyses are offline and read only the saved records. Run records are create-only JSON files with a checksum file, and no number in this report was typed in by hand.", { spacing: { before: 120 } }),
  h2("References"),
  p([run("Kullback, S. and Leibler, R. A. (1951). On Information and Sufficiency. Annals of Mathematical Statistics 22(1), 79–86.", { size: 18 })]),
  p([run("Ren, S., Deng, Y., He, K. and Che, W. (2019). Generating Natural Language Adversarial Examples through Probability Weighted Word Saliency. Proc. ACL, 1085–1097.", { size: 18 })]),
  p([run("Mozes, M., Stenetorp, P., Kleinberg, B. and Griffin, L. (2021). Frequency-Guided Word Substitutions for Detecting Textual Adversarial Examples. Proc. EACL, 171–186.", { size: 18 })]),
  p([run("Miller, G. A. (1995). WordNet: A Lexical Database for English. Communications of the ACM 38(11), 39–41.", { size: 18 })]),
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
