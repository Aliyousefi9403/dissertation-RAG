from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.config import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    QDRANT_URL,
)


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vector_store() -> QdrantVectorStore:
    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        collection_name=QDRANT_COLLECTION,
        url=QDRANT_URL,
    )