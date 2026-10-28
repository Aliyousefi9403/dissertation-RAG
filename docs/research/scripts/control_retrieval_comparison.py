"""Retrieval-only comparison: clean vs formatting-only control vs PWWS-poisoned.

No LLM calls. Indexes backend/data/control/knowledge_base into its own Qdrant
collection, using the same loader, splitter, embeddings and top-k as the
pipeline (app.ingestion.load_documents). It never touches the clean or
poisoned collections. Then scores Hit@3 and RR for every benchmark question
with the project's own metric.

Usage (Qdrant running):
  cd backend && PYTHONPATH=. python ../docs/research/scripts/control_retrieval_comparison.py BENCHMARK.json OUT.json [--index]
"""

import json
import sys
from pathlib import Path

from app.config import QDRANT_URL, RETRIEVAL_TOP_K, get_qdrant_collection
from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from app.generation.rag_chain import build_sources
from app.ingestion.load_documents import add_document_metadata, split_documents
from app.vectorstore.qdrant_store import get_embeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_qdrant import QdrantVectorStore

CONTROL_ROOT = (
    Path(__file__).resolve().parents[3] / "backend/data/control/knowledge_base"
)
CONTROL_COLLECTION = "cybersecurity_knowledge_base_control_flattened"


def index_control():
    loader = DirectoryLoader(
        str(CONTROL_ROOT),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    chunks = split_documents(add_document_metadata(loader.load(), "control"))
    QdrantVectorStore.from_documents(
        chunks,
        embedding=get_embeddings(),
        url=QDRANT_URL,
        collection_name=CONTROL_COLLECTION,
        force_recreate=True,
    )
    return len(chunks)


def main(benchmark, out, do_index):
    if do_index:
        print("control chunks:", index_control())
    embeddings = get_embeddings()
    stores = {
        state: QdrantVectorStore.from_existing_collection(
            embedding=embeddings, collection_name=name, url=QDRANT_URL
        )
        for state, name in (
            ("clean", get_qdrant_collection("clean")),
            ("control", CONTROL_COLLECTION),
            ("poisoned", get_qdrant_collection("poisoned")),
        )
    }
    rows = []
    for q in json.loads(Path(benchmark).read_text()):
        row = {
            "id": q["id"],
            "split": q.get("split"),
            "category": q.get("question_category"),
        }
        for state, store in stores.items():
            sources = build_sources(
                store.similarity_search_with_score(q["question"], k=RETRIEVAL_TOP_K)
            )
            hit, rr = hit_at_3_and_reciprocal_rank(
                sources, q["expected_attack_type"], q["expected_sections"]
            )
            row[f"{state}_hit"], row[f"{state}_rr"] = hit, rr
        rows.append(row)
    summary = {
        s: {
            "hit_at_3": round(sum(r[f"{s}_hit"] for r in rows) / len(rows), 4),
            "mrr": round(sum(r[f"{s}_rr"] for r in rows) / len(rows), 4),
        }
        for s in ("clean", "control", "poisoned")
    }
    with open(out, "x") as handle:
        json.dump(
            {
                "benchmark": str(benchmark),
                "n": len(rows),
                "summary": summary,
                "rows": rows,
            },
            handle,
            indent=1,
        )
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--index" in sys.argv)
