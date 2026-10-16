"""
Retrieval-quality metrics (dissertation Phase 2):

- Poison Hit@3: does a genuinely PWWS-modified chunk reach the poisoned
  Top-3 context handed to the LLM?
- Hit@3 / Recall@3 and Mean Reciprocal Rank against a hand-curated
  ground-truth question set (backend/data/evaluation/questions.json).

Relevance for Hit@3/RR and PWWS-genuineness is metadata-based: retrieved
chunks are resolved to a stable `section` slug via
app.ingestion.section_metadata (heading structure of the source file +
the chunk's own `start_index`/content span), not via literal substring
matching of an expected phrase against chunk content. This is robust to
HTML-table content, chunk-boundary splits, and phrasing differences that
broke the previous substring-based check.

All functions are pure/query-time -- no Qdrant writes, no attack re-runs,
no changes to the live collections.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from app.config import PROJECT_ROOT, get_knowledge_base_path
from app.evaluation.pwws_manifest import get_successful_entries_by_file
from app.ingestion.section_metadata import normalize_heading, sections_overlapping

QUESTIONS_FILE = PROJECT_ROOT / "data" / "evaluation" / "questions.json"

# Unicode-aware: also collapses non-breaking spaces, tabs, and other
# whitespace variants that plain str.split()/.strip() alone would miss.
_QUESTION_WHITESPACE_RE = re.compile(r"\s+")

# Fallback only (used when section metadata cannot be resolved, e.g. the
# source file is unreadable at evaluation time): the share of a retrieved
# chunk's own words that must also appear in a successful manifest entry's
# adversarial_text for the same file to treat it as a content-based match.
_OVERLAP_THRESHOLD = 0.6


def _relative_poisoned_path(source_path: str) -> str:
    """Best-effort "ddos/http_flood.md"-style relative path, matching the
    manifest's own `file` field, from a chunk's absolute/loaded source
    path."""
    try:
        poisoned_root = get_knowledge_base_path("poisoned")
        return str(Path(source_path).resolve().relative_to(poisoned_root.resolve()))
    except (ValueError, OSError):
        # Fallback: last two path segments (e.g. "ddos/http_flood.md"),
        # robust even if the stored path was relativized differently.
        parts = Path(source_path).parts
        return "/".join(parts[-2:]) if len(parts) >= 2 else source_path


def _text_overlap_ratio(chunk_text: str, section_text: str) -> float:
    chunk_words = set(chunk_text.lower().split())
    if not chunk_words:
        return 0.0
    section_words = set(section_text.lower().split())
    return len(chunk_words & section_words) / len(chunk_words)


def _is_genuine_pwws_chunk(source: dict[str, Any]) -> Optional[str]:
    """Returns the matching section name if `source` is genuinely
    PWWS-modified content, else None.

    Primary rule (metadata-based): the retrieved chunk's own byte range
    (`start_index` .. `start_index + len(content)`, resolved against the
    source file's heading structure) overlaps a section the manifest
    records as a *successful* PWWS perturbation for that file -- this is
    what stops an unmodified chunk from an otherwise-poisoned-collection
    file being counted as poisoned just because it lives in the poisoned
    collection (`get_successful_entries_by_file()` already restricts
    candidates to `success: true` manifest entries).

    Fallback (only when section metadata cannot be resolved): the original
    content-similarity check against the manifest's `adversarial_text`.
    """
    metadata = source.get("metadata", {}) or {}
    source_path = source.get("source") or metadata.get("source") or ""
    relative_path = _relative_poisoned_path(source_path)

    entries = get_successful_entries_by_file().get(relative_path, [])
    if not entries:
        return None

    content = (source.get("content") or "").strip()
    if not content:
        return None

    start_index = metadata.get("start_index")
    overlapping_sections = sections_overlapping(source_path, start_index, len(content))

    for entry in entries:
        entry_section = normalize_heading(entry.get("section", ""))

        if overlapping_sections:
            if entry_section in overlapping_sections:
                return entry.get("section")
            continue

        adversarial_text = entry.get("adversarial_text", "")
        normalized_adv = " ".join(adversarial_text.split())
        normalized_chunk = " ".join(content.split())

        if normalized_chunk in normalized_adv or normalized_adv in normalized_chunk:
            return entry.get("section")

        if _text_overlap_ratio(normalized_chunk, normalized_adv) >= _OVERLAP_THRESHOLD:
            return entry.get("section")

    return None


def poison_hit_at_3(poisoned_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Poison Hit@3 = 1 if at least one of the (up to 3) poisoned-side
    retrieved chunks is genuinely PWWS-modified content, else 0.
    """
    top3 = poisoned_sources[:3]
    poisoned_chunks_in_top_3 = 0
    poisoned_chunk_ranks: list[int] = []

    for rank, source in enumerate(top3, start=1):
        section = _is_genuine_pwws_chunk(source)
        if section is not None:
            poisoned_chunks_in_top_3 += 1
            poisoned_chunk_ranks.append(rank)

    return {
        "poison_hit_at_3": 1 if poisoned_chunks_in_top_3 > 0 else 0,
        "poisoned_chunks_in_top_3": poisoned_chunks_in_top_3,
        "poisoned_chunk_ranks": poisoned_chunk_ranks,
    }


@lru_cache(maxsize=1)
def load_questions() -> list[dict[str, Any]]:
    if not QUESTIONS_FILE.exists():
        return []
    return json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))


