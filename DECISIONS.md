# AegisRAG — Architecture and Research Decisions

This document records the main technical and methodological decisions made during the development of AegisRAG.

The purpose of this file is to preserve the reasoning behind important design choices and make the project easier to reproduce, review, and modify during attack reproduction, defence development, evaluation, and deployment.

---

## ADR-001: Use Qdrant as the Vector Database

### Decision

AegisRAG uses Qdrant as its vector database instead of Chroma or a standalone FAISS index.

### Rationale

The project requires more than basic semantic similarity search. During the poisoning and defence experiments, documents and chunks need to carry structured metadata such as:

- `attack_type`
- `origin`
- `source_authority`
- `experiment_id`
- `poisoning_method`
- `poisoning_status`
- `trust_score`
- `document_version`

Qdrant supports persistent vector storage and metadata-based payload filtering. This allows the retrieval pipeline to distinguish between clean and poisoned documents and to isolate specific experimental conditions.

For example, future searches may filter documents using:

```text
origin = "clean"
origin = "poisoned"
```
This is important because the dissertation will compare retrieval and generation behaviour before and after knowledge-base poisoning.
### Alternatives Considered
### Chroma
Chroma is convenient for prototypes and simple local applications. However, Qdrant provides stronger collection management, payload filtering, persistence, and inspection tools for controlled experiments.
### FAISS
FAISS is an efficient vector-search library, but it is not a complete vector database. Metadata filtering, persistence, document management, and collection separation would require additional custom code.
### Consequences
### Benefits:
Persistent vector collections
Metadata filtering
Support for clean and poisoned document tags
Collection inspection through the Qdrant dashboard
Suitable for research experiments and possible future deployment
### Trade-offs:
Qdrant must be running locally or remotely
Collection state must be managed carefully
Re-indexing must be controlled to avoid contaminating experiments
## ADR-002: Use all-MiniLM-L6-v2 for Initial Embeddings
### Decision
AegisRAG initially uses:
sentence-transformers/all-MiniLM-L6-v2
as its embedding model.
### Rationale
The model is lightweight, widely supported, and practical for local development. It offers a reasonable balance between semantic retrieval quality, speed, memory use, and reproducibility.
It was selected because it aligns with the intended reproduction setup based on the Ikbarieh et al. 2025 paper. The exact model and configuration used in the paper must still be verified before the dissertation claims exact methodological replication.
The model is also appropriate for early development because the knowledge base will be re-indexed repeatedly while ingestion, poisoning, metadata, and evaluation components are being built.
### Alternatives Considered
Larger embedding models may improve retrieval quality but increase:
indexing time
memory usage
hardware requirements
experiment runtime
model download size
API-based embedding models were not selected for the baseline because they introduce external cost and reduce local reproducibility.
### Consequences
### Benefits:
Fast local indexing
Low hardware requirements
No embedding API cost
Easy integration with Sentence Transformers and LangChain
Reproducible local experiments
Limitations:
It may confuse related cybersecurity concepts
Retrieval quality may be lower than newer or larger models
A reranker or alternative embedding model may later be evaluated
The embedding model remains configurable so it can be replaced without redesigning the pipeline.
## ADR-003: Use gpt-4o-mini as the Initial Language Model
### Decision
AegisRAG initially uses:
gpt-4o-mini
for answer generation.
### Rationale
The first objective is to validate the complete RAG pipeline while keeping development and experimentation costs manageable.
gpt-4o-mini provides a practical balance between:
answer quality
latency
API cost
instruction following
### availability
The project will require repeated model calls while testing retrieval, prompts, clean and poisoned knowledge bases, and evaluation queries. Using a lower-cost model makes this development cycle more practical.
The model is created through:
backend/app/generation/llm_factory.py
This factory abstraction allows the language model to be changed later without rewriting the retrieval and generation pipeline.
Possible future replacements include:
a larger OpenAI model
a local Hugging Face model
an Ollama-hosted model
another API-based model
### Alternatives Considered
A larger model may produce stronger answers, but it would increase cost and could make it harder to determine whether improvements came from the defence or simply from a stronger generator.
A fully local model may improve offline reproducibility, but it may require more hardware and deployment work.
### Consequences
### Benefits:
Lower experimentation cost
Fast responses
Adequate quality for baseline development
Easy model replacement through llm_factory.py
Limitations:
Results may not generalise to every language model
Different models may respond differently to poisoned context
Final evaluation may need to test more than one model
## ADR-004: Use FastAPI and Next.js
### Decision
AegisRAG uses:
FastAPI for the backend API
Next.js, React, and TypeScript for the frontend
### Rationale
The frontend and backend are separated to keep the research pipeline independent from the user interface.
FastAPI is responsible for:
request validation
### document retrieval
RAG execution
answer generation
source metadata
future attack endpoints
future defence endpoints
future evaluation endpoints
Next.js is responsible for:
the chat interface
evidence-chain presentation
dashboard pages
knowledge-base views
attack-lab views
defence-engine views
evaluation views
future deployment and authentication features
This separation allows the backend to be tested independently through Swagger, scripts, automated experiments, or other clients.
It also prevents research logic from becoming tightly coupled to a temporary interface implementation.
### Alternatives Considered
Streamlit
Streamlit was useful for quickly validating the first working interface. However, it offers less control over routing, state management, advanced interaction, visual design, and future commercial deployment.
Single-framework application
Keeping all logic in one framework would reduce the number of services initially, but it would mix machine-learning research code with frontend concerns.
### Consequences
### Benefits:
Clear separation of concerns
Independent backend testing
Production-style architecture
Better frontend control
Easier future deployment
Easier replacement of either frontend or backend
Trade-offs:
Two development servers must run locally
CORS must be configured
Deployment is more complex than a single application
## ADR-005: Start with Chunk Size 500 and Overlap 100
### Decision
The initial chunking configuration is:
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
### Rationale
A chunk size of 500 characters is used as an initial baseline. It is intended to preserve enough technical context while keeping retrieved chunks focused.
An overlap of 100 characters reduces the chance that an important sentence, attack mechanism, mitigation step, or heading is separated from its surrounding context at a chunk boundary.
This configuration is a starting point and not a final optimisation.
Chunking may affect:
retrieval accuracy
poisoning effectiveness
retrieval scores
evidence duplication
answer completeness
defence signals
For this reason, chunk size and overlap remain configurable and may later be tested experimentally.
### Alternatives Considered
Smaller chunks may improve precision but lose context and create fragmentation.
Larger chunks may preserve more context but include unrelated material and reduce retrieval specificity.
### Consequences
### Benefits:
Simple initial configuration
Reasonable balance between context and precision
Reduced information loss at chunk boundaries
### Limitations:
Not yet empirically tuned
Character-based splitting may divide semantic sections poorly
Overlap can produce duplicated evidence
A later evaluation may compare different chunking configurations.
## ADR-006: Use a Markdown-Based Knowledge Base
### Decision
The controlled research knowledge base is stored as Markdown files rather than PDFs.
### Rationale
Markdown is better suited to reproducible poisoning experiments because it is:
plain text
easy to inspect
easy to chunk
easy to modify
easy to generate programmatically
easy to compare with Git
easy to tag with metadata
free from PDF parsing noise
The research requires deliberate modifications to knowledge-base content. Git diffs can show exactly which words or passages changed between clean and poisoned documents.
This makes it easier to preserve:
the original clean document
the poisoned version
the exact textual perturbation
document metadata
experimental versions
PDF files would introduce additional variables such as:
extraction errors
broken reading order
page headers and footers
tables
images
OCR differences
inconsistent whitespace
These issues could make it difficult to determine whether a retrieval change was caused by poisoning or document extraction.
Alternatives Considered
PDFs
PDFs may better resemble real organisational documents, but they reduce control and add parsing complexity.
HTML
HTML preserves structure but often contains navigation, scripts, styles, and unrelated page elements that must be cleaned.
Database records
Database records provide structure but are less transparent for manual inspection and Git-based comparison.
### Consequences
### Benefits:
Highly controllable corpus
Reproducible clean and poisoned versions
Clear Git history
Straightforward chunking
Easy metadata extraction
Suitable for controlled experimental manipulation
Limitations:
Less representative of some real enterprise document collections
Source material must be carefully adapted and cited
Formatting conventions must remain consistent
Other formats may be tested later to evaluate whether the defence generalises beyond Markdown.
## ADR-007: Keep Core Components Configurable
### Decision
Model names, database locations, collection names, retrieval depth, chunking settings, and credentials are managed through configuration instead of being hard-coded throughout the application.
### Rationale
The dissertation requires controlled comparisons between different experimental conditions.
Configuration-driven components allow changes to:
embedding models
language models
retrieval depth
Qdrant collections
clean and poisoned corpora
chunk size
overlap
experimental mode
without rewriting the core application.
This supports reproducibility and reduces the risk of introducing unrelated code changes between experiments.
### Consequences
### Benefits:
Easier experimentation
Cleaner code
Better reproducibility
Lower coupling
Simpler deployment configuration
Trade-offs:
Configuration must be documented
Invalid settings must be handled
Experiment configurations must be preserved with results
Current Status
These decisions describe the current clean-baseline architecture.
They may be revised after:
verification of the Ikbarieh et al. methodology
reconstruction of the authoritative knowledge base
baseline retrieval evaluation
TextFooler attack reproduction
defence-engine implementation
ablation studies
deployment testing
Substantial changes should be documented as new decisions or explicit revisions rather than silently replacing the original rationale.
## ADR-008: Relative-entropy defences, adaptive attackers and resumable runs (16–19 Oct 2026)

