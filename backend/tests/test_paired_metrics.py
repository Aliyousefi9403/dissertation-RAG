"""Synthetic paired-accounting tests; evaluator integration uses only mocks."""

import importlib.util
import json
import socket
import sqlite3
import sys
from itertools import product
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest
from app.evaluation.paired_metrics import build_paired_metrics, classify_score


def _correctness_rows(pairs):
    return [
        {"clean_answer_correctness": clean, "poisoned_answer_correctness": poisoned}
        for clean, poisoned in pairs
    ]


def _assert_invariants(summary):
    total = summary["total_observations"]
    assert total == sum(summary[key] for key in (
        "paired_valid_count", "clean_only_unavailable_count",
        "poisoned_only_unavailable_count", "both_unavailable_count",
    ))
    for condition in ("clean", "poisoned"):
        assert total == sum(
            summary[f"{condition}_{status}_count"]
            for status in ("valid", "missing", "malformed")
        )


@pytest.mark.parametrize("value", [0, 1, 0.0, 0.75, -1, 2.0])
def test_finite_builtin_scores_are_preserved_without_clipping(value):
    score, status = classify_score(value)
    assert status == "valid"
    assert score == value
    assert type(score) is type(value)


@pytest.mark.parametrize("value", [
    float("nan"), float("inf"), float("-inf"), True, False,
    "0.75", "invalid", "", [], {}, (), object(),
])
def test_invalid_scores_are_malformed_not_missing(value):
    assert classify_score(value) == (None, "malformed")
    summary = build_paired_metrics(_correctness_rows([(value, 1)]))["correctness"]
    assert summary["clean_malformed_count"] == 1
    assert summary["clean_missing_count"] == 0
    assert summary["clean_only_unavailable_count"] == 1
    assert summary["paired_valid_count"] == 0
    _assert_invariants(summary)


def test_none_and_absent_scores_are_missing():
    assert classify_score(None) == (None, "missing")
    rows = [{}, {"clean_answer_correctness": None, "poisoned_answer_correctness": None}]
    summary = build_paired_metrics(rows)["correctness"]
    assert summary["clean_missing_count"] == summary["poisoned_missing_count"] == 2
    assert summary["clean_malformed_count"] == summary["poisoned_malformed_count"] == 0
    assert summary["both_unavailable_count"] == 2
    _assert_invariants(summary)


def test_complete_pairs_and_versioned_schema():
    summary = build_paired_metrics(_correctness_rows([(1, 0.5), (0.5, 0.75)]))
    assert set(summary) == {"schema_version", "delta_direction", "correctness", "faithfulness"}
    assert summary["schema_version"] == 1
    assert summary["delta_direction"] == "poisoned_minus_clean"
    assert summary["correctness"] == {
        "total_observations": 2,
        "clean_valid_count": 2,
        "poisoned_valid_count": 2,
        "paired_valid_count": 2,
        "clean_only_unavailable_count": 0,
        "poisoned_only_unavailable_count": 0,
        "both_unavailable_count": 0,
        "clean_missing_count": 0,
        "clean_malformed_count": 0,
        "poisoned_missing_count": 0,
        "poisoned_malformed_count": 0,
        "paired_clean_mean": 0.75,
        "paired_poisoned_mean": 0.625,
        "mean_delta": -0.125,
    }


def test_asymmetric_missingness_never_pairs_different_questions():
    summary = build_paired_metrics(
        _correctness_rows([(1, 0.5), (0, None), (None, 1)])
    )["correctness"]
    assert summary["clean_valid_count"] == summary["poisoned_valid_count"] == 2
    assert summary["paired_valid_count"] == 1
    assert summary["clean_only_unavailable_count"] == 1
    assert summary["poisoned_only_unavailable_count"] == 1
    assert summary["paired_clean_mean"] == 1
    assert summary["paired_poisoned_mean"] == 0.5
    assert summary["mean_delta"] == -0.5
    _assert_invariants(summary)


@pytest.mark.parametrize("pairs", [[], [(1, None), (None, 0)], [(None, None)]])
def test_no_valid_pairs_returns_null_summaries(pairs):
    result = build_paired_metrics(_correctness_rows(pairs))
    for metric in ("correctness", "faithfulness"):
        summary = result[metric]
        assert summary["total_observations"] == len(pairs)
        assert summary["paired_valid_count"] == 0
        for key in ("paired_clean_mean", "paired_poisoned_mean", "mean_delta"):
            assert summary[key] is None
        _assert_invariants(summary)


@pytest.mark.parametrize("clean,poisoned,expected", [(1, 0, -1), (0, 1, 1), (0, 0, 0)])
def test_delta_is_poisoned_minus_clean(clean, poisoned, expected):
    summary = build_paired_metrics(_correctness_rows([(clean, poisoned)]))["correctness"]
    assert summary["mean_delta"] == expected


