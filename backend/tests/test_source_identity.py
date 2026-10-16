"""Synthetic document identities and isolated /compare integration tests."""

import importlib.util
import os
import socket
import sqlite3
import sys
from pathlib import Path, PurePosixPath
from types import ModuleType
from unittest.mock import Mock

import pytest
from app.evaluation.source_identity import (
    CYBERSECURITY_DATASET_NAMESPACE,
    build_document_overlap,
    resolve_document_identity,
)
from pydantic import BaseModel, ConfigDict

ROOTS = {
    PurePosixPath("/corpora/clean"): CYBERSECURITY_DATASET_NAMESPACE,
    PurePosixPath("/corpora/poisoned"): CYBERSECURITY_DATASET_NAMESPACE,
    PurePosixPath("/corpora/defended"): CYBERSECURITY_DATASET_NAMESPACE,
}


def _source(path, offset=0):
    return {
        "source": path,
        "score": 0.9,
        "content": "Synthetic evidence.",
        "metadata": {"source": path, "start_index": offset, "attack_type": "sample"},
    }


@pytest.mark.parametrize("state", ["clean", "poisoned", "defended"])
def test_corresponding_documents_match_across_explicit_roots(state):
    assert resolve_document_identity(
        _source(f"/corpora/{state}/injection/sql.md"), corpus_roots=ROOTS
    ) == (CYBERSECURITY_DATASET_NAMESPACE, "injection/sql.md")


def test_basename_collisions_case_and_namespaces_remain_distinct():
    roots = {**ROOTS, "/other-dataset": "other.dataset"}
    paths = [
        "/corpora/clean/injection/sql.md", "/corpora/poisoned/archive/sql.md",
        "/corpora/clean/injection/SQL.md", "/other-dataset/injection/sql.md",
    ]
    identities = {resolve_document_identity(_source(path), corpus_roots=roots) for path in paths}
    assert len(identities) == 4
    assert None not in identities


def test_offsets_content_hashes_and_chunk_indices_do_not_affect_identity():
    clean = _source("/corpora/clean/injection/sql.md", 12)
    poisoned = _source("/corpora/poisoned/injection/sql.md", 987)
    clean["metadata"].update(chunk_index=1, content_hash="original", document_version="v1")
    poisoned["metadata"].update(chunk_index=9, content_hash="changed", document_version="v2")
    poisoned["content"] = "Perturbed synthetic evidence."
    assert resolve_document_identity(clean, corpus_roots=ROOTS) == resolve_document_identity(
        poisoned, corpus_roots=ROOTS
    )


@pytest.mark.parametrize("source", [
    {"source": "/corpora/clean/doc.md"},
    {"metadata": {"source": "/corpora/clean/doc.md"}},
    {"source": None, "metadata": {"source": "/corpora/clean/doc.md"}},
    {"source": "", "metadata": {"source": "/corpora/clean/doc.md"}},
    {"source": "/corpora/clean/doc.md", "metadata": {"source": "/corpora/poisoned/doc.md"}},
])
def test_single_supplied_path_or_agreeing_identities_are_accepted(source):
    assert resolve_document_identity(source, corpus_roots=ROOTS) == (
        CYBERSECURITY_DATASET_NAMESPACE, "doc.md"
    )


@pytest.mark.parametrize("path", [
    "/unknown/doc.md", "/corpora/clean-extra/doc.md", "injection/sql.md",
    "corpora/clean/doc.md", "/corpora/clean/../clean/doc.md", "/corpora/clean/../outside.md",
    "/corpora/clean", "/corpora/clean/", "/corpora/clean/folder/",
    "//corpora/clean/doc.md", "/corpora/clean/a\x00.md", r"C:\corpora\clean\doc.md",
    "/corpora/clean/a\\b.md", "", None, 42, False, [], {},
])
def test_unknown_relative_traversal_and_malformed_paths_are_unavailable(path):
    assert resolve_document_identity(_source(path), corpus_roots=ROOTS) is None


@pytest.mark.parametrize("source", [
    {}, {"metadata": "malformed"}, None,
    {"source": "/corpora/clean/a.md", "metadata": {"source": "/corpora/clean/b.md"}},
    {"source": "/unknown/a.md", "metadata": {"source": "/corpora/clean/a.md"}},
    {"source": "/corpora/clean/a.md", "metadata": {"source": "/unknown/a.md"}},
    {"source": 123, "metadata": {"source": "/corpora/clean/a.md"}},
])
def test_missing_conflicting_or_partly_unknown_sources_are_not_guessed(source):
    assert resolve_document_identity(source, corpus_roots=ROOTS) is None


