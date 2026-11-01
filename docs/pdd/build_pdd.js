// Builds AegisRAG-Project-Definition-Document.docx (IN3007 PDD, structure of Project Handbook 2026/27 §4.5).
// Run: node build_pdd.js   (from docs/pdd/; needs gantt.png from make_gantt.py)
// Word limit (BSc): 1,700 words excluding the cover page, references and Appendix A; check with count_words.py.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Footer, AlignmentType, HeadingLevel, ImageRun, PageBreak,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, LevelFormat, PageNumber,
} = require("docx");

const FONT = "Arial";
const W = 9026; // A4 text width at 2.5 cm margins (DXA)
const SZ = 22; // 11 pt

const runs = (parts) => (Array.isArray(parts) ? parts : [parts]).map((t) => (typeof t === "string" ? new TextRun(t) : t));
const p = (parts, opts = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...opts, children: runs(parts) });
const b = (t) => new TextRun({ text: t, bold: true });
const i = (t) => new TextRun({ text: t, italics: true });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80, line: 264 }, children: runs(parts) });
const ref = (t) => new Paragraph({ spacing: { after: 60, line: 252 }, indent: { left: 400, hanging: 400 }, children: runs(t) });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cell = (text, width, head = false) => new TableCell({
  width: { size: width, type: WidthType.DXA },
  borders: { top: border, bottom: border, left: border, right: border },
  shading: head ? { fill: "E8EEF4", type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  children: [new Paragraph({ spacing: { after: 0, line: 240 }, children: [new TextRun({ text, bold: head, size: 19 })] })],
});
const table = (widths, rows) => new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: widths,
  rows: rows.map((r, n) => new TableRow({ children: r.map((t, k) => cell(t, widths[k], n === 0)) })),
});
const coverLine = (label, value) => p([b(label + ": "), value], { spacing: { after: 140 } });

const WORDS = process.env.PDD_WORDS || "[word count]";

const cover = [
  new Paragraph({ spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "Project Definition Document", bold: true, size: 36 })] }),
  new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: "IN3007 Individual Project, 2026/27", size: 24, color: "444444" })] }),
  coverLine("Degree programme", "BSc (Hons) Computer Science"),
  coverLine("Project title", "AegisRAG: detecting word-substitution poisoning of a cybersecurity RAG knowledge base with relative entropy and runtime verification"),
  coverLine("Student", "Ali Yousefi (240061480), ali.yousefi@citystgeorges.ac.uk"),
  coverLine("Consultant", "Hafizul Asad"),
  coverLine("Client", "None (academic research project)"),
  coverLine("Proposed by", "Ali Yousefi; the relative-entropy detection approach was suggested by Nikos Komninos, and the runtime-verification monitor by Hafizul Asad"),
  coverLine("Other promises made", "None"),
  coverLine("Word count", `${WORDS} words (excluding cover page, references and Appendix A)`),
  new Paragraph({ children: [new PageBreak()] }),
];

