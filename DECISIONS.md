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