@pytest.mark.parametrize("namespace", [CYBERSECURITY_DATASET_NAMESPACE, "other.dataset"])
def test_nested_recognised_roots_are_ambiguous_even_with_same_namespace(namespace):
    roots = {**ROOTS, "/corpora/clean/injection": namespace}
    assert resolve_document_identity(
        _source("/corpora/clean/injection/sql.md"), corpus_roots=roots
    ) is None


def test_lexical_processing_does_not_access_files_or_resolve_symlinks(monkeypatch):
    blocked = Mock(side_effect=AssertionError("Filesystem access is forbidden"))
    with monkeypatch.context() as guarded:
        for name in ("resolve", "stat", "exists", "open", "read_text"):
            guarded.setattr(Path, name, blocked)
        for name in ("stat", "lstat", "readlink"):
            guarded.setattr(os, name, blocked)
        identity = resolve_document_identity(
            _source("/corpora/clean/alias/./doc.md"), corpus_roots=ROOTS
        )
        overlap = build_document_overlap(
            [_source("/corpora/clean/alias/doc.md")],
            [_source("/corpora/poisoned/alias/doc.md")], corpus_roots=ROOTS,
        )
    blocked.assert_not_called()
    assert identity == (CYBERSECURITY_DATASET_NAMESPACE, "alias/doc.md")
    assert overlap["jaccard"] == 1.0


def test_duplicate_chunks_are_deduplicated_at_document_level_without_mutation():
    clean = [_source("/corpora/clean/a.md", offset) for offset in (0, 100, 200)]
    poisoned = [_source("/corpora/poisoned/a.md", offset) for offset in (20, 120)]
    assert build_document_overlap(clean, poisoned, corpus_roots=ROOTS) == {
        "schema_version": 1, "status": "ok", "jaccard": 1.0,
        "clean_source_count": 3, "poisoned_source_count": 2,
        "clean_unknown_source_count": 0, "poisoned_unknown_source_count": 0,
        "clean_known_document_count": 1, "poisoned_known_document_count": 1,
        "known_shared_document_count": 1, "known_union_document_count": 1,
    }
    assert clean == [_source("/corpora/clean/a.md", offset) for offset in (0, 100, 200)]
    assert poisoned == [_source("/corpora/poisoned/a.md", offset) for offset in (20, 120)]


def test_partial_intersection_uses_document_union_and_final_rounding():
    overlap = build_document_overlap(
        [_source("/corpora/clean/a.md"), _source("/corpora/clean/b.md")],
        [_source("/corpora/poisoned/b.md"), _source("/corpora/poisoned/c.md")],
        corpus_roots=ROOTS,
    )
    assert overlap["known_shared_document_count"] == 1
    assert overlap["known_union_document_count"] == 3
    assert overlap["jaccard"] == 0.3333


@pytest.mark.parametrize("clean,poisoned,status,jaccard", [
    ([], [], "both_empty", None),
    ([], [_source("/corpora/poisoned/a.md")], "ok", 0.0),
    ([_source("/corpora/clean/a.md")], [], "ok", 0.0),
    ([], [_source("/unknown/a.md")], "unknown_identity", None),
    ([_source("/unknown/a.md")], [], "unknown_identity", None),
])
def test_empty_sides_and_unknown_identities_have_explicit_status(clean, poisoned, status, jaccard):
    overlap = build_document_overlap(clean, poisoned, corpus_roots=ROOTS)
    assert overlap["status"] == status
    assert overlap["jaccard"] == jaccard
    assert overlap["clean_source_count"] == len(clean)
    assert overlap["poisoned_source_count"] == len(poisoned)


def test_unknown_sources_remain_counted_and_prevent_known_only_jaccard():
    overlap = build_document_overlap(
        [_source("/corpora/clean/a.md"), _source("/unknown/x.md"), _source("/unknown/x.md")],
        [_source("/corpora/poisoned/a.md"), _source("/unknown/x.md")], corpus_roots=ROOTS,
    )
    assert overlap["status"] == "unknown_identity"
    assert overlap["jaccard"] is None
    assert overlap["clean_source_count"] == 3
    assert overlap["poisoned_source_count"] == 2
    assert overlap["clean_unknown_source_count"] == 2
    assert overlap["poisoned_unknown_source_count"] == 1
    assert overlap["clean_known_document_count"] == overlap["poisoned_known_document_count"] == 1
    assert overlap["known_shared_document_count"] == overlap["known_union_document_count"] == 1


