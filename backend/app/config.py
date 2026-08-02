import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "data" / "raw" / "knowledge_base"

QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "cybersecurity_knowledge_base"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
RETRIEVAL_TOP_K = 3

# LLM configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))