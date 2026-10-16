from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.config import (
    EMBEDDING_MODEL,
    QDRANT_URL,
    get_qdrant_collection,
)


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vector_store(system_state: str = "clean") -> QdrantVectorStore:
    collection_name = get_qdrant_collection(system_state)

    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        collection_name=collection_name,
        url=QDRANT_URL,
    )