const body = [
  h1("1 Problem to be solved"),
  p("Retrieval-augmented generation (RAG) answers questions by retrieving passages from a knowledge base and passing them to a large language model (Lewis et al., 2020). The knowledge base therefore becomes part of the system's trust boundary. Injected passages can steer RAG answers (Zhong et al., 2023; Zou et al., 2025), and word-level perturbation of a knowledge base degrades the mitigation advice of an LLM-based security framework (Ikbarieh, Aryal and Gupta, 2025). Attacks such as PWWS (Ren et al., 2019) and TextFooler (Jin et al., 2020) replace words with plausible synonyms, so poisoned text still reads almost normally."),
  p("Two problems follow for a cybersecurity question-answering assistant. First, it is not known how much in-place word substitution harms retrieval and answers, or through what mechanism. Second, existing defences either change the generation pipeline (Xiang et al., 2024), need access to the attacked classifier (Mozes et al., 2021), or filter whole inputs by language-model perplexity (Jain et al., 2023); none tells an operator which retrieved passages look tampered with, or which words. Information theory suggests a test: a substituted word should be improbable under a reference distribution q of normal text, measurable with relative entropy (Kullback and Leibler, 1951). Whether such a detector works, which reference it needs, and whether it survives an attacker who knows it, is an open question. A third problem is that a filter learns nothing: the same poisoned passage is judged afresh each time, and removing it also removes evidence. Runtime verification checks a running system against formal properties (Leucker and Schallhart, 2009; Bartocci et al., 2018); whether a monitor that checks answers against a trusted reference, and remembers what misled it, can help is also untested."),

  h1("2 Project objectives"),
  p([b("Main objective. "), "This project shall build AegisRAG, an auditable cybersecurity RAG system with clean and poisoned knowledge bases, and use it to measure the effect of word-substitution poisoning to evaluate relative-entropy detection of poisoned passages as a retrieval-time defence, and to evaluate a runtime verification monitor that checks answers against trusted MITRE data."]),
  p([b("Research questions. "), "RQ1: How much does PWWS poisoning reduce retrieval quality and answer correctness, and through what mechanism? RQ2: How well do relative-entropy detectors, with word-frequency and language-model references, identify poisoned passages, and do they react to substitutions rather than formatting? RQ3: Does filtering detected passages reduce exposure to poisoned text and confidently wrong answers, and at what cost on clean data? RQ4: Does detection survive adaptive attackers and a second attack (TextFooler)? RQ5: Does a runtime monitor with feedback and a quarantine memory reduce exposure and wrong answers, and can a trusted fallback restore correctness?"]),
  p([b("Hypotheses. "), "H1: poisoning lowers correctness only for questions whose source section was perturbed. H2: a per-word log-ratio detector exceeds AUROC 0.8 on poisoned passages and stays near 0.5 on a formatting-only control. H3: filtering significantly reduces exposure with no significant correctness loss on clean data. H4: an attacker constrained to evade the detector loses most of its successful attacks. H5: the monitor significantly reduces exposure at no significant clean-data cost, and never re-admits a quarantined passage."]),
  p(b("Sub-objectives and how each will be tested")),
  bullet([b("O1. "), "Build the RAG system and comparison interface (FastAPI, Qdrant, Next.js). ", i("Test: "), "automated tests pass; the same question returns recorded answers and sources from each corpus."]),
  bullet([b("O2. "), "Create clean, PWWS-poisoned and formatting-only control knowledge bases from MITRE ATT&CK and CAPEC. ", i("Test: "), "attack manifest records every original and edited section; corpora are checksummed."]),
  bullet([b("O3. "), "Build and freeze a reviewed benchmark of at least 44 questions with reference facts and source anchors, split into development and held-out documents. ", i("Test: "), "benchmark hash recorded before the main run."]),
  bullet([b("O4. "), "Run paired, repeated clean-versus-poisoned evaluations. ", i("Test: "), "complete create-only records; question-level bootstrap intervals and Wilcoxon tests answer RQ1."]),
  bullet([b("O5. "), "Implement relative-entropy detectors (KL divergence, surprisal, synonym gap with word-frequency and language-model references). ", i("Test: "), "AUROC on poisoned, control and held-out passages answers RQ2 and H2."]),
  bullet([b("O6. "), "Deploy the best detectors as retrieval filters and evaluate them live. ", i("Test: "), "paired exposure, correctness, abstention and clean-data cost answer RQ3 and H3; a blind manual check of the LLM judge (Zheng et al., 2023) reports agreement."]),
  bullet([b("O7. "), "Evaluate adaptive attackers and TextFooler. ", i("Test: "), "attack success and detector AUROC per attacker answer RQ4 and H4."]),
  bullet([b("O8. "), "Evaluate the answer evidence-check indicator (Es et al., 2024). ", i("Test: "), "precision, recall and false alarms against reference-based error labels."]),
  bullet([b("O9. "), "Build and evaluate a runtime verification monitor: three properties derived from hash-pinned MITRE STIX data (no rare non-MITRE word copied from the passages; no refusal when MITRE covers the attack; in linear temporal logic (Pnueli, 1977), a quarantined passage never re-enters the context), an append-only quarantine memory, regeneration with feedback, and an optional trusted fallback. ", i("Test: "), "unit tests; the temporal property checked on every trace; paired live runs on poisoned, clean and TextFooler corpora, with quarantine precision, answer RQ5 and H5."]),

  h1("3 Project beneficiaries"),
  p("The first beneficiaries are researchers in RAG security and adversarial NLP, who receive a measured attack mechanism, a detector with its failure modes, and a reproducible benchmark, corpora and evaluation records. Developers of security assistants benefit from a defence that needs no access to the attacked model and explains each decision, and from runtime verification applied to language-model output. Security analysts using such assistants benefit later, if these results inform deployed systems. By the end of the project, benefit will be shown by the objective tests above, a public code and data release, and a research paper submitted for peer review."),

  h1("4 Work plan"),
  p("The project follows an iterative, experiment-driven method: build the minimal pipeline, freeze the benchmark and protocol, pilot, then add detectors and attackers one at a time, each evaluated against fixed settings (gpt-4o-mini, temperature 0, all-MiniLM-L6-v2 embeddings, top-3 retrieval). Attacks use TextAttack (Morris et al., 2020); the contextual reference uses distilgpt2 (Radford et al., 2019). Version control is on GitHub. The monitor (A9) uses the same protocol, each condition starting with an empty memory."),
  p("Evaluation protocol. Every benchmark question runs three times per condition, paired by schedule index with alternating condition order. Each run writes create-only, checksummed records of prompts, retrieved passages, answers and judge scores, so every reported number can be regenerated offline. Detector thresholds are fixed on development documents at a 10% false-positive rate before held-out evaluation. A first-order adaptive attacker may only make substitutions the word-frequency reference does not penalise; a second-order attacker must also keep each passage as probable under the language model; both use the same surrogate classifier as an unrestricted control run, so the restriction is the only difference."),
  table([600, 3100, 3026, 1100, 1200], [
    ["ID", "Activity", "Output", "Start", "End"],
    ["A1", "Literature review, threat model", "Context notes, protocol", "1 Oct 26", "8 Nov 26"],
    ["A2", "RAG pipeline, interface, three corpora", "Software, corpora, manifest", "1 Oct 26", "31 Oct 26"],
    ["A3", "Benchmark build, review, freeze", "Benchmark v1", "15 Oct 26", "8 Nov 26"],
    ["A4", "Pilot, first paired evaluation", "Run records, analysis", "1 Nov 26", "22 Nov 26"],
    ["A5", "Relative-entropy detectors (offline)", "Detector results", "9 Nov 26", "20 Dec 26"],
    ["A6", "Live defences, judge check", "Defence runs, agreement", "1 Dec 26", "31 Jan 27"],
    ["A7", "Adaptive attackers, TextFooler", "Attack corpora, results", "4 Jan 27", "14 Feb 27"],
    ["A8", "Evidence check, held-out, uncertainty", "Final analyses", "1 Feb 27", "7 Mar 27"],
    ["A9", "Runtime verification monitor", "Monitor, tests, live runs", "18 Jan 27", "7 Mar 27"],
    ["A10", "Report, demo video, paper", "Final submission", "1 Feb 27", "4 Apr 27"],
  ]),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync("gantt.png"), transformation: { width: 600, height: 325 } })] }),
  p([i("Figure 1. Work plan. Milestones: PDD and ethics form, 11 Nov 2026; final submission, 4 Apr 2027; project review, 1–11 Jun 2027.")], { alignment: AlignmentType.CENTER }),
  p("Project outputs: (1) the AegisRAG software with its defences and runtime monitor; (2) the benchmark, corpora and attack manifests; (3) an evaluation report with checksummed run records; (4) a research paper manuscript."),

  h1("5 Risks to the project"),
  table([2300, 3300, 3426], [
    ["Risk", "Prevention", "Fallback if it happens"],
    ["Scope too large for 450 hours", "Fixed core (O1–O6); O7–O9 scheduled after", "Drop O8, limit O9 to verify mode, then reduce O7 to one attacker"],
    ["Attack does not transfer to RAG answers", "Pilot before main runs; report attack success separately", "Report as a negative finding; detection results remain valid"],
    ["API cost or outages", "Pilot measures calls; spending cap; timeouts", "Detectors run offline; resume interrupted runs"],
    ["Data loss or contaminated results", "Create-only records, checksums, GitHub backups", "Re-run from frozen benchmark and corpora"],
    ["Invalid conclusions", "Frozen protocol, held-out split, control corpus", "Report limitations; avoid claims beyond evidence"],
    ["Licence of data or models unclear", "Check MITRE terms and model licences in A1", "Replace the affected source"],
    ["Attack libraries fail with current dependencies", "Separate pinned environment for attacks", "Use the recorded attack corpora already produced"],
    ["Trusted reference misses some content (OWASP, NIST)", "Measure coverage; record withheld answers", "Limit monitor claims to MITRE-covered questions"],
  ]),

  h1("6 Legal, social, ethical and professional issues"),
  p([b("Category. "), "This is a category 1 project: AegisRAG is a research prototype for evaluation, not for distribution or operational use."]),
  p([b("Legal. "), "MITRE ATT&CK and CAPEC content is used under MITRE's terms of use with attribution (MITRE, 2026a; 2026b); software and model licences will be recorded. Questions and passages are sent to the OpenAI API; they contain no personal data. API keys are kept out of the repository."]),
  p([b("Social and ethical. "), "If deployed, the assistant could give wrong security advice, and a detector could miss poisoned text or wrongly flag clean text; users might over-trust a fluent answer. The interface will label AegisRAG as a prototype, show retrieved evidence and detector explanations, and never present a score as proof that a source is clean. The monitor's memory could wrongly quarantine clean passages, so it is shown in the interface and reset by archiving, never deleting. The attack code reproduces published methods on a local copy of public documents and attacks no live system. There are no human participants, so research-ethics risk is low."]),
  p([b("Dual use. "), "Publishing how the detector works also tells attackers what to avoid. The project therefore evaluates attackers who know the detector and reports where it fails, so that the published defence is not over-trusted; no new attack technique beyond the published ones is released."]),
  p([b("Professional. "), "Following the BCS Code of Conduct, results will be reported as measured, including negative findings, and all reused code, data and tools will be acknowledged."]),
];

