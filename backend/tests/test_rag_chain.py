"""RAG response-contract tests with retrieval and generation isolated."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from langchain_core.documents import Document


@pytest.fixture
def rag_chain(monkeypatch):
    # Stub dependencies before import: never load configuration, models,
    # the vector store, or the API/history modules for these unit tests.
    search = ModuleType("app.retrieval.search")
    search.search_knowledge_base = Mock()
    factory = ModuleType("app.generation.llm_factory")
    factory.create_llm = Mock()
    prompt = ModuleType("app.generation.prompt")
    prompt.RAG_PROMPT = MagicMock()
    for dependency in (search, factory, prompt):
        monkeypatch.setitem(sys.modules, dependency.__name__, dependency)

    path = Path(__file__).resolve().parents[1] / "app/generation/rag_chain.py"
    spec = importlib.util.spec_from_file_location("rag_chain_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("system_state", ["clean", "poisoned", "defended"])
def test_empty_retrieval_abstains_without_generation(rag_chain, system_state):
    question = "What evidence supports this claim?"
    rag_chain.search_knowledge_base.return_value = []

    result = rag_chain.answer_question(question, system_state=system_state)

    assert result == {
        "question": question,
        "answer": (
            "I cannot answer this question because no supporting evidence "
            "was retrieved."
        ),
        "sources": [],
        "system_state": system_state,
    }
    rag_chain.search_knowledge_base.assert_called_once_with(
        query=question, system_state=system_state
    )
    rag_chain.create_llm.assert_not_called()
    assert rag_chain.RAG_PROMPT.mock_calls == []


@pytest.mark.parametrize("system_state", ["clean", "poisoned", "defended"])
def test_nonempty_retrieval_preserves_generation_and_sources(rag_chain, system_state):
    question = "How can SQL injection be prevented?"
    document = Document(
        page_content="Use parameterized queries.",
        metadata={"source": "sql_injection.md", "start_index": 42},
    )
    rag_chain.search_knowledge_base.return_value = [(document, 0.875)]
    llm = rag_chain.create_llm.return_value
    chain = rag_chain.RAG_PROMPT.__or__.return_value
    chain.invoke.return_value = SimpleNamespace(
        content="Use parameterized queries. [Source 1]"
    )

    result = rag_chain.answer_question(question, system_state=system_state)

    rag_chain.search_knowledge_base.assert_called_once_with(
        query=question, system_state=system_state
    )
    rag_chain.create_llm.assert_called_once_with()
    rag_chain.RAG_PROMPT.__or__.assert_called_once_with(llm)
    chain.invoke.assert_called_once_with({
        "question": question,
        "context": (
            "[Source 1]\nFile: sql_injection.md\nSimilarity score: 0.8750\n"
            "Start index: 42\nContent:\nUse parameterized queries."
        ),
    })
    assert result == {
        "question": question,
        "answer": "Use parameterized queries. [Source 1]",
        "sources": [{
            "source_number": 1,
            "source": "sql_injection.md",
            "score": 0.875,
            "content": "Use parameterized queries.",
            "metadata": document.metadata,
        }],
        "system_state": system_state,
    }


def test_default_state_remains_clean(rag_chain):
    rag_chain.search_knowledge_base.return_value = []

    result = rag_chain.answer_question("What evidence is available?")

    assert result["system_state"] == "clean"
    rag_chain.search_knowledge_base.assert_called_once_with(
        query="What evidence is available?", system_state="clean"
    )


def test_empty_question_still_raises_before_retrieval(rag_chain):
    with pytest.raises(ValueError, match="^Question cannot be empty\\.$"):
        rag_chain.answer_question("")

    rag_chain.search_knowledge_base.assert_not_called()
    rag_chain.create_llm.assert_not_called()
    assert rag_chain.RAG_PROMPT.mock_calls == []
