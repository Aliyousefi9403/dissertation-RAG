// Builds AegisRAG-Project-Definition-Document.docx (IN3007 PDD).
// Run: node build_pdd.js   (from docs/pdd/)
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Header, Footer, AlignmentType, HeadingLevel,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, LevelFormat, PageNumber,
} = require("docx");

const FONT = "Arial";
const W = 9026; // A4 text width at 1" margins (DXA)

const p = (text, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 276 }, ...opts,
  children: (Array.isArray(text) ? text : [text]).map((t) => typeof t === "string" ? new TextRun(t) : t),
});
const b = (t) => new TextRun({ text: t, bold: true });
const i = (t) => new TextRun({ text: t, italics: true });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (runs) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80, line: 264 },
  children: (Array.isArray(runs) ? runs : [runs]).map((t) => typeof t === "string" ? new TextRun(t) : t) });
const ref = (t) => new Paragraph({ spacing: { after: 80, line: 252 }, indent: { left: 400, hanging: 400 }, children: [new TextRun({ text: t, size: 19 })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cell = (text, width, head = false) => new TableCell({
  width: { size: width, type: WidthType.DXA },
  borders: { top: border, bottom: border, left: border, right: border },
  shading: head ? { fill: "E8EEF4", type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 70, bottom: 70, left: 110, right: 110 },
  children: [new Paragraph({ spacing: { after: 0, line: 252 }, children: [new TextRun({ text, bold: head, size: 20 })] })],
});
const table = (widths, rows) => new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: widths,
  rows: rows.map((r, n) => new TableRow({ children: r.map((t, k) => cell(t, widths[k], n === 0)) })),
});

const children = [
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "AegisRAG — Project Definition Document", bold: true, size: 36 })] }),
  p([b("Project title: "), "Evaluating answer reliability under knowledge base poisoning in cybersecurity RAG systems"]),
  p(["Ali Yousefi | BSc Computer Science | IN3007 Individual Project | ", "November 2026"], { spacing: { after: 240 } }),

  h1("1 Abstract"),
  p("I propose to develop and evaluate AegisRAG, a cybersecurity question-answering system that compares responses generated from a clean knowledge base and from a deliberately altered copy. My aim is to measure how a word-substitution poisoning attack affects retrieval and answer quality, and to investigate whether practical reliability indicators can identify answers that need checking. I will use a controlled text attack (PWWS), a reviewed and frozen benchmark, a formatting-only control condition and repeated paired experiments. I will evaluate evidence support and answer consistency, separate answers that are wrong from answers that decline for lack of evidence, and examine cases where incorrect answers are stated confidently. The project will produce a working comparison interface, a versioned benchmark, recorded experimental evidence and reproducible tables and figures. It will assess the usefulness and limitations of these indicators rather than claim to create a new general-purpose defence."),

  h1("2 Introduction and problem statement"),
  p("Retrieval-augmented generation (RAG) retrieves relevant passages and gives them to a language model to help it answer a question [1]. This makes the source material part of the system's trust boundary: a plausible but misleading passage can influence the answer, and an answer may sound certain even when its evidence is unreliable. Knowledge-corruption attacks show that injecting a few crafted texts into a retrieval corpus can steer answers to attacker-chosen targets [4], and that adversarial passages can mislead dense retrievers across domains [5]. Work on an LLM-based threat detection and mitigation framework shows that word-level adversarial perturbation of its knowledge base, using TextFooler [6], degrades the framework [2]. My attack condition instead uses probability weighted word saliency (PWWS) [3], implemented with TextAttack [7]. I will treat this as a distinct experimental setting rather than claim to reproduce the original study."),
  p("The practical problem is that users can mistake a fluent, well-supported-looking response for a correct one. A retrieved passage can be relevant and still misleading, and a poisoned passage can even support a false answer. Defences with formal guarantees exist, for example isolating and aggregating per-passage answers [11], but they change the pipeline and do not tell a user whether a particular answer should be trusted. I will therefore assess retrieval quality, answer correctness and reliability indicators separately, so the evaluation shows where a failure occurs and whether it can be flagged."),

  h1("3 Aims, objectives and research question"),
  p("My overall aim is to build an auditable experimental framework for measuring the effects of knowledge base poisoning and for evaluating observable indicators of answer reliability."),
  p([b("Research question. "), "To what extent does knowledge base poisoning reduce retrieval and answer quality in a cybersecurity RAG system, and how well can selected reliability indicators distinguish incorrect answers from correct answers under clean and poisoned conditions?"]),
  bullet([b("Objective 1 – Define the experiment. "), "Review the literature and specify the attacker's access, the permitted text changes, fixed system settings and evaluation rules. Output: a literature comparison and a written protocol frozen before the main experiment."]),
  bullet([b("Objective 2 – Build a reviewed benchmark. "), "At least 44 questions across 14 attack types in 5 categories, each with a stable identifier, atomic reference facts and an exact source anchor (file hash and character offsets). Development and held-out questions are separated by source document, chosen before any main run. Output: a versioned benchmark with a review record."]),
  bullet([b("Objective 3 – Run controlled comparisons. "), "Clean, PWWS-poisoned and formatting-only control knowledge bases in separate collections, with matched retrieval and generation settings. Classifier attack success is reported separately from effects on the RAG system. Output: repeatable paired runs with saved answers, retrieved passages and errors."]),
  bullet([b("Objective 4 – Implement bounded reliability indicators. "), "(a) Evidence support: claims checked against retrieved passages with verbatim quotations; (b) consistency: agreement of key claims across k additional sampled answers at temperature above zero, following sampling-based self-checking [8]. Fixed rubrics; outputs are documented scores and warning rules, never calibrated probabilities."]),
  bullet([b("Objective 5 – Measure effects and indicator usefulness. "), "Correctness, faithfulness, Hit@3, mean reciprocal rank, edited-text exposure and an outcome category (correct / incorrect / abstained). Indicators are evaluated against reference-based error labels (precision, recall, false alarms) with thresholds chosen on development data and then frozen. Output: reproducible tables, plots and uncertainty estimates, including negative findings."]),
  bullet([b("Objective 6 – Deliver an auditable system and report. "), "A comparison interface that shows answers, evidence and indicator results; automated tests; run instructions; saved experiment records; and a dissertation explaining methods and limitations. Every reported number must be traceable to its question, source material, settings and analysis code."]),
  p([b("Scope and success criteria. "), "The core project uses one RAG pipeline, PWWS as the attack and two candidate indicators. Additional attacks, model comparisons and active defences are extensions only if time permits. Success means a reproducible evaluation with clear limitations, including negative findings; it does not depend on a predetermined attack effect or detection accuracy."], { spacing: { before: 120, after: 120 } }),

  h1("4 Technical approach and methodology"),
  h2("System architecture"),
  p("Python and FastAPI for the backend, Qdrant for vector retrieval and Next.js for the comparison interface. The interface sends the same question to the clean and poisoned conditions and displays answers and retrieved evidence side by side; an optional evidence-check mode shows the claim-level result. An experiment runner uses the same pipeline and records outputs for offline analysis."),
  h2("Knowledge base and controlled poisoning"),
  p("The knowledge base is a local, versioned collection of MITRE ATT&CK and CAPEC material (18 documents), split into overlapping passages that keep their document identity and position. A DistilBERT attack-type classifier acts as a surrogate target: PWWS proposes word substitutions against it, and successfully attacked sections are written to a separate poisoned copy. Original and altered text are recorded in an attack manifest. Because the poisoning script also flattens the layout of attacked sections, I add a formatting-only control copy in which the same sections are flattened but keep their original words; clean, control and poisoned then isolate layout effects from substitution effects. Classifier success is reported as successful ÷ (successful + failed) attacks, separately from any transfer to retrieval or answers."),
  h2("Matched generation and benchmark"),
  p("The same embedding model, retrieval depth (three passages), prompt and language-model settings are used in every condition, and all versions and settings are recorded. The attacker may alter eligible source text but not the question, reference facts or evaluation code. The benchmark has 44 reviewed questions (35 development, 9 held out on four documents not used in the pilot). Reference facts are verbatim source sentences, except CAPEC consequence fields, which are rewritten as plain impact statements and flagged as derived."),
  h2("Pilot evidence and repeated evaluation"),
  p("A 12-question pilot (three repetitions, 216 recorded model calls, no error records) confirmed complete recording and offline reproducibility. It showed lower poisoned retrieval (Hit@3 0.92 → 0.50) and correctness (0.88 → 0.67), mostly because the relevant passage was displaced and the model declined to answer, and retrieval was identical across repetitions. With the formatting-only control, Hit@3 equals the clean condition on both the pilot set (0.92) and the 44-question benchmark (0.70, against 0.57 when poisoned), so the retrieval drop comes from the word substitutions rather than from the layout change. These are pilot observations on development questions, not main results. In the main evaluation, repetitions will not be treated as independent questions; failures stay in the record and are reported as missing, not as zero scores. The protocol is frozen before the main run and later amendments are recorded."),
  h2("Reliability indicators and confident errors"),
  p("The evidence-support indicator uses a separate verifier call: it splits the answer into claims, labels each supported, unsupported or contradicted by the retrieved passages, and must give quotations that are checked verbatim against those passages. A versioned policy releases an answer only if every claim is supported, records abstentions separately, and never treats a failed check as a pass. The consistency indicator compares claims across sampled answers. A stratified sample is manually checked for assertive language alongside correctness labels; assertive wording, self-reported certainty and calibrated probability are kept distinct. Because poisoned evidence can support a wrong answer, missed errors and false alarms are reported explicitly, and indicators are compared with simple retrieval-score baselines and with a word-substitution detection approach [9]."),
  h2("Measurements"),
  bullet([b("Answer correctness "), "against atomic reference facts with a fixed rubric (LLM judge), plus manual checks on a stratified sample to estimate judge agreement, given known judge biases [10]."]),
  bullet([b("Faithfulness: "), "whether the answer's claims follow from the retrieved passages [12]. A faithful answer can still be wrong if the passages are misleading; abstentions are reported separately rather than scored as unfaithful."]),
  bullet([b("Hit@3 and mean reciprocal rank "), "using a documented section-level relevance rule."]),
  bullet([b("Exposure: "), "both whether an attacked section was retrieved and whether actually edited text was retrieved; edited-text exposure is the primary measure. Exposure is not harm."]),
  bullet([b("Indicator performance: "), "precision, recall and false-positive rate against reference-based error labels, with counts and uncertainty; plus latency and model-call cost."]),
  h2("Evidence recording and statistical analysis"),
  p("Each run stores its ID, benchmark hash, corpus snapshots and hashes, attack manifest, code version, settings, retrieved passages, answers, raw evaluations, timings and errors, in create-only files with a checksum record. Scripts regenerate every table and figure from these records. I will report paired clean-versus-poisoned differences, results stratified by attack type and by whether a question's target section was actually perturbed, and question-level (cluster) bootstrap intervals that respect pairing and source groups. No result will be described as statistically significant without an appropriate test."),
  h2("Testing and deliverables"),
  p("Automated tests cover document identities, passage offsets, metric calculations, verifier-output validation, failed-run handling and record integrity; integration checks cover retrieval, the API and the interface. Deliverables: the application, the documented benchmark, attack and control records, experiment outputs, analysis scripts, tables and figures, run instructions and the dissertation."),

  h1("5 Milestones and project management"),
  table([2300, W - 2300], [
    ["Period", "Planned work and checkpoint"],
    ["Oct – 11 Nov 2026", "Consultant meetings; literature review; threat model; benchmark review and freeze (v1); control corpus; PDD submitted by Wed 11 Nov, 20:00."],
    ["Nov – Dec 2026", "Verify and analyse the first full clean/poisoned run on benchmark v1; add the control condition to the runner; manual judge-agreement sample."],
    ["Jan 2027", "Implement and test the consistency indicator; finalise the evidence-support indicator; choose thresholds on development data only."],
    ["Feb 2027", "Held-out evaluation and uncertainty analysis; final ethics materials submitted by Sun 21 Feb, 17:00."],
    ["Mar – 4 Apr 2027", "Tables, figures, dissertation and reproducibility checks; submission of all elements by Sun 4 Apr, 17:00."],
    ["1 – 11 Jun 2027", "Project review (in person) with demonstration."],
  ]),
  p("Dependencies: the benchmark must be frozen before the main experiments; the pilot must show complete recording before larger runs; thresholds are frozen before held-out evaluation; tables must be reproducible from saved records before the report is finalised. I keep version control on GitHub, backups, a weekly progress log and a decision record, and reserve time for failed runs and corrections, cutting optional extensions if the core work is at risk.", { spacing: { before: 160, after: 120 } }),

  h1("6 Project risks"),
  p("The attack changes stored text only; it does not execute malware or attack any system, and retrieved content is treated as data with no authority to run commands."),
  table([2600, W - 2600], [
    ["Risk", "Mitigation"],
    ["Scope and schedule", "One attack and two indicators are the core; extensions only if milestones are met."],
    ["Data loss or contamination", "Separate collections per condition; create-only records with checksums; hashes of corpora and benchmark checked before every run; backups on GitHub."],
    ["Cost and service failures", "Call volume measured in the pilot (216 calls) and planned per full run (792 calls); spending limit; explicit timeouts and bounded retries; completed records analysed offline."],
    ["Invalid conclusions", "Frozen protocol, held-out split, formatting-only control, manual judge checks, question-level uncertainty; limitations reported."],
    ["Weak attack transfer or weak indicators", "Treated as findings, not reasons to redefine success after seeing the data."],
  ]),

  h1("7 Legal, social, ethical and professional issues"),
  p([b("Legal and information handling. "), "MITRE ATT&CK and CAPEC content is used under MITRE's terms of use with attribution, and licences of datasets, model weights and software are recorded. Question, passage and answer text is sent to the OpenAI API; it contains no personal or confidential data, and the provider and settings are documented. API keys are kept outside the repository and are redacted from saved evidence."]),
  p([b("Social and ethical considerations. "), "The system could give misleading cybersecurity advice: a warning may miss an incorrect answer and a false alarm may discourage a correct one. AegisRAG is presented as a research prototype, and no score is described as proof that an answer is true or that a source is clean. The study uses public documents and synthetic questions with no participants; I will complete the university's ethics screening before any activity that needs approval and seek approval before any user testing."]),
  p([b("Professional practice. "), "I distinguish planned methods, implemented functionality and measured results; document assumptions, failed runs and protocol changes; and do not claim a new defence, a universal vulnerability or statistical significance without evidence. AI tools assisted with drafting, coding and organising this work; I record and acknowledge this assistance in line with the module's policy and remain responsible for checking all code, references and conclusions."]),

  h1("References"),
  ref("[1] Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 33. https://arxiv.org/abs/2005.11401"),
  ref("[2] Ikbarieh, S., Aryal, K. and Gupta, M. (2025). RAG-targeted Adversarial Attack on LLM-based Threat Detection and Mitigation Framework. arXiv:2511.06212."),
  ref("[3] Ren, S., Deng, Y., He, K. and Che, W. (2019). Generating Natural Language Adversarial Examples through Probability Weighted Word Saliency. Proc. ACL, 1085–1097. https://doi.org/10.18653/v1/P19-1103"),
  ref("[4] Zou, W., Geng, R., Wang, B. and Jia, J. (2025). PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models. USENIX Security Symposium. arXiv:2402.07867"),
  ref("[5] Zhong, Z., Huang, Z., Wettig, A. and Chen, D. (2023). Poisoning Retrieval Corpora by Injecting Adversarial Passages. Proc. EMNLP, 13764–13775."),
  ref("[6] Jin, D., Jin, Z., Zhou, J. T. and Szolovits, P. (2020). Is BERT Really Robust? A Strong Baseline for Natural Language Attack on Text Classification and Entailment. Proc. AAAI 34(5), 8018–8025."),
  ref("[7] Morris, J. et al. (2020). TextAttack: A Framework for Adversarial Attacks, Data Augmentation, and Adversarial Training in NLP. Proc. EMNLP: System Demonstrations, 119–126."),
  ref("[8] Manakul, P., Liusie, A. and Gales, M. (2023). SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. Proc. EMNLP, 9004–9017."),
  ref("[9] Mozes, M., Stenetorp, P., Kleinberg, B. and Griffin, L. (2021). Frequency-Guided Word Substitutions for Detecting Textual Adversarial Examples. Proc. EACL, 171–186."),
  ref("[10] Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 36, Datasets and Benchmarks Track."),
  ref("[11] Xiang, C., Wu, T., Zhong, Z., Wagner, D., Chen, D. and Mittal, P. (2024). Certifiably Robust RAG against Retrieval Corruption. arXiv:2405.15556."),
  ref("[12] Es, S., James, J., Espinosa Anke, L. and Schockaert, S. (2024). RAGAs: Automated Evaluation of Retrieval Augmented Generation. Proc. EACL: System Demonstrations, 150–158."),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "1F3A5F" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FONT, color: "1F3A5F" }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, right: 1440, bottom: 1300, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ children: [new TextRun({ text: "Ali Yousefi | IN3007 Individual Project | Project Definition Document", size: 17, color: "666666" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "AegisRAG | ", size: 17, color: "666666" }), new TextRun({ children: [PageNumber.CURRENT], size: 17, color: "666666" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("AegisRAG-Project-Definition-Document.docx", buf);
  console.log("written");
});