const references = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("References"),
  ref("Bartocci, E., Falcone, Y., Francalanza, A. and Reger, G. (2018) 'Introduction to runtime verification', in Bartocci, E. and Falcone, Y. (eds.) Lectures on Runtime Verification. Lecture Notes in Computer Science, 10457. Cham: Springer, pp. 1–33."),
  ref("Es, S., James, J., Espinosa Anke, L. and Schockaert, S. (2024) 'RAGAs: automated evaluation of retrieval augmented generation', in Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations. St. Julians: ACL, pp. 150–158."),
  ref("Ikbarieh, S., Aryal, K. and Gupta, M. (2025) 'RAG-targeted adversarial attack on LLM-based threat detection and mitigation framework', arXiv preprint, arXiv:2511.06212."),
  ref("Jin, D., Jin, Z., Zhou, J.T. and Szolovits, P. (2020) 'Is BERT really robust? A strong baseline for natural language attack on text classification and entailment', in Proceedings of the AAAI Conference on Artificial Intelligence, 34(5), pp. 8018–8025."),
  ref("Jain, N. et al. (2023) 'Baseline defenses for adversarial attacks against aligned language models', arXiv preprint, arXiv:2309.00614."),
  ref("Kullback, S. and Leibler, R.A. (1951) 'On information and sufficiency', The Annals of Mathematical Statistics, 22(1), pp. 79–86."),
  ref("Leucker, M. and Schallhart, C. (2009) 'A brief account of runtime verification', The Journal of Logic and Algebraic Programming, 78(5), pp. 293–303."),
  ref("Lewis, P. et al. (2020) 'Retrieval-augmented generation for knowledge-intensive NLP tasks', in Advances in Neural Information Processing Systems 33, pp. 9459–9474."),
  ref("MITRE (2026a) MITRE ATT&CK. Available at: https://attack.mitre.org/ (Accessed: 19 October 2026)."),
  ref("MITRE (2026b) CAPEC: Common Attack Pattern Enumeration and Classification. Available at: https://capec.mitre.org/ (Accessed: 19 October 2026)."),
  ref("Morris, J., Lifland, E., Yoo, J.Y., Grigsby, J., Jin, D. and Qi, Y. (2020) 'TextAttack: a framework for adversarial attacks, data augmentation, and adversarial training in NLP', in Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations. Online: ACL, pp. 119–126."),
  ref("Mozes, M., Stenetorp, P., Kleinberg, B. and Griffin, L. (2021) 'Frequency-guided word substitutions for detecting textual adversarial examples', in Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics. Online: ACL, pp. 171–186."),
  ref("Pnueli, A. (1977) 'The temporal logic of programs', in 18th Annual Symposium on Foundations of Computer Science. Providence: IEEE, pp. 46–57."),
  ref("Radford, A., Wu, J., Child, R., Luan, D., Amodei, D. and Sutskever, I. (2019) Language models are unsupervised multitask learners. San Francisco: OpenAI."),
  ref("Ren, S., Deng, Y., He, K. and Che, W. (2019) 'Generating natural language adversarial examples through probability weighted word saliency', in Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics. Florence: ACL, pp. 1085–1097."),
  ref("Xiang, C., Wu, T., Zhong, Z., Wagner, D., Chen, D. and Mittal, P. (2024) 'Certifiably robust RAG against retrieval corruption', arXiv preprint, arXiv:2405.15556."),
  ref("Zheng, L. et al. (2023) 'Judging LLM-as-a-judge with MT-Bench and Chatbot Arena', in Advances in Neural Information Processing Systems 36, Datasets and Benchmarks Track."),
  ref("Zhong, Z., Huang, Z., Wettig, A. and Chen, D. (2023) 'Poisoning retrieval corpora by injecting adversarial passages', in Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing. Singapore: ACL, pp. 13764–13775."),
  ref("Zou, W., Geng, R., Wang, B. and Jia, J. (2025) 'PoisonedRAG: knowledge corruption attacks to retrieval-augmented generation of large language models', in Proceedings of the 34th USENIX Security Symposium. Seattle: USENIX Association."),
];