def _normalize_question_text(text: str) -> str:
    """Lowercase, trim ends, and collapse repeated/Unicode whitespace to a
    single space. Still a strict equality check afterwards -- no fuzzy or
    semantic matching, just harmless-formatting tolerance."""
    return _QUESTION_WHITESPACE_RE.sub(" ", text.strip().lower())


def find_ground_truth(question: str) -> Optional[dict[str, Any]]:
    """Exact (case/whitespace-insensitive) match against questions.json.
    Deliberately not fuzzy -- a small, hand-curated question set should be
    matched precisely rather than guessed at."""
    normalized = _normalize_question_text(question)
    for item in load_questions():
        if _normalize_question_text(item["question"]) == normalized:
            return item
    return None


def hit_at_3_and_reciprocal_rank(
    sources: list[dict[str, Any]],
    expected_attack_type: str,
    expected_sections: list[str],
) -> tuple[int, float]:
    """
    Hit@3 = 1 if relevant expected evidence appears anywhere in the top 3
    sources, else 0. Relevance is judged entirely on stable retrieval
    metadata: `attack_type` must match, AND the chunk's resolved section
    (its byte range mapped onto the source file's heading structure --
    see app.ingestion.section_metadata) must overlap one of
    `expected_sections`. No literal heading-text substring check against
    chunk content is performed.

    `expected_sections` may list more than one normalized section slug --
    the KB may use a different heading name for the same concept across
    files, or (for a couple of attack types) lack a dedicated section
    entirely, in which case the caller points at the section that
    actually contains the relevant sentence (documented per-question).

    Reciprocal rank: 1/rank of the first relevant hit (1.0, 0.5, 0.3333),
    or 0.0 if not found in the top 3.
    """
    normalized_expected = {normalize_heading(section) for section in expected_sections}
    top3 = sources[:3]

    for rank, source in enumerate(top3, start=1):
        metadata = source.get("metadata", {}) or {}
        attack_type = metadata.get("attack_type") or source.get("attack_type")

        if attack_type != expected_attack_type:
            continue

        if normalized_expected:
            source_path = source.get("source") or metadata.get("source") or ""
            content = source.get("content") or ""
            overlapping_sections = sections_overlapping(
                source_path, metadata.get("start_index"), len(content)
            )
            if not overlapping_sections & normalized_expected:
                # attack_type matches but this particular chunk's resolved
                # section(s) don't cover any expected section -- keep
                # looking at lower ranks rather than counting a
                # same-document-wrong-section chunk as a hit.
                continue

        return 1, round(1.0 / rank, 4)

    return 0, 0.0
