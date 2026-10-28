"""Lexical cross-state document identity and document overlap, schema version 1."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePath, PurePosixPath
from typing import Any

CYBERSECURITY_DATASET_NAMESPACE = "aegisrag.cybersecurity"

DocumentIdentity = tuple[str, str]
CorpusRoots = Mapping[str | PurePath, str]


def _absolute_path(value: Any) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.anchor != "/" or ".." in path.parts:
        return None
    return path


def _identity_for_path(value: Any, corpus_roots: CorpusRoots) -> DocumentIdentity | None:
    path = _absolute_path(value)
    if path is None or value.endswith("/"):
        return None
    matches: list[DocumentIdentity] = []
    for root, namespace in corpus_roots.items():
        root_path = _absolute_path(str(root))
        if root_path is None or not isinstance(namespace, str) or not namespace.strip():
            continue
        if path == root_path:
            return None  # A corpus root itself is not a document.
        if path.is_relative_to(root_path):
            matches.append((namespace, path.relative_to(root_path).as_posix()))
    # Even nested roots in the same namespace are ambiguous: the relative
    # document path depends on which root was chosen.
    return matches[0] if len(matches) == 1 else None


def resolve_document_identity(
    source: Mapping[str, Any], *, corpus_roots: CorpusRoots
) -> DocumentIdentity | None:
    """Resolve both supplied source paths, requiring agreement when both exist."""
    if not isinstance(source, Mapping):
        return None
    metadata = source.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        return None
    identities = []
    for value in (source.get("source"), metadata.get("source")):
        if value is None or value == "":
            continue
        identity = _identity_for_path(value, corpus_roots)
        if identity is None:
            return None
        identities.append(identity)
    if not identities or any(identity != identities[0] for identity in identities):
        return None
    return identities[0]


def _documents_and_unknown_count(
    sources: list[dict[str, Any]], corpus_roots: CorpusRoots
) -> tuple[set[DocumentIdentity], int]:
    documents: set[DocumentIdentity] = set()
    unknown = 0
    for source in sources:
        identity = resolve_document_identity(source, corpus_roots=corpus_roots)
        if identity is None:
            unknown += 1
        else:
            documents.add(identity)
    return documents, unknown


def build_document_overlap(
    clean_sources: list[dict[str, Any]],
    poisoned_sources: list[dict[str, Any]],
    *,
    corpus_roots: CorpusRoots,
) -> dict[str, Any]:
    """Deduplicate all returned sources by document."""
    clean, clean_unknown = _documents_and_unknown_count(clean_sources, corpus_roots)
    poisoned, poisoned_unknown = _documents_and_unknown_count(poisoned_sources, corpus_roots)
    shared = clean & poisoned
    union = clean | poisoned
    if not clean_sources and not poisoned_sources:
        status = "both_empty"
    elif clean_unknown or poisoned_unknown:
        status = "unknown_identity"
    else:
        status = "ok"
    return {
        "schema_version": 1,
        "status": status,
        "jaccard": round(len(shared) / len(union), 4) if status == "ok" else None,
        "clean_source_count": len(clean_sources),
        "poisoned_source_count": len(poisoned_sources),
        "clean_unknown_source_count": clean_unknown,
        "poisoned_unknown_source_count": poisoned_unknown,
        "clean_known_document_count": len(clean),
        "poisoned_known_document_count": len(poisoned),
        "known_shared_document_count": len(shared),
        "known_union_document_count": len(union),
    }
