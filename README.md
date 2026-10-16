# AegisRAG

AegisRAG is a research platform for measuring how **knowledge-base poisoning** affects a cybersecurity
Retrieval-Augmented Generation (RAG) system, and how far simple **reliability indicators** can flag answers
that need checking. It is an IN3007 individual project (City St George's, University of London, 2026–27).

It is a measurement framework, not a new defence. "Supported by the sources" never means "true", and a
poisoned source can support a false answer.

## What is in the repository

| Area | Location |
|---|---|
| RAG pipeline (FastAPI, Qdrant, MiniLM embeddings, gpt-4o-mini) | `backend/app/` |
| PWWS poisoning (DistilBERT surrogate, TextAttack) | `backend/app/attack/` |
| Clean, PWWS-poisoned and formatting-only control knowledge bases | `backend/data/{raw,poisoned,control}/knowledge_base/` |
| Metrics: Hit@3/MRR, poison and edited-text exposure, document overlap, LLM-judge correctness and faithfulness, paired accounting, attack success | `backend/app/evaluation/` |
| Experimental evidence check (`POST /guarded-chat`, policy v2) | `backend/app/defence/` (see its README) |
| Benchmarks: 12-question pilot set; frozen 44-question v1 (dev/held-out) | `backend/data/evaluation/` |
| Recorded runs (create-only, checksummed) | `pilot-runs/` |
| Comparison interface (Next.js) | `frontend-next/` |
| Methods, metrics, results, PDD | `docs/research/`, `docs/pdd/` |

## Setup

Requirements: Python 3.12, Node 20+, a running Qdrant (`http://localhost:6333`), and an OpenAI key.

```bash
uv venv -p 3.12 .venv && . .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env            # set LLM_API_KEY; never commit .env

# index the knowledge bases (each collection is recreated)
cd backend
python -m app.ingestion.load_documents --system-state clean
python -m app.ingestion.load_documents --system-state poisoned
```

## Run the application

```bash
cd backend && uvicorn app.main:app --port 8000
cd frontend-next && npm ci && npm run dev        # http://localhost:3000
```

Use the mode selector for Clean, PWWS Poisoned or Compare. Turn on **Evidence check** to send questions through
`/guarded-chat`.

## Tests

```bash
PYTHONPATH=backend pytest backend/tests -q          # offline, no model calls
cd frontend-next && npx tsc --noEmit && npx eslint .
npx playwright test e2e/evidence-check.spec.ts     # UI states, mocked backend; needs `npm run dev`
```

## Reproduce the experiments

```bash
cd backend
# dry run: validates and snapshots inputs, no calls
AEGIS_BENCHMARK_FILE=$PWD/data/evaluation/questions_v1.json PYTHONPATH=. \
  python -m app.evaluation.pilot_runner --dry-run --spec ../pilot-config/main-v1-44q-3rep.json
# live run (about 800 model calls): add --execute --output-root ../pilot-runs
# offline analysis of any saved run (no model calls)
PYTHONPATH=. python ../docs/research/scripts/analyse_run.py ../pilot-runs/<RUN_ID> /tmp/analysis
```

Each figure in `docs/research/evaluation-methods-and-results.md` lists the command that regenerates it.

## Research integrity

- Corpora, benchmarks, attack manifests and run records are never edited in place. New versions are new
  files with hashes.
- Failed or missing model results stay in the record as unavailable, never as zero.
- The verifier and runtime indicators never see reference answers, clean counterparts or attack labels.
- AI assistance was used for drafting, coding and analysis, and is acknowledged under the module's policy.