def test_deltas_are_computed_before_rounding_means_or_individual_deltas():
    summary = build_paired_metrics(_correctness_rows([(0.10004, 0.10006)]))["correctness"]
    assert summary["paired_clean_mean"] == 0.1
    assert summary["paired_poisoned_mean"] == 0.1001
    assert summary["mean_delta"] == 0.0

    summary = build_paired_metrics(
        _correctness_rows([(0.5, 0.50004), (0.5, 0.50004), (0.5, 0.50014)])
    )["correctness"]
    assert summary["mean_delta"] == 0.0001


def test_correctness_and_faithfulness_use_independent_pairs_without_mutation():
    rows = [
        {"clean_answer_correctness": 1, "poisoned_answer_correctness": 0.5},
        {"clean_faithfulness": 0.5, "poisoned_faithfulness": 1},
    ]
    original = [dict(row) for row in rows]
    result = build_paired_metrics(rows)
    assert result["correctness"]["mean_delta"] == -0.5
    assert result["faithfulness"]["mean_delta"] == 0.5
    for metric in ("correctness", "faithfulness"):
        assert result[metric]["paired_valid_count"] == 1
        assert result[metric]["both_unavailable_count"] == 1
        _assert_invariants(result[metric])
    assert rows == original


@pytest.mark.parametrize("clean,poisoned", list(product([0.5, None, float("nan")], repeat=2)))
def test_every_availability_combination_accounts_for_one_observation(clean, poisoned):
    summary = build_paired_metrics(_correctness_rows([(clean, poisoned)]))["correctness"]
    assert summary["total_observations"] == 1
    _assert_invariants(summary)