@pytest.fixture
def api_module(monkeypatch):
    class HistoryPayload(BaseModel):
        model_config = ConfigDict(extra="allow")

    history_service = ModuleType("app.history.service")
    history_service.save_experiment = Mock()
    history = ModuleType("app.history")
    history.__path__ = []
    history.service = history_service
    dependencies = {
        "app.config": {"KNOWLEDGE_BASE_PATHS": dict(zip(("clean", "poisoned", "defended"), ROOTS))},
        "app.evaluation.compare_metrics": {"build_research_metrics": Mock(return_value={
            "attack_quality": None, "retrieval_quality": None,
            "generation_quality": None, "attack_success": None,
        })},
        "app.generation.rag_chain": {"answer_question": Mock()},
        "app.history.models": {
            "ExperimentCreate": HistoryPayload, "ExperimentRecord": HistoryPayload,
            "ExperimentStats": HistoryPayload,
        },
    }
    for name, attributes in dependencies.items():
        dependency = ModuleType(name)
        dependency.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, dependency)
    monkeypatch.setitem(sys.modules, "app.history", history)
    monkeypatch.setitem(sys.modules, "app.history.service", history_service)

    blocked = Mock(side_effect=AssertionError("Network/database access forbidden"))
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    path = Path(__file__).resolve().parents[1] / "app/main.py"
    spec = importlib.util.spec_from_file_location("api_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    blocked.assert_not_called()


def _compare(api_module, clean, poisoned):
    api_module.answer_question.side_effect = [
        {"answer": "Clean answer", "sources": clean},
        {"answer": "Poisoned answer", "sources": poisoned},
    ]
    result = api_module.compare_states(api_module.CompareRequest(question="  Question?  "))
    assert result["question"] == "Question?"
    assert api_module.CompareResponse.model_validate(result).model_dump()["metrics"] == result["metrics"]
    return result["metrics"]


def test_compare_adds_document_overlap_without_changing_any_legacy_metric(api_module):
    metrics = _compare(
        api_module,
        [_source("/corpora/clean/a.md", 10), _source("/corpora/clean/a.md", 20)],
        [_source("/corpora/poisoned/a.md", 999)],
    )
    document_overlap = metrics.pop("document_overlap")
    assert document_overlap["schema_version"] == 1
    assert document_overlap["jaccard"] == 1.0
    assert metrics == {
        "attack_method": "PWWS", "top_k": 2, "top_k_overlap": 0.0,
        "retrieval_shift": 1.0, "clean_top_score": 0.9, "poisoned_top_score": 0.9,
        "top_score_delta": 0.0, "answer_changed": True, "shared_chunks": 0,
        "clean_source_ids": ["/corpora/clean/a.md::10", "/corpora/clean/a.md::20"],
        "poisoned_source_ids": ["/corpora/poisoned/a.md::999"],
        "clean_attack_types": ["sample", "sample"], "poisoned_attack_types": ["sample"],
    }
    saved = api_module.history_service.save_experiment.call_args.args[0].model_dump()
    assert saved["top_k_overlap"] == 0.0
    assert saved["retrieval_shift"] == 1.0
    assert saved["shared_chunks"] == 0
    assert "document_overlap" not in saved


@pytest.mark.parametrize("sources,status,document_jaccard", [
    ([], "both_empty", None),
    ([_source("/corpora/clean/a.md", 10)], "ok", 1.0),
    ([_source("/unknown/a.md", 10)], "unknown_identity", None),
])
def test_compare_preserves_legacy_agreement_for_identical_or_empty_sets(
    api_module, sources, status, document_jaccard
):
    metrics = _compare(api_module, sources, sources)
    assert metrics["top_k_overlap"] == 1.0
    assert metrics["retrieval_shift"] == 0.0
    assert metrics["shared_chunks"] == len(sources)
    assert metrics["document_overlap"]["status"] == status
    assert metrics["document_overlap"]["jaccard"] == document_jaccard
