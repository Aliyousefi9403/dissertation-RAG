from app.config import (
    KNOWLEDGE_BASE_PATH,
    QDRANT_URL,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pathlib import Path


def add_document_metadata(documents):
    for document in documents:
        source_path = Path(document.metadata["source"])
        attack_type = source_path.stem

        document.metadata.update(
            {
                "attack_type": attack_type,
                "origin": "clean",
                "source_authority": "pending_kb_rebuild",
            }
        )

    return documents





def load_documents():
    loader = DirectoryLoader(
        path=str(KNOWLEDGE_BASE_PATH),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )

    documents = loader.load()

    if not documents:
        raise RuntimeError(
            f"No Markdown documents found in {KNOWLEDGE_BASE_PATH}"
        )

    return add_document_metadata(documents)


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )
    return splitter.split_documents(documents)


def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def index_documents():
    documents = load_documents()
    chunks = split_documents(documents)
    embeddings = create_embeddings()

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        force_recreate=True,
    )

    print(f"Loaded documents: {len(documents)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Qdrant collection: {QDRANT_COLLECTION}")
    print("Indexing completed successfully.")


if __name__ == "__main__":
    index_documents()