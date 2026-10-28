import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "data" / "raw" / "knowledge_base"
KNOWLEDGE_BASE_PATHS = {
    "clean": PROJECT_ROOT / "data" / "raw" / "knowledge_base",
    "poisoned": PROJECT_ROOT / "data" / "poisoned" / "knowledge_base",
    "defended": PROJECT_ROOT / "data" / "defended" / "knowledge_base",
    # Research-only state (not accepted by the API): the TextFooler-poisoned corpus.
    "textfooler": PROJECT_ROOT / "data" / "poisoned_textfooler" / "knowledge_base",
}
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTIONS = {
    "clean": "cybersecurity_knowledge_base",
    "poisoned": "cybersecurity_knowledge_base_poisoned",
    "defended": "cybersecurity_knowledge_base_defended",
    "textfooler": "cybersecurity_knowledge_base_textfooler",
}

DEFAULT_SYSTEM_STATE = "clean"


def get_qdrant_collection(system_state: str = DEFAULT_SYSTEM_STATE) -> str:
    try:
        return QDRANT_COLLECTIONS[system_state]
    except KeyError:
        valid_states = ", ".join(QDRANT_COLLECTIONS.keys())
        raise ValueError(
            f"Unknown system state '{system_state}'. "
            f"Expected one of: {valid_states}"
        )

def get_knowledge_base_path(
    system_state: str = DEFAULT_SYSTEM_STATE,
) -> Path:
    try:
        return KNOWLEDGE_BASE_PATHS[system_state]
    except KeyError:
        valid_states = ", ".join(KNOWLEDGE_BASE_PATHS.keys())
        raise ValueError(
            f"Unknown system state '{system_state}'. "
            f"Expected one of: {valid_states}"
        )        

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
RETRIEVAL_TOP_K = 3

# LLM configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))