from typing import Any

from langchain_core.documents import Document
from app.retrieval.search import search_knowledge_base


from app.generation.llm_factory import create_llm
from app.generation.prompt import RAG_PROMPT



def retrieve_documents(
    question: str,
    system_state: str = "clean",
) -> list[tuple[Document, float]]:
    return search_knowledge_base(
        query=question,
        system_state=system_state,
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


def answer_question(
    question: str,
    system_state: str = "clean",
    *,
    capture: dict[str, Any] | None = None,
    llm_factory=None,
    retrieval_fn=None,
) -> dict[str, Any]:
    """Optional pilot capture/adapters leave existing caller defaults intact."""

    if not question:
        raise ValueError("Question cannot be empty.")

    if capture is not None:
        capture.update(retrieval_status="pending", generation_status="not_started")
    try:
        results = (retrieval_fn or retrieve_documents)(question, system_state=system_state)
    except Exception as exc:
        if capture is not None:
            capture.update(retrieval_status="unavailable", error={
                "stage": "retrieval", "type": type(exc).__name__,
            })
        raise
    if capture is not None:
        capture.update(retrieval_status="ok", sources=build_sources(results))

    if not results:
        if capture is not None:
            capture.update(generation_status="abstained", request_attempts=0)
        return {
            "question": question,
            "answer": (
                "I cannot answer this question because no supporting evidence "
                "was retrieved."
            ),
            "sources": [],
            "system_state": system_state,
}
    try:
        context = format_context(results)
        if capture is not None:
            capture["context"] = context
        llm = (llm_factory or create_llm)()
        chain = RAG_PROMPT | llm
        response = chain.invoke({"question": question, "context": context})
    except Exception as exc:
        if capture is not None:
            capture.update(generation_status="unavailable", error={
                "stage": "generation", "type": type(exc).__name__,
            })
        raise
    if capture is not None:
        capture.update(generation_status="ok", answer=str(response.content))
        metadata = getattr(response, "response_metadata", {})
        capture["model_metadata"] = {
            key: metadata[key] for key in ("model_name", "model", "system_fingerprint")
            if isinstance(metadata, dict) and key in metadata
        }

    return {
        "question": question,
        "answer": str(response.content),
        "sources": build_sources(results),
        "system_state": system_state,
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
