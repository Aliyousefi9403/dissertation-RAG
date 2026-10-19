"""Index an attack corpus into its own Qdrant collection (create-only).

Same loader, splitter (500/100) and embeddings (all-MiniLM-L6-v2) as the pipeline
(app.ingestion.load_documents). Refuses to run if the collection already exists, and never
touches the clean, poisoned or control collections. No LLM calls.

Usage (from backend/, Qdrant running): PYTHONPATH=. python ../docs/research/scripts/index_attack_corpus.py textfooler
"""

import sys

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.config import QDRANT_URL, get_knowledge_base_path, get_qdrant_collection
from app.ingestion.load_documents import add_document_metadata, split_documents
from app.vectorstore.qdrant_store import get_embeddings

PROTECTED = {"clean", "poisoned", "defended"}


def main(state):
    assert state not in PROTECTED, f"{state} is an existing pipeline collection; refusing"
    collection = get_qdrant_collection(state)
    if QdrantClient(url=QDRANT_URL).collection_exists(collection):
        raise SystemExit(f"{collection} already exists; outputs are create-only")
    loader = DirectoryLoader(str(get_knowledge_base_path(state)), glob="**/*.md", loader_cls=TextLoader,
                             loader_kwargs={"encoding": "utf-8"})
    chunks = split_documents(add_document_metadata(loader.load(), state))
    QdrantVectorStore.from_documents(chunks, embedding=get_embeddings(), url=QDRANT_URL, collection_name=collection)
    print(f"{collection}: {len(chunks)} chunks")


if __name__ == "__main__":
    main(sys.argv[1])