### Decisions
- **Detector.** Detect substituted words with the *synonym gap*, the per-word log-ratio log₂ q(synonym) − log₂ q(word), rather than whole-passage KL or Jensen–Shannon divergence, which dilute a few changed words (results §11, §16).
- **Reference.** Offer two deployed references as separate system states: a word-frequency reference (`defended`, `entropy-filter-v1`, threshold 7.2262 bits) and a language-model reference, distilgpt2 (`contextual`, `contextual-filter-v1`, threshold 4.4611 bits). Both thresholds were fixed once on development documents at a 10% false-positive rate and never re-tuned. Clean and poisoned states are unchanged.
- **Drop, not repair.** Dropping flagged passages is kept as the policy; WordNet repair (`repaired`, `entropy-repair-v1`) is retained only as an evaluated alternative, because it restored too few substitutions (§13, §15).
- **Adaptive evaluation.** Every detector is evaluated against a formatting-only control, a matched unrestricted rerun, a first-order (frequency-matched) attacker, second-order attackers with language-model budgets 0, 4.46, 20, 100 and 300 bits, and a second attack (TextFooler), all with the same retrained surrogate (§16, §18).
- **Resumable, create-only runs.** Attack generation checkpoints each file and can resume, with several workers sharing a corpus through boot-aware locks; live runs resume in place only when the run's code hashes match, or after a recorded equivalence check (§17). No record is ever rewritten.

