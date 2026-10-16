from app.ingestion.section_metadata import (
    normalize_heading,
    section_for_offset,
    sections_overlapping,
)

SAMPLE_DOC = """# Sample Attack

## Metadata

- Attack key: `sample`

## Attack description

This attack does something bad to the target.

## Detection indicators

Detection content is not automatically inferred.

## Prevention and mitigation

Mitigation guidance is limited to mapped sources.
"""


def test_normalize_heading_matches_spec_examples():
    assert normalize_heading("Prevention and mitigation") == "prevention_mitigation"
    assert normalize_heading("Detection indicators") == "detection_indicators"


def test_normalize_heading_strips_punctuation_and_is_idempotent():
    assert normalize_heading("ATT&CK adversary context") == "attck_adversary_context"
    assert normalize_heading("attack_description") == "attack_description"


def test_section_for_offset_resolves_enclosing_heading():
    detection_offset = SAMPLE_DOC.index("Detection content")
    assert section_for_offset(__file__, detection_offset) is None  # wrong file, sanity check


def test_section_for_offset_with_real_document(tmp_path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    description_offset = SAMPLE_DOC.index("This attack does something bad")
    detection_offset = SAMPLE_DOC.index("Detection content is not")

    assert section_for_offset(str(doc_path), description_offset) == "attack_description"
    assert section_for_offset(str(doc_path), detection_offset) == "detection_indicators"
    assert section_for_offset(str(doc_path), None) is None


def test_sections_overlapping_covers_multi_section_chunk(tmp_path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

    # A chunk starting at offset 0 spans the title through part of
    # "Attack description" -- short documents/large chunk sizes make this
    # the common case, which is why relevance checks use overlap, not a
    # single start-offset section.
    end_of_description = SAMPLE_DOC.index("## Detection indicators")
    overlap = sections_overlapping(str(doc_path), 0, end_of_description)

    assert "attack_description" in overlap
    assert "detection_indicators" not in overlap


def test_sections_overlapping_empty_when_unresolvable():
    assert sections_overlapping("/nonexistent/file.md", 0, 10) == set()
    assert sections_overlapping("/nonexistent/file.md", None, 10) == set()
