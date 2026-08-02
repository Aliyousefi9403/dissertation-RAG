from typing import Any

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.config import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    QDRANT_URL,
    RETRIEVAL_TOP_K,
)
from app.generation.llm_factory import create_llm
from app.generation.prompt import RAG_PROMPT


def create_vector_store() -> QdrantVectorStore:
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=QDRANT_COLLECTION,
        url=QDRANT_URL,
    )


def retrieve_documents(
    question: str,
) -> list[tuple[Document, float]]:
    vector_store = create_vector_store()

    return vector_store.similarity_search_with_score(
        query=question,
        k=RETRIEVAL_TOP_K,
    )


def format_context(
    results: list[tuple[Document, float]],
) -> str:
    formatted_sources: list[str] = []

    for position, (document, score) in enumerate(results, start=1):
        source = document.metadata.get("source", "Unknown source")
        start_index = document.metadata.get("start_index", "Unknown")

        formatted_sources.append(
            f"[Source {position}]\n"
            f"File: {source}\n"
            f"Similarity score: {score:.4f}\n"
            f"Start index: {start_index}\n"
            f"Content:\n{document.page_content}"
        )

    return "\n\n".join(formatted_sources)


def build_sources(
    results: list[tuple[Document, float]],
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []

    for position, (document, score) in enumerate(results, start=1):
        sources.append(
            {
                "source_number": position,
                "source": document.metadata.get(
                    "source",
                    "Unknown source",
                ),
                "score": float(score),
                "content": document.page_content,
                "metadata": document.metadata,
            }
        )

    return sources


def answer_question(question: str) -> dict[str, Any]:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    results = retrieve_documents(question)

    if not results:
        return {
            "question": question,
            "answer": (
                "No relevant information was found "
                "in the knowledge base."
            ),
            "sources": [],
        }

    context = format_context(results)
    llm = create_llm()
    chain = RAG_PROMPT | llm

    response = chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )

    return {
        "question": question,
        "answer": str(response.content),
        "sources": build_sources(results),
    }


if __name__ == "__main__":
    test_question = (
        "What is SQL injection, what damage can it cause, "
        "and how can it be prevented?"
    )

    result = answer_question(test_question)

    print(f"\nQuestion:\n{result['question']}\n")
    print(f"Answer:\n{result['answer']}\n")
    print("Retrieved sources:")

    for source in result["sources"]:
        print(
            f"- Source {source['source_number']}: "
            f"{source['source']} "
            f"(score={source['score']:.4f})"
        )