### Consequences
- The contextual state costs about 1.3 s more per answer (language-model scoring, cached per passage) and needs `torch` and `transformers` in the backend environment.
- Filtering reduces exposure to poisoned text and removes confidently wrong answers, but does not restore correctness on poisoned data; that requires restoring the original text and is future work.
- All headline numbers are checked by `docs/research/scripts/verify_evidence.py` (73 claims) against saved files.

## ADR-009: Runtime verification monitor with feedback and memory (approved 27 Oct 2026)

**Origin.** Suggested by the project supervisor, Dr Hafizul Asad: detect bad answers at runtime against a formal specification, feed the failure back to the model, and remember it so the same attack does not succeed twice. Approved by the author on 27 Oct 2026.

1. **Confirmed problem.** The passage filters (ADR-008) make a poisoned knowledge base safe to read but do not restore correctness, and nothing is learned between questions: the same poisoned passage misleads the system every time it is retrieved. Confidently wrong answers repeat a substituted phrase ("Engraft Malicious Package") that appears nowhere in the official MITRE data.
2. **Why a backend change is necessary.** The monitor must run inside the answer path (check, diagnose, regenerate, quarantine), which needs new defence code; it cannot be done in the interface or offline.
3. **Files.** New: `backend/app/defence/runtime_monitor.py`, `backend/tests/test_runtime_monitor.py`, `docs/research/scripts/run_monitor_eval.py`, `docs/research/scripts/analyse_monitor.py`. Edited: this file, the results write-up and the evidence index. No existing module is modified.
4. **Unchanged behaviour.** `/chat`, `/compare`, `/guarded-chat` and all existing modes; the base prompt, model, temperature, embeddings, chunking and top-k. The monitor's first generation uses the unchanged pipeline prompt; only regeneration rounds add the monitor's feedback.
5. **API contract.** No change: the monitor is a research mode run by the evaluation script (`ChatRequest` is unchanged). Exposing it in the interface would be a separate, later decision.
6. **Research validity.** The trusted reference is the official MITRE STIX data (`backend/data/external/`, SHA-256 pinned in the module), separate from the knowledge base the attacker edits; the threat model assumes the attacker cannot alter it. Specifications are fixed before any live run; the rare-word cut-off (Zipf 3.5) is fixed from a dry check on clean answers only. Two modes are reported separately: *verify* (the trusted data is used only to check) and *restore* (it may also be added as a source when a refusal cannot otherwise be fixed), the latter as an upper bound. Memory effects are measured across the three scheduled repetitions; the clean condition measures false quarantines.
7. **Security.** Fails closed if the trusted files are missing or their hashes differ; the memory is an append-only file inside the run folder; retrieved text and monitor feedback are data, never commands. A memory that quarantines passages can be abused to suppress clean passages (denial of service); this is measured on the clean corpus.
8. **Tests.** Base forms; the lexical and availability specifications; diagnosis; append-only memory with reload; the full loop with stub retrieval and model (violation → quarantine → regenerate → release; repeat question skips the quarantined passage with no violation; restore adds the trusted source; unresolved lexical violation withholds the answer; round 0 prompt equals the pipeline prompt); hash mismatch fails closed.
9. **Rollback.** Delete the four new files; no existing behaviour depends on them. Run records are create-only and stay as evidence.