const appendix = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("Appendix A: Use of AI"),
  p([b("Tools used: "), "Claude (Anthropic), through Claude Code, 11–19 October 2026. ChatGPT (Open-AI),"]),
  p([b("1. Project idea and research direction. "), "The project topic was my own. The relative-entropy approach to detecting poisoned text was suggested by Dr Nikos Komninos. I used AI to brainstorm and discuss options. Firs I’ve asked to give me the whole idea and the way of implementing it, and then I asked to considering my attacks tell me whether it’s a realistic implementation or not. And AI came back with the idea that it fits the project very well because of the nature of the attacks which they change some words into mostly odd synonyms."]),
  p([b("2. Drafting the PDD text (16–18 October). "), "I asked Claude to check the written PDD File and correct the grammar and dictation and also compress it into the Handbooks policy since my Original PDD file was around 2100 words. Claude produced complete drafts, generated by a script in the repository (docs/pdd/build_pdd.js). Then I reviewed and made sure that with the compressed word limit still the whole plan and results remain clear."]),
  p([b("3. Restructuring to the handbook (19 October). "), "I gave Claude the Project Handbook and asked it to make the PDD comply with §4.5. It converted the references to Harvard style."]),
  p([b("4. Work plan chart. "), "Claude generated the Gantt chart (Figure 1) with a Python script, from activities and dates I approved and the results that I have achieved and shared."]),
  p([b("5. References. "), "Claude formatted the reference list in Harvard style. I gave all the references and papers that I’ve read and used and checked that each source exists."]),
  p([b("6. Adding the runtime monitor (1 November). "), "After Dr Hafizul Asad suggested a runtime verification monitor, I asked Claude to update the PDD to include it. Claude drafted the new problem sentences, RQ5, H5, O9, activity A9, the new risk, the ethics sentence and the three new references, and regenerated the Gantt chart. [Student to check and complete.]"]),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: SZ } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "1F3A5F" }, paragraph: { spacing: { before: 260, after: 120 }, outlineLevel: 0 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1418, right: 1418, bottom: 1418, left: 1418 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "666666" })] })] }) },
    children: [...cover, ...body, ...references, ...appendix],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("AegisRAG-Project-Definition-Document.docx", buf);
  console.log("written");
});