@pytest.fixture
def evaluator(monkeypatch):
    # Stub every application dependency before loading the runner. No real
    # config/.env, benchmark, manifest, source file, model, or history import.
    dependencies = {
        "app.config": {"PROJECT_ROOT": Path("/unused-evaluation-root")},
        "app.evaluation.compare_metrics": {
            "build_attack_success": Mock(return_value={"rag_attack_success": False}),
        },
        "app.evaluation.llm_judge": {
            "evaluate_correctness": Mock(), "evaluate_faithfulness": Mock(),
        },
        "app.evaluation.pwws_manifest": {
            "get_summary": Mock(return_value=None), "load_manifest": Mock(return_value=[]),
        },
        "app.evaluation.retrieval_metrics": {
            "hit_at_3_and_reciprocal_rank": Mock(return_value=(1, 1.0)),
            "load_questions": Mock(),
            "poison_hit_at_3": Mock(return_value={
                "poison_hit_at_3": 0, "poisoned_chunks_in_top_3": 0,
            }),
        },
        "app.generation.rag_chain": {"answer_question": Mock()},
        "app.ingestion.section_metadata": {"section_for_offset": Mock()},
    }
    for name, attributes in dependencies.items():
        dependency = ModuleType(name)
        dependency.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, dependency)

    blocked = Mock(side_effect=AssertionError("I/O forbidden in mocked evaluator tests"))
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    monkeypatch.setattr(Path, "write_text", blocked)
    path = Path(__file__).resolve().parents[1] / "app/evaluation/run_research_evaluation.py"
    spec = importlib.util.spec_from_file_location("evaluation_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    blocked.assert_not_called()


def _configure_run(evaluator, observations):
    questions = [
        {"id": f"q{i}", "question": f"Question {i}?", "expected_attack_type": "sample"}
        for i in range(len(observations))
    ]
    by_question = {item["question"]: row for item, row in zip(questions, observations)}
    evaluator.load_questions.return_value = questions
    evaluator.answer_question.side_effect = lambda question, system_state: {
        "answer": system_state, "sources": [],
    }
    evaluator.evaluate_correctness.side_effect = lambda question, facts, answer: {
        "score": by_question[question].get(f"{answer}_answer_correctness"),
    }
    evaluator.evaluate_faithfulness.side_effect = lambda question, context, answer: {
        "score": by_question[question].get(f"{answer}_faithfulness"),
    }


def test_mocked_runner_preserves_legacy_outputs_and_adds_paired_metrics(evaluator):
    observations = _correctness_rows([(1, 0.5), (0, None), (None, 1)])
    observations[0].update(clean_faithfulness=0.75, poisoned_faithfulness=1)
    observations[1].update(clean_faithfulness=None, poisoned_faithfulness=0)
    observations[2].update(clean_faithfulness=0.5, poisoned_faithfulness=None)
    _configure_run(evaluator, observations)

    report = evaluator.run_evaluation()

    assert set(report) == {"aggregate", "per_question", "paired_metrics"}
    assert report["aggregate"] == {
        "question_count": 3,
        "clean_hit_at_3_rate": 1.0, "poisoned_hit_at_3_rate": 1.0,
        "clean_mrr": 1.0, "poisoned_mrr": 1.0, "poison_hit_at_3_rate": 0.0,
        "mean_semantic_similarity": None, "mean_modification_rate": None,
        "mean_clean_correctness": 0.5, "mean_poisoned_correctness": 0.75,
        "mean_clean_faithfulness": 0.625, "mean_poisoned_faithfulness": 0.5,
        "rag_attack_success_rate": 0.0, "pwws_surrogate_asr": None,
    }
    for i, row in enumerate(report["per_question"]):
        assert row == {
            "id": f"q{i}", "question": f"Question {i}?", "expected_attack_type": "sample",
            "expected_sections": [],
            "clean_hit_at_3": 1, "clean_reciprocal_rank": 1.0,
            "poisoned_hit_at_3": 1, "poisoned_reciprocal_rank": 1.0,
            "poison_hit_at_3": 0, "poisoned_chunks_in_top_3": 0,
            **observations[i],
            "rag_attack_success": False, "clean_top_3": [], "poisoned_top_3": [],
        }
    assert report["paired_metrics"]["correctness"]["mean_delta"] == -0.5
    assert report["paired_metrics"]["faithfulness"]["mean_delta"] == 0.25


def test_mocked_runner_retains_malformed_status_but_normalizes_downstream_scores(evaluator):
    observations = [
        {"clean_answer_correctness": float("nan"), "poisoned_answer_correctness": 0.5,
         "clean_faithfulness": 1, "poisoned_faithfulness": float("inf")},
        {"clean_answer_correctness": None, "poisoned_answer_correctness": "0.5",
         "clean_faithfulness": False, "poisoned_faithfulness": None},
    ]
    _configure_run(evaluator, observations)

    report = evaluator.run_evaluation()

    correctness = report["paired_metrics"]["correctness"]
    faithfulness = report["paired_metrics"]["faithfulness"]
    assert correctness["clean_missing_count"] == correctness["clean_malformed_count"] == 1
    assert correctness["poisoned_valid_count"] == correctness["poisoned_malformed_count"] == 1
    assert correctness["clean_only_unavailable_count"] == 1
    assert correctness["both_unavailable_count"] == 1
    assert faithfulness["clean_valid_count"] == faithfulness["clean_malformed_count"] == 1
    assert faithfulness["poisoned_missing_count"] == faithfulness["poisoned_malformed_count"] == 1
    assert faithfulness["poisoned_only_unavailable_count"] == 1
    assert faithfulness["both_unavailable_count"] == 1
    for metric in (correctness, faithfulness):
        assert metric["paired_valid_count"] == 0
        assert metric["mean_delta"] is None
        _assert_invariants(metric)
    assert report["aggregate"]["mean_clean_correctness"] is None
    assert report["aggregate"]["mean_poisoned_correctness"] == 0.5
    assert report["aggregate"]["mean_clean_faithfulness"] == 1
    assert report["aggregate"]["mean_poisoned_faithfulness"] is None
    for row in report["per_question"]:
        assert row["clean_answer_correctness"] is None
        assert row["poisoned_faithfulness"] is None
    calls = evaluator.build_attack_success.call_args_list
    assert calls[0].kwargs["generation_quality"] == {
        "clean_answer_correctness": None, "poisoned_answer_correctness": 0.5,
    }
    assert calls[1].kwargs["generation_quality"] == {
        "clean_answer_correctness": None, "poisoned_answer_correctness": None,
    }
    json.dumps(report, allow_nan=False)


def test_mocked_runner_treats_absent_scores_and_judge_none_as_missing(evaluator):
    _configure_run(evaluator, [{}])
    evaluator.evaluate_correctness.side_effect = [None, {"reason": "no score recorded"}]
    evaluator.evaluate_faithfulness.side_effect = [{}, {"score": None}]
    report = evaluator.run_evaluation()
    for metric in ("correctness", "faithfulness"):
        summary = report["paired_metrics"][metric]
        assert summary["clean_missing_count"] == summary["poisoned_missing_count"] == 1
        assert summary["clean_malformed_count"] == summary["poisoned_malformed_count"] == 0
        assert summary["both_unavailable_count"] == 1
        assert summary["mean_delta"] is None
        _assert_invariants(summary)


def test_mocked_empty_runner_returns_zero_counts_without_judge_calls(evaluator):
    _configure_run(evaluator, [])
    report = evaluator.run_evaluation()
    assert report["aggregate"]["question_count"] == 0
    assert report["per_question"] == []
    for metric in ("correctness", "faithfulness"):
        assert report["paired_metrics"][metric]["total_observations"] == 0
        assert report["paired_metrics"][metric]["mean_delta"] is None
    evaluator.answer_question.assert_not_called()
    evaluator.evaluate_correctness.assert_not_called()
    evaluator.evaluate_faithfulness.assert_not_called()
