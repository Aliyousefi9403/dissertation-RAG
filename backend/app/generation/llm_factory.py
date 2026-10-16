from typing import Optional

from langchain_openai import ChatOpenAI

from app.config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
)


def create_llm(temperature: Optional[float] = None) -> ChatOpenAI:
    """
    `temperature` overrides the configured default -- used by the
    research evaluators (app/evaluation/llm_judge.py), which must run at
    0 for reproducibility regardless of what LLM_TEMPERATURE is set to
    for normal answer generation. Existing callers (`create_llm()` with
    no args) are unaffected.
    """
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
        temperature=LLM_TEMPERATURE if temperature is None else temperature,
    )