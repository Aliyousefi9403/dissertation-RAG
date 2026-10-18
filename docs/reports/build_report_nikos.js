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
  new Paragraph({ spacing: { after: 40 }, children: [run("Using your relative-entropy idea to catch poisoned text in my RAG project", { bold: true, size: 32 })] }),
  p([b("To: "), "Nikos   ", b("From: "), "Ali Yousefi (IN3007 Individual Project)   ", b("Date: "), "18 October 2026"], { spacing: { after: 200 } }),

  h1("Where this came from"),
  p("My project, AegisRAG, is a cybersecurity question-answering system that reads from a knowledge base before it answers (retrieval-augmented generation, RAG). I attack that knowledge base with PWWS, which quietly swaps words for synonyms, for example “deny” becomes “abnegate” and “server” becomes “waiter”. The text still reads almost normally, but the answers get worse."),
  p("You suggested looking at it through relative entropy: compare a passage's word distribution p with what normal text looks like, q, using KL(p‖q) = Σ p(x) log₂ p(x)/q(x). I followed that idea all the way through, and this note is a short account of what happened."),

  h1("What I tried"),
  numbered([b("Letters vs English. "), `It does not work (AUROC ${f2(det.all.char_kl.auroc)}, where 0.5 is chance). PWWS swaps whole words, so letter counts barely move.`]),
  numbered([b("Words vs a domain reference. "), `I built q from the other documents in the knowledge base (each document left out of its own reference) mixed with general English. Now there is a signal (${f2(det.all.kl_domain.auroc)}).`]),
  numbered([b("The synonym gap. "), `Instead of the full sum, I look at the log-ratio term for each word: how many bits more likely its best synonym is than the word itself, log₂ q(synonym) − log₂ q(word). “abnegate” scores high because “deny” is far more likely. AUROC ${f2(det.all.syngap_top3_domain.auroc)}, and ${f2(det.held_out.syngap_top3_domain.auroc)} on documents I never tuned on.`]),
  numbered([b("A language model as q. "), `Same log-ratio, but q now comes from a small language model (distilgpt2) that reads the whole sentence. AUROC ${f2(famP.all.ctx_syngap_top3.auroc)}.`]),
  p(`A nice side effect is that it explains itself: of ${expl.flagged_edited_chunks} poisoned passages it flagged, ${expl.explanation_names_exact_original} name the exact word PWWS replaced (abnegate → deny, meshing → network, noesis → knowledge).`),

  h1("Checking it was real"),
  p(`The attack also changes the layout of the sections it touches, so a detector could just be spotting layout. I built a control copy with the same layout changes but no word swaps. The word-frequency version still scores ${f2(famC.all.syngap_top3_domain.auroc)} there, so part of its signal is layout. The language-model version scores ${f2(famC.all.ctx_syngap_top3.auroc)}, which is chance, so it really is reacting to the swapped words.`),
  p([b("Two things I wondered about. "), `Would better smoothing or a symmetric divergence help? A Dirichlet prior instead of the 50/50 mix makes almost no difference (${f2(famP.all.syngap_top3_dirichlet.auroc)} vs ${f2(famP.all.syngap_top3_domain.auroc)}). Jensen–Shannon over the whole distribution does not work (${f2(famP.all.js_domain.auroc)}): only a few words change per passage, and a whole-distribution measure dilutes them. What helped was a better q, not a different divergence.`]),

  h1("Using it as a defence"),
  p(`In the live system the detector sits in front of the model: it fetches ${live.defence.candidate_k} passages, drops any that score above a threshold fixed on development data (${live.defence.threshold_bits} bits), and passes the best ${live.defence.keep} that are left. On ${live.questions} questions × 3 runs:`),
  bullet(`Poisoned text reached the model on ${Math.round(100 * dp.exposure.b)}% of questions before and ${Math.round(100 * dp.exposure.a)}% after (Wilcoxon p ${pval(dp.exposure.wilcoxon_p)}).`),
  bullet(`Confidently wrong answers went from ${out.poisoned.incorrect} to ${out.defended.incorrect}. In one case the model had been repeating a poisoned stage called “Engraft Malicious Package”; with the defence it said it could not find the answer instead.`),
  bullet(`Accuracy did not come back (${sgn(dp.correctness.delta)}), and I also tried repairing the suspicious words instead of dropping the passage, which was slightly worse (${f3(rep.comparisons.repaired_vs_defended.all.correctness.a)} vs ${f3(rep.comparisons.repaired_vs_defended.all.correctness.b)}). So for now it is a safety filter, not a fix.`),

  h1("Trying to break it"),
  p(`A detector is only interesting if it survives someone who knows about it. I changed PWWS so it may only swap a word for one that is at least as common under my own q. Against that attacker, the word-frequency detector fails completely (${f2(detA.results.all.syngap_top3_domain.auroc)}, ${flaggedAt(detA, live.defence.threshold_bits)[0]} of ${flaggedAt(detA, live.defence.threshold_bits)[1]} poisoned passages caught). The language-model version still catches it (${f2(famA.all.ctx_syngap_top3.auroc)}), because the attacker matched how common words are, not whether they fit the sentence. Being sneaky also cost the attacker a lot: it succeeded on ${atk.adaptive_attack.successful} of 88 sections, against ${rerunOk} for the normal attack with the same setup.`),
  figure("fig5_entropy_family.png", 560, 322),
  caption("How well each version finds poisoned passages on four versions of the knowledge base (0.5 = chance)."),

  h1("What I'd love your view on"),
  numbered("Is it fair to call this a relative-entropy method, since it uses the log-ratio for a few words rather than the full KL sum, or would you describe it differently?", "questions"),
  numbered("Do you think an attacker who also matches the language model could beat the contextual version, or is there an information-theory reason that fooling the classifier while staying natural is hard?", "questions"),
  numbered("Is there anything in how I built q that you would do differently?", "questions"),

  h1("Where everything is"),
  p([run("Code, data and every run are on GitHub: "), b("github.com/Aliyousefi9403/dissertation-rag"), run(", branch "), b("feature/aegisrag-evidence-check"), run(` (commit ${COMMIT}). The file docs/research/EVIDENCE.md checks each number above against the file it came from, and the full write-up is docs/research/evaluation-methods-and-results.md. I am happy to walk you through any of it.`)]),
  h2("References"),
  p([run("Kullback and Leibler (1951), On Information and Sufficiency. Ren et al. (2019), PWWS, ACL. Mozes et al. (2021), Frequency-Guided Word Substitutions for Detecting Textual Adversarial Examples, EACL. Lin (1991), Divergence Measures Based on the Shannon Entropy. Zhai and Lafferty (2004), smoothing methods for language models. Radford et al. (2019), GPT-2. Miller (1995), WordNet.", { size: 18 })]),
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
    headers: { default: new Header({ children: [new Paragraph({ children: [run("AegisRAG | Relative entropy and RAG poisoning | Ali Yousefi", { size: 16, color: "666666" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run("Ali Yousefi | ", { size: 16, color: "666666" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "666666" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(__dirname, "AegisRAG-relative-entropy-report-for-Nikos.docx"), buf);
  console.log("written");
});
