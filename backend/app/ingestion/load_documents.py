import argparse
from pathlib import Path

from app.config import (
    QDRANT_URL,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    get_qdrant_collection,
    get_knowledge_base_path,
)

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ingestion.section_metadata import section_for_offset


def add_document_metadata(documents, system_state: str):
    for document in documents:
        source_path = Path(document.metadata["source"])
        attack_type = source_path.stem

        document.metadata.update(
            {
                "attack_type": attack_type,
                "origin": system_state,
                "system_state": system_state,
                "source_authority": "pending_kb_rebuild",
            }
        )

    return documents


def load_documents(system_state: str = "clean"):
    kb_path = get_knowledge_base_path(system_state)

    loader = DirectoryLoader(
        path=str(kb_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )

    documents = loader.load()

    if not documents:
        raise RuntimeError(
            f"No Markdown documents found in {kb_path}"
        )

    return add_document_metadata(documents, system_state)


def annotate_chunk_metadata(chunks):
    """Attaches `chunk_index` and `section` to each chunk."""
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        chunk.metadata["section"] = section_for_offset(
            chunk.metadata.get("source", ""),
            chunk.metadata.get("start_index"),
        )

    return chunks


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)
    return annotate_chunk_metadata(chunks)


def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def index_documents(system_state: str = "clean"):
    kb_path = get_knowledge_base_path(system_state)
    collection_name = get_qdrant_collection(system_state)

    print(f"System state: {system_state}")
    print(f"Knowledge base: {kb_path}")
    print(f"Qdrant collection: {collection_name}")

    documents = load_documents(system_state)
    chunks = split_documents(documents)
    embeddings = create_embeddings()

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        collection_name=collection_name,
        force_recreate=True,
    )

    print(f"Loaded documents: {len(documents)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Qdrant collection: {collection_name}")
    print("Indexing completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--system-state",
        default="clean",
        choices=["clean", "poisoned", "defended"],
    )

    args = parser.parse_args()

    index_documents(args.system_state)