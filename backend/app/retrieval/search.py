from app.vectorstore.qdrant_store import get_vector_store

from app.config import RETRIEVAL_TOP_K


def search_knowledge_base(
    query: str,
    limit: int = RETRIEVAL_TOP_K,
) -> None:
    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(
        query=query,
        k=limit,
    )

    print(f"\nQuery: {query}\n")

    for position, (document, score) in enumerate(results, start=1):
        print(f"Result {position}")
        print(f"Score: {score:.4f}")
        print(f"Source: {document.metadata.get('source', 'Unknown')}")
        print(document.page_content)
        print("-" * 70)


if __name__ == "__main__":
    search_knowledge_base(
        "How can attackers manipulate a database through user input?"
    )