from langchain_openai import ChatOpenAI

from app.config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
)


def create_llm() -> ChatOpenAI:
    if LLM_PROVIDER.lower() != "openai":
        raise ValueError(
            f"Unsupported LLM provider: {LLM_PROVIDER}. "
            "Currently supported: openai."
        )

    if not LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY is missing. Add it to your local .env file."
        )

    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        temperature=LLM_TEMPERATURE,
    )