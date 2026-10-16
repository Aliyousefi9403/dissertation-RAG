from langchain_core.documents import Document

from app.config import RETRIEVAL_TOP_K
from app.vectorstore.qdrant_store import get_vector_store


def search_knowledge_base(
    query: str,
    k: int = RETRIEVAL_TOP_K,
    system_state: str = "clean",
) -> list[tuple[Document, float]]:
    vector_store = get_vector_store(system_state=system_state)

    return vector_store.similarity_search_with_score(
        query,
        k=k,
    )


if __name__ == "__main__":
    query = "How can attackers manipulate a database through user input?"

    results = search_knowledge_base(query)

    print(f"\nQuery: {query}\n")

    for position, (document, score) in enumerate(results, start=1):
        print(f"Result {position}")
        print(f"Score: {score:.4f}")
        print(f"Source: {document.metadata.get('source', 'Unknown')}")
        print(document.page_content)
        print("-" * 70)