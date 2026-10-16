"""
Derives a stable, snake_case "section" identity for a knowledge-base
Markdown chunk from the `##` heading structure of its source file --
instead of relying on literal substring matching of chunk content against
an expected phrase (the old approach in app/evaluation/retrieval_metrics.py,
which broke on HTML-table content, chunk-boundary splits, and phrasing
differences).

Shared by:
- app/ingestion/load_documents.py -- tags `chunk.metadata["section"]` for
  any FUTURE re-ingestion. Not applied to the live Qdrant collections; no
  re-ingestion is run as part of adding this module.
- app/evaluation/retrieval_metrics.py -- resolves section for an
  already-retrieved chunk at query time, purely by re-reading its source
  `.md` file (read-only) and mapping `start_index` (already stored in the
  Qdrant payload, from RecursiveCharacterTextSplitter(add_start_index=True))
  onto the file's heading ranges. Requires no Qdrant writes.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_PUNCTUATION_RE = re.compile(r"[^\w\s-]")
_SEPARATOR_RE = re.compile(r"[\s-]+")
_STOPWORDS = {"and"}


def normalize_heading(heading: str) -> str:
    """"Prevention and mitigation" -> "prevention_mitigation";
    "Detection indicators" -> "detection_indicators". Idempotent, so it is
    also used to normalize the PWWS manifest's own `section` strings
    (already lowercase, e.g. "att&ck adversary context") onto the same
    slug space as headings parsed from the Markdown files."""
    cleaned = _PUNCTUATION_RE.sub("", heading.strip().lower())
    tokens = [token for token in _SEPARATOR_RE.split(cleaned) if token and token not in _STOPWORDS]
    return "_".join(tokens)


def _heading_ranges(text: str) -> list[tuple[int, int, str]]:
    """[(start, end, normalized_section), ...] -- every KB document in this
    project opens with a top-level `# Title` heading at offset 0, so this
    covers the whole document with no unattributed prefix."""
    matches = list(_HEADING_RE.finditer(text))
    ranges = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        ranges.append((start, end, normalize_heading(match.group(1))))
    return ranges


@lru_cache(maxsize=256)
def _read_file(path: str) -> Optional[str]:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


def section_for_offset(source_path: str, start_index: Optional[int]) -> Optional[str]:
    """Single primary section containing `start_index` -- used to tag one
    `section` value per chunk during ingestion."""
    if start_index is None or not source_path:
        return None
    text = _read_file(source_path)
    if text is None:
        return None
    for start, end, section in _heading_ranges(text):
        if start <= start_index < end:
            return section
    return None


def sections_overlapping(source_path: str, start_index: Optional[int], length: int) -> set[str]:
    """All sections whose heading range overlaps [start_index, start_index +
    length) -- used for query-time relevance checks, since a retrieved
    chunk's byte span commonly crosses more than one heading (short KB
    documents relative to chunk_size, chunk_overlap). Anchoring relevance
    on a single start-offset section would produce false negatives for
    exactly this case."""
    if start_index is None or not source_path or length <= 0:
        return set()
    text = _read_file(source_path)
    if text is None:
        return set()
    chunk_end = start_index + length
    return {
        section
        for start, end, section in _heading_ranges(text)
        if start < chunk_end and end > start_index
    }
