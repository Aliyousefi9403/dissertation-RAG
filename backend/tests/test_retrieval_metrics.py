import pytest

from app.evaluation import retrieval_metrics as rm
from app.evaluation.retrieval_metrics import (
    find_ground_truth,
    hit_at_3_and_reciprocal_rank,
    load_questions,
)

SAMPLE_DOC = """# Sample Attack

## Attack description

This attack does something bad to the target and consumes resources.

## Detection indicators

Detection content is not automatically inferred.
"""


def _make_source(doc_path, start_index, content, attack_type="sample"):
    return {
        "source": str(doc_path),
        "content": content,
        "metadata": {
            "source": str(doc_path),
            "start_index": start_index,
            "attack_type": attack_type,
        },
    }


def test_hit_at_3_matches_on_section_overlap_not_substring(tmp_path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    description_offset = SAMPLE_DOC.index("This attack does something bad")
    chunk_content = "This attack does something bad to the target and consumes resources."

    sources = [_make_source(doc_path, description_offset, chunk_content)]

    hit, reciprocal_rank = hit_at_3_and_reciprocal_rank(sources, "sample", ["attack_description"])
    assert hit == 1
    assert reciprocal_rank == 1.0


def test_hit_at_3_rejects_wrong_section(tmp_path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    detection_offset = SAMPLE_DOC.index("Detection content is not")
    chunk_content = "Detection content is not automatically inferred."

    sources = [_make_source(doc_path, detection_offset, chunk_content)]

    hit, reciprocal_rank = hit_at_3_and_reciprocal_rank(sources, "sample", ["attack_description"])
    assert hit == 0
    assert reciprocal_rank == 0.0


def test_hit_at_3_rejects_wrong_attack_type(tmp_path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    description_offset = SAMPLE_DOC.index("This attack does something bad")
    chunk_content = "This attack does something bad to the target and consumes resources."

    sources = [_make_source(doc_path, description_offset, chunk_content, attack_type="other")]

    hit, _ = hit_at_3_and_reciprocal_rank(sources, "sample", ["attack_description"])
    assert hit == 0


def test_reciprocal_rank_by_position(tmp_path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    description_offset = SAMPLE_DOC.index("This attack does something bad")
    chunk_content = "This attack does something bad to the target and consumes resources."
    relevant = _make_source(doc_path, description_offset, chunk_content)
    irrelevant = _make_source(doc_path, 0, "# Sample Attack", attack_type="other")

    sources = [irrelevant, irrelevant, relevant]
    hit, reciprocal_rank = hit_at_3_and_reciprocal_rank(sources, "sample", ["attack_description"])
    assert hit == 1
    assert reciprocal_rank == pytest.approx(1 / 3, rel=1e-3)


def test_poison_hit_at_3_uses_section_metadata_not_pure_text_overlap(tmp_path, monkeypatch):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    monkeypatch.setattr(
        rm,
        "get_successful_entries_by_file",
        lambda: {
            "sample.md": [
                {"section": "attack description", "adversarial_text": "irrelevant text"}
            ]
        },
    )
    monkeypatch.setattr(rm, "_relative_poisoned_path", lambda path: "sample.md")

    description_offset = SAMPLE_DOC.index("This attack does something bad")
    genuine = _make_source(
        doc_path,
        description_offset,
        "This attack does something bad to the target and consumes resources.",
    )

    detection_offset = SAMPLE_DOC.index("Detection content is not")
    not_genuine = _make_source(
        doc_path, detection_offset, "Detection content is not automatically inferred."
    )

    genuine_result = rm.poison_hit_at_3([genuine])
    assert genuine_result["poison_hit_at_3"] == 1
    assert genuine_result["poisoned_chunk_ranks"] == [1]

    not_genuine_result = rm.poison_hit_at_3([not_genuine])
    assert not_genuine_result["poison_hit_at_3"] == 0


def test_questions_file_has_12_entries_with_expected_sections():
    questions = load_questions()
    assert len(questions) == 12
    for item in questions:
        assert isinstance(item["expected_sections"], list)
        assert item["expected_sections"]


def test_find_ground_truth_exact_match():
    ground_truth = find_ground_truth("How does a SQL injection attack work?")
    assert ground_truth is not None
    assert ground_truth["expected_attack_type"] == "sql_injection"

    assert find_ground_truth("not a real question") is None


def test_find_ground_truth_tolerates_harmless_formatting_differences():
    canonical = "How does a SQL injection attack work?"

    # leading/trailing whitespace + case (already supported before this fix)
    assert find_ground_truth(f"  {canonical.upper()}  ") is not None

    # doubled/irregular internal whitespace
    doubled_internal_space = "How does  a SQL injection   attack work?"
    result = find_ground_truth(doubled_internal_space)
    assert result is not None
    assert result["expected_attack_type"] == "sql_injection"

    # non-breaking space (U+00A0) in place of a regular space, and a tab
    nbsp_variant = canonical.replace(" attack", " attack")
    result = find_ground_truth(nbsp_variant)
    assert result is not None
    assert result["expected_attack_type"] == "sql_injection"

    tab_variant = canonical.replace(" ", "\t", 1)
    result = find_ground_truth(tab_variant)
    assert result is not None
    assert result["expected_attack_type"] == "sql_injection"


def test_find_ground_truth_still_rejects_genuinely_different_questions():
    # A missing trailing "?" is a content difference, not formatting --
    # must not match (matching stays strict, not fuzzy).
    assert find_ground_truth("How does a SQL injection attack work") is None
    assert find_ground_truth("How does XSS work?") is None
