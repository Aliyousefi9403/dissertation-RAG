# AegisRAG

**Detecting and containing word-substitution poisoning of a cybersecurity question-answering system.**

Ali Yousefi, with Nikos Komninos and Hafizul Asad
Department of Computer Science, City St George's, University of London

Paper: *Reading the Poison: Detecting Word-Substitution Poisoning of a Cybersecurity RAG Knowledge Base
with Relative Entropy and Runtime Verification* ([PDF](docs/paper/arxiv/AegisRAG-paper.pdf)).

---

## In plain language

AI assistants are increasingly used for security work: explaining how an attack works, what it needs and
how to stop it. To keep them accurate, most are built to answer from a library of trusted documents
rather than from memory. They look up the passages that match the question and answer from those.

That makes the library a target. This project studies an attacker who does not add fake documents but
quietly edits real ones, swapping words for near-synonyms ("implants malicious software" becomes
"engraft malicious package"). The document keeps its source, its place and its topic, so nothing looks
new or out of place.

The project asks three questions and answers each with measured evidence:

1. **How much damage does this do?** The system answers correctly less often. Mostly it does not repeat the
   poisoned wording as fact; it loses the evidence it needed and says "I don't know".
2. **Can the edited passages be found?** Yes, for this kind of edit. A swapped-in word is usually much
   less likely, in its sentence, than the ordinary word it replaced. Measuring that gap with a small
   language model finds most edited passages and ignores harmless formatting changes.
