"""PWWS attack manifest analysis."""

from __future__ import annotations

import json
import statistics
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from app.config import PROJECT_ROOT
from app.vectorstore.qdrant_store import get_embeddings

MANIFEST_FILE = PROJECT_ROOT / "data" / "poisoned" / "pwws_attack_manifest.jsonl"
METRICS_FILE = PROJECT_ROOT / "data" / "poisoned" / "pwws_attack_manifest_metrics.jsonl"
SUMMARY_FILE = PROJECT_ROOT / "data" / "poisoned" / "pwws_attack_manifest_summary.json"


def load_manifest() -> list[dict[str, Any]]:
    if not MANIFEST_FILE.exists():
        return []

    entries = []
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def word_modification_rate(original: str, adversarial: str) -> tuple[int, int, float]:
    """Changed words / original words, compared with difflib.SequenceMatcher."""
    import difflib

    original_words = original.split()
    adversarial_words = adversarial.split()

    original_word_count = len(original_words)
    if original_word_count == 0:
        return 0, 0, 0.0

    matcher = difflib.SequenceMatcher(None, original_words, adversarial_words)
    changed_word_count = sum(
        (i2 - i1)
        for tag, i1, i2, _j1, _j2 in matcher.get_opcodes()
        if tag in ("replace", "delete")
    )

    rate = changed_word_count / original_word_count
    return original_word_count, changed_word_count, rate


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.asarray(vec_a, dtype=np.float64)
    b = np.asarray(vec_b, dtype=np.float64)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def enrich_manifest_and_summarize() -> dict[str, Any]:
    """Compute word_modification_rate + semantic_similarity for every successful
    manifest entry and write the two sidecar files.
    """
    entries = load_manifest()
    successful = [e for e in entries if e.get("success") and e.get("original_text") and e.get("adversarial_text")]

    if not successful:
        summary = {
            "sections_total": len(entries),
            "sections_successful": 0,
            "mean_modification_rate": None,
            "median_modification_rate": None,
            "mean_semantic_similarity": None,
            "median_semantic_similarity": None,
        }
        SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        METRICS_FILE.write_text("", encoding="utf-8")
        return summary

    # Batch-embed all original + adversarial texts in one call (MiniLM,
    # same model/instance used for retrieval — no second embedding model).
    embeddings = get_embeddings()
    originals = [e["original_text"] for e in successful]
    adversarials = [e["adversarial_text"] for e in successful]
    original_vecs = embeddings.embed_documents(originals)
    adversarial_vecs = embeddings.embed_documents(adversarials)

    enriched: list[dict[str, Any]] = []
    modification_rates: list[float] = []
    similarities: list[float] = []

    for entry, orig_vec, adv_vec in zip(successful, original_vecs, adversarial_vecs):
        original_word_count, changed_word_count, rate = word_modification_rate(
            entry["original_text"], entry["adversarial_text"]
        )
        similarity = _cosine_similarity(orig_vec, adv_vec)

        modification_rates.append(rate)
        similarities.append(similarity)

        enriched.append(
            {
                "file": entry.get("file"),
                "attack_type": entry.get("attack_type"),
                "section": entry.get("section"),
                "original_word_count": original_word_count,
                "changed_word_count": changed_word_count,
                "modification_rate": round(rate, 4),
                "semantic_similarity": round(similarity, 4),
            }
        )

    with METRICS_FILE.open("w", encoding="utf-8") as f:
        for row in enriched:
            f.write(json.dumps(row) + "\n")

    summary = {
        "sections_total": len(entries),
        "sections_successful": len(successful),
        "mean_modification_rate": round(statistics.mean(modification_rates), 4),
        "median_modification_rate": round(statistics.median(modification_rates), 4),
        "mean_semantic_similarity": round(statistics.mean(similarities), 4),
        "median_semantic_similarity": round(statistics.median(similarities), 4),
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


@lru_cache(maxsize=1)
def get_summary() -> dict[str, Any] | None:
    """Cached read of the precomputed summary (attack_quality block for
    /compare — dataset-wide, so it never needs recomputing per request)."""
    if not SUMMARY_FILE.exists():
        return None
    return json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_successful_entries_by_file() -> dict[str, list[dict[str, Any]]]:
    """Cached lookup: relative poisoned-KB file path -> list of successful manifest
    entries for that file.
    """
    by_file: dict[str, list[dict[str, Any]]] = {}
    for entry in load_manifest():
        if entry.get("success") and entry.get("adversarial_text"):
            by_file.setdefault(entry["file"], []).append(entry)
    return by_file


if __name__ == "__main__":
    result = enrich_manifest_and_summarize()
    print(json.dumps(result, indent=2))