**Baseline before the change.** Branch `feature/aegisrag-evidence-check`; backend tests 285 passed, 1 skipped.

**Outcome (27 Oct 2026).** Implemented as planned; backend tests 297 passed, 1 skipped (12 new). Only the planned files changed; no data, corpus or vector collection was modified. Offline dry check passed (no clean answer flagged by φ1). Live run `20261027T225951Z-monitor-7435694678804a8fb151bed0f2cb853d`: verify mode reduces edited-text exposure (0.409 → 0.280) without restoring correctness; restore mode lifts correctness to 0.773 and cuts refusals from 45 to 7; φ3 holds on every trace; nothing is quarantined on clean data; specification coverage (MITRE STIX lacks the knowledge base's OWASP/NIST text) causes 7 false withholds. Results: evaluation write-up §23.

## ADR-010: "Verified" mode in the interface, distinct defence views, and a public deployment (approved 28 Oct 2026)

Approved by the author on 28 Oct 2026 ("I approve version A … the UI plan and everything").

1. **Problem.** The runtime monitor (ADR-009) is only reachable from the evaluation script; the three existing defences share one shield visual, so the interface does not show how each works; the system only runs on a developer machine.
2. **Why backend changes are needed.** `/chat` must accept the new state and return the monitor trace; the interface needs the quarantine memory; deployment needs the vector-store address from the environment and, when public, access control and rate limiting.
3. **Files.** Backend: `app/main.py` (accept `verified`, optional `trusted_fallback`, optional `monitor` in the response), new `app/defence/monitor_router.py` (`GET /monitor/memory`, `POST /monitor/memory/reset`), `app/config.py` (`QDRANT_URL` from the environment, same default), new `app/access.py` (optional password and rate limit, off unless `AEGIS_ACCESS_PASSWORD` is set), tests. Frontend: mode selector, types, API client, one view per defence. Deployment: `Dockerfile`, `docker-compose.yml`, `deploy/` notes. Research code and data are untouched.
4. **Unchanged behaviour.** Every existing state answers exactly as before; `ChatResponse` only gains an optional field that is null outside Verified mode; with no new environment variables set, the backend behaves as today (no password, no rate limit, Qdrant on localhost).
5. **API contract.** Additive only: a new `system_state` value `verified`, an optional request field `trusted_fallback` (default false), an optional response field `monitor`, and two new endpoints. No field is removed or renamed.
6. **Research validity.** No research parameter changes. The interface's Verified mode uses `runtime-monitor-v1` unchanged on the PWWS-poisoned collection; its live memory file is separate from the evaluation run's memories (`backend/runtime/`, not committed), so demo use cannot alter recorded evidence.
7. **Security.** The public deployment must set a password, a per-client rate limit and an OpenAI spending cap; the API key is a platform secret, never in the repository or image. Reset archives the memory file instead of deleting it (append-only audit). Monitor feedback and retrieved text remain data, not commands.
8. **Tests.** `/chat` with `verified` returns a monitor trace (stubbed model and retrieval); existing states unchanged; memory endpoints list and archive; access control: no password set means open, wrong or missing password is refused, rate limit returns 429; frontend type check, lint and end-to-end tests.
9. **Rollback.** Revert the commits; delete `backend/runtime/`; recorded evidence is unaffected.

**ADR-009 addendum (28 Oct 2026): runtime-monitor-v2.** Testing Verified mode in the interface showed φ1 withholding an answer for a word the model chose itself ("emphasizing"), the same false-withhold weakness reported in §23. v2 flags a rare word outside the trusted vocabulary only if it also occurs in the retrieved context, i.e. the model copied it from possibly tampered evidence. `check(..., context=None)` reproduces v1 exactly; the v1 evaluation (§23) used commit `39498ac` and stays as recorded. v2 is to be evaluated live before any claim is made about it.
