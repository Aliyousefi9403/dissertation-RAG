"""
Proves the live `/compare` path (app.evaluation.compare_metrics) resolves
ground truth and returns real numeric values -- not None/N/A -- for an
exact benchmark question, using the SAME retrieval_metrics functions
(find_ground_truth, hit_at_3_and_reciprocal_rank, poison_hit_at_3) that
run_research_evaluation.py's offline pass exercises indirectly via
questions.json. No Qdrant, no live LLM calls (evaluate_correctness /
evaluate_faithfulness are monkeypatched).
"""

from __future__ import annotations

from app.evaluation import compare_metrics


SAMPLE_DOC = """# SQL Injection

## Attack description
v
This attack does something bad to the target and consumes resources.

## Detection indicators

Detection content is not automatically inferred.
"""


def _make_source(doc_path, start_index, content, attack_type="sql_injection"):
    return {
        "source": str(doc_path),
        "content": content,
        "metadata": {
            "source": str(doc_path),
            "start_index": start_index,
            "attack_type": attack_type,
        },
    }


def _clean_sources(doc_path):
    description_offset = SAMPLE_DOC.index("This attack does something bad")
    return [
        _make_source(
            doc_path,
            description_offset,
            "This attack does something bad to the target and consumes resources.",
        )
    ]


def test_build_retrieval_quality_returns_real_values_for_exact_question(tmp_path):
    doc_path = tmp_path / "sql_injection.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    question = "How does a SQL injection attack work?"
    clean_sources = _clean_sources(doc_path)
    poisoned_sources = _clean_sources(doc_path)

    result = compare_metrics.build_retrieval_quality(question, clean_sources, poisoned_sources)

    assert result["clean_hit_at_3"] == 1
    assert result["clean_reciprocal_rank"] == 1.0
    assert result["poisoned_hit_at_3"] == 1
    assert result["poisoned_reciprocal_rank"] == 1.0


def test_build_retrieval_quality_tolerates_formatting_differences(tmp_path):
    doc_path = tmp_path / "sql_injection.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    # Same question a user might type/paste live: doubled internal
    # whitespace, unlike the byte-exact fixture text in questions.json.
    question = "How does  a SQL injection   attack work?"
    clean_sources = _clean_sources(doc_path)
    poisoned_sources = _clean_sources(doc_path)

    result = compare_metrics.build_retrieval_quality(question, clean_sources, poisoned_sources)

    assert result["clean_hit_at_3"] is not None
    assert result["clean_reciprocal_rank"] is not None


def test_build_retrieval_quality_none_for_unmatched_question(tmp_path):
    doc_path = tmp_path / "sql_injection.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    result = compare_metrics.build_retrieval_quality(
        "not a real benchmark question", _clean_sources(doc_path), _clean_sources(doc_path)
    )

    assert result["clean_hit_at_3"] is None
    assert result["clean_reciprocal_rank"] is None
    assert result["poisoned_hit_at_3"] is None
    assert result["poisoned_reciprocal_rank"] is None


def test_build_generation_quality_and_attack_success_return_real_values(tmp_path, monkeypatch):
    doc_path = tmp_path / "sql_injection.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    def fake_correctness(question, reference_facts, answer):
        return {"score": 1.0 if answer == "clean answer" else 0.5, "reason": "mocked"}

    def fake_faithfulness(question, context, answer):
        return {"score": 0.9, "reason": "mocked"}

    monkeypatch.setattr(compare_metrics, "evaluate_correctness", fake_correctness)
    monkeypatch.setattr(compare_metrics, "evaluate_faithfulness", fake_faithfulness)

    question = "How does a SQL injection attack work?"
    clean_sources = _clean_sources(doc_path)
    poisoned_sources = _clean_sources(doc_path)

    generation_quality = compare_metrics.build_generation_quality(
        question, "clean answer", "poisoned answer", clean_sources, poisoned_sources
    )

    assert generation_quality["clean_answer_correctness"] == 1.0
    assert generation_quality["poisoned_answer_correctness"] == 0.5

    retrieval_quality = compare_metrics.build_retrieval_quality(
        question, clean_sources, poisoned_sources
    )
    attack_success = compare_metrics.build_attack_success(retrieval_quality, generation_quality)

    assert attack_success["rag_attack_success"] is not None
    assert attack_success["correctness_drop"] == 0.5