3. **What should the system do once it has found them?** Simply removing suspicious passages makes the
   system safer but does not bring the answers back, because the edited passage usually held the answer.
   So the project adds a **runtime monitor**: before an answer is released it is checked against an
   official source the attacker cannot edit (MITRE's published data), passages that cause a violation are
   remembered and never used again, and the monitor can bring in the official entry when the library has
   been damaged.

Every experiment is recorded so that the numbers in the paper can be checked against the files that
produced them.

## In technical terms

**System.** A retrieval-augmented generation (RAG) pipeline over a knowledge base built from MITRE ATT&CK
and CAPEC STIX data (18 documents, 200 passages, 14 attack types): FastAPI backend, Qdrant vector store,
`all-MiniLM-L6-v2` embeddings, top-3 retrieval over 500/100-character chunks, `gpt-4o-mini` at
temperature 0. A Next.js interface compares clean, poisoned and defended answers side by side.

**Threat model.** The attacker can edit existing passages but not add documents or change the model. Edits
are produced with PWWS and TextFooler against a DistilBERT surrogate that classifies passages by attack
type; edits are accepted when the surrogate's decision flips. A layout-only control corpus separates the
effect of the words from the effect of the edit.

**Benchmark and statistics.** 44 reviewed questions (35 development, 9 held out by document), each with
reference facts and the exact source section; every question run three times per condition in paired
schedules. Correctness is scored by an LLM judge checked against 75 blind manual grades (quadratic
weighted κ = 0.82). Uncertainty: question-level cluster bootstrap (B = 10,000) and Wilcoxon signed-rank
tests.

**Detection (relative entropy).** The whole-passage divergence KL(p‖q) between a passage's word
distribution and normal text is a weak signal. One term of it, the log-ratio between a word and its most
probable synonym (the *synonym gap*), is strong, especially when the probabilities come from a language
model reading the passage in context (`distilgpt2`). Thresholds are fixed on development data before
held-out data is scored.

**Defences.** (1) Retrieval filters that drop passages above the threshold (word-frequency and contextual
versions). (2) An evidence check that compares answers with retrieved sources. (3) A runtime-verification
monitor with three properties:
- φ1: an answer must not contain a rare word copied from the retrieved passages that is absent from the
  trusted MITRE vocabulary and from the question;
- φ2: an answer must not be a refusal when the trusted data covers the attack asked about;
- φ3 (LTL): G(quarantined(p) → G ¬inContext(p)), a passage once quarantined never reaches the model again.

The trusted files are pinned by SHA-256 and the monitor refuses to start if they change. On a violation
the monitor blames passages, adds them to an append-only quarantine memory, and regenerates (at most two
retries). In *restore* mode it may add the official MITRE entry as a trusted source.

**Adaptive attackers.** A frequency-constrained PWWS attacker, and second-order attackers that must keep
each passage as probable under the language model, at budgets of 0, 4.46, 20, 100 and 300 bits.

## Main results (version described in the paper)

| Finding | Result |
|---|---|
| Poisoning, judged correctness | 0.714 → 0.555; refusals 26 → 45 of 132; wrong answers 0 → 2 |
| Contextual synonym gap, AUROC | PWWS 0.95, retrained-surrogate PWWS 0.97, TextFooler 0.91, layout-only control 0.53 |
| Same detector on the held-out documents | 0.88 (word-frequency version 0.94) |
| Constrained attackers | strict second-order attacker: 0 of 57 sections succeed; at 100 bits 5 succeed and 3 of 6 edited passages are still flagged |
| Filtering | halves exposure to edited text, but correctness does not recover |
| Monitor, verify mode (PWWS) | exposure 0.41 → 0.26 (p = 0.016), no wrong answers, correctness not restored |
| Monitor, verify mode (TextFooler) | exposure 0.82 → 0.58 (p = 0.001) |
| Monitor, restore mode | correctness 0.555 → 0.786 (p = 0.0001), refusals 45 → 7 |
| Monitor on clean data | correctness 0.708 vs 0.714, nothing quarantined |
| φ3 checked over the full trace of the monitor run | 0 violations |

Costs and failure cases are reported in the paper with every gain, including the monitor's imprecise
blame step (on PWWS, 10 of the 18 quarantined passages were edited).

## Versions in this repository

| Branch | What it is |
|---|---|
| `main`, `dissertation-v1.0` | **The version described in the paper and the dissertation.** All numbers above come from this version. |
| `tdsc` | Later work towards a journal version (larger knowledge base, more attacks, more models). It is in progress; its results are not part of the paper above. |

## Repository map

| Area | Location |
|---|---|
| RAG pipeline (ingestion, retrieval, generation, API) | `backend/app/` |
| Attacks: PWWS, TextFooler, adaptive and second-order attackers, surrogate training | `backend/app/attack/` |
| Defences: entropy and contextual filters, evidence check, runtime monitor | `backend/app/defence/` |
| Knowledge-base builder and source mapping | `backend/app/kb_builder/` |
| Metrics: Hit@3/MRR, edited-text exposure, LLM-judge correctness and faithfulness | `backend/app/evaluation/` |
| Corpora: clean, poisoned, control, TextFooler, adaptive | `backend/data/` |
| Benchmarks and their review records | `backend/data/evaluation/`, `docs/research/benchmark-review/` |
| Recorded runs (create-only, checksummed) | `pilot-runs/` |
| Analysis and experiment scripts | `docs/research/scripts/` |
| Results, methods write-up, evidence index | `docs/research/` |
| Paper (LaTeX and PDF) | `docs/paper/arxiv/` |
| Interface (Next.js) | `frontend-next/` |

## Setup

Requirements: Python 3.12, Node 20+, a running Qdrant (`http://localhost:6333`) and an OpenAI API key.

```bash
uv venv -p 3.12 .venv && . .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env            # set LLM_API_KEY; never commit .env

cd backend                      # index the knowledge bases (each collection is recreated)
python -m app.ingestion.load_documents --system-state clean
python -m app.ingestion.load_documents --system-state poisoned
```

On macOS, `./start-aegisrag.sh` sets up the environment, starts Qdrant in Docker and runs both servers.

## Run the application

```bash
cd backend && uvicorn app.main:app --port 8000
cd frontend-next && npm ci && npm run dev        # http://localhost:3000
```

## Tests

```bash
PYTHONPATH=backend pytest backend/tests -q          # offline, no model calls
cd frontend-next && npx tsc --noEmit && npx eslint .
npx playwright test                                # interface tests, mocked backend; needs `npm run dev`
```

## Reproduce and verify

```bash
python docs/research/scripts/verify_evidence.py     # re-hashes every run record and checks the reported numbers
```

The methods and results write-up (`docs/research/evaluation-methods-and-results.md`) gives the command for
every run, analysis and figure. Live runs need an API key; all analyses of saved runs are offline.

## Research integrity

- Corpora, benchmarks, attack manifests and run records are never edited in place; new versions are new
  files with hashes.
- Failed or missing model results stay in the record as unavailable, never as zero.
- Thresholds are fixed on development data before held-out data is scored, and negative results are
  reported.
- AI tools were used to help with coding, analysis and drafting; all code, numbers and references were
  checked by the author.

## Licence

Copyright (c) 2026 Ali Yousefi. All rights reserved. The repository is public so that the research can be
inspected and checked; it is not open source. See [LICENSE](LICENSE) for what is permitted, and
[NOTICE](NOTICE) for third-party material (MITRE ATT&CK and CAPEC data remain under MITRE's terms).
