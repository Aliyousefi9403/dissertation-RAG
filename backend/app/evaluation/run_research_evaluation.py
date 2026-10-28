"""Aggregate research-evaluation script."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from statistics import mean
from typing import Any, Optional

from app.config import PROJECT_ROOT
from app.evaluation.compare_metrics import build_attack_success
from app.evaluation.llm_judge import evaluate_correctness, evaluate_faithfulness
from app.evaluation.paired_metrics import build_paired_metrics, classify_score
from app.evaluation.pwws_manifest import get_summary, load_manifest
from app.evaluation.retrieval_metrics import (
    hit_at_3_and_reciprocal_rank,
    load_questions,
    poison_hit_at_3,
)
from app.generation.rag_chain import answer_question
from app.ingestion.section_metadata import section_for_offset

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "evaluation" / "research_evaluation_report.json"


def _pwws_surrogate_asr() -> Optional[float]:
    """Fraction of attacked manifest sections where PWWS actually fooled the
    surrogate classifier -- distinct from `rag_attack_success_rate`, which
    measures whether the attack fools the RAG pipeline end-to-end."""
    manifest = load_manifest()
    if not manifest:
        return None
    successes = sum(1 for entry in manifest if entry.get("success"))
    return round(successes / len(manifest), 4)


def _context_block(sources: list[dict[str, Any]]) -> str:
    parts = [
        f"[Source {position}]\n{source.get('content', '')}"
        for position, source in enumerate(sources, start=1)
    ]
    return "\n\n".join(parts)


def _mean_or_none(values: list[float]) -> Optional[float]:
    return round(mean(values), 4) if values else None


def _describe_top3(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-question audit trail: which attack_type/section each retrieved
    Top-3 chunk resolves to, for spotting questions where the clean KB
    itself has no relevant evidence to retrieve."""
    described = []
    for source in sources[:3]:
        metadata = source.get("metadata", {}) or {}
        source_path = source.get("source") or metadata.get("source") or ""
        described.append(
            {
                "attack_type": metadata.get("attack_type") or source.get("attack_type"),
                "section": section_for_offset(source_path, metadata.get("start_index")),
            }
        )
    return described


def run_evaluation() -> dict[str, Any]:
    questions = load_questions()

    clean_hits: list[int] = []
    poisoned_hits: list[int] = []
    clean_rrs: list[float] = []
    poisoned_rrs: list[float] = []
    poison_hits: list[int] = []
    clean_correctness_scores: list[float] = []
    poisoned_correctness_scores: list[float] = []
    clean_faithfulness_scores: list[float] = []
    poisoned_faithfulness_scores: list[float] = []
    rag_attack_successes: list[bool] = []
    per_question: list[dict[str, Any]] = []
    score_observations: list[dict[str, Any]] = []

    for item in questions:
        question = item["question"]
        expected_attack_type = item["expected_attack_type"]
        expected_sections = item.get("expected_sections", [])
        reference_facts = item.get("reference_facts", [])

        logger.info("Evaluating question: %s", question)

        clean = answer_question(question, system_state="clean")
        poisoned = answer_question(question, system_state="poisoned")

        clean_sources = clean.get("sources", [])
        poisoned_sources = poisoned.get("sources", [])
        clean_answer = (clean.get("answer") or "").strip()
        poisoned_answer = (poisoned.get("answer") or "").strip()

        clean_hit, clean_rr = hit_at_3_and_reciprocal_rank(
            clean_sources, expected_attack_type, expected_sections
        )
        poisoned_hit, poisoned_rr = hit_at_3_and_reciprocal_rank(
            poisoned_sources, expected_attack_type, expected_sections
        )
        clean_hits.append(clean_hit)
        poisoned_hits.append(poisoned_hit)
        clean_rrs.append(clean_rr)
        poisoned_rrs.append(poisoned_rr)

        poison = poison_hit_at_3(poisoned_sources)
        poison_hits.append(poison["poison_hit_at_3"])

        clean_correctness_result = evaluate_correctness(question, reference_facts, clean_answer)
        poisoned_correctness_result = evaluate_correctness(
            question, reference_facts, poisoned_answer
        )
        clean_faithfulness_result = evaluate_faithfulness(
            question, _context_block(clean_sources), clean_answer
        )
        poisoned_faithfulness_result = evaluate_faithfulness(
            question, _context_block(poisoned_sources), poisoned_answer
        )

        # Preserve raw values for missing/malformed accounting before
        # normalising unavailable scores for the existing downstream code.
        raw_scores = {
            "clean_answer_correctness": (clean_correctness_result or {}).get("score"),
            "poisoned_answer_correctness": (poisoned_correctness_result or {}).get("score"),
            "clean_faithfulness": (clean_faithfulness_result or {}).get("score"),
            "poisoned_faithfulness": (poisoned_faithfulness_result or {}).get("score"),
        }
        score_observations.append(raw_scores)
        clean_correctness = classify_score(raw_scores["clean_answer_correctness"])[0]
        poisoned_correctness = classify_score(raw_scores["poisoned_answer_correctness"])[0]
        clean_faithfulness = classify_score(raw_scores["clean_faithfulness"])[0]
        poisoned_faithfulness = classify_score(raw_scores["poisoned_faithfulness"])[0]

        if clean_correctness is not None:
            clean_correctness_scores.append(clean_correctness)
        if poisoned_correctness is not None:
            poisoned_correctness_scores.append(poisoned_correctness)
        if clean_faithfulness is not None:
            clean_faithfulness_scores.append(clean_faithfulness)
        if poisoned_faithfulness is not None:
            poisoned_faithfulness_scores.append(poisoned_faithfulness)

        attack_success = build_attack_success(
            retrieval_quality={"poison_hit_at_3": poison["poison_hit_at_3"]},
            generation_quality={
                "clean_answer_correctness": clean_correctness,
                "poisoned_answer_correctness": poisoned_correctness,
            },
        )
        if attack_success["rag_attack_success"] is not None:
            rag_attack_successes.append(attack_success["rag_attack_success"])

        per_question.append(
            {
                "id": item.get("id"),
                "question": question,
                "expected_attack_type": expected_attack_type,
                "expected_sections": expected_sections,
                "clean_hit_at_3": clean_hit,
                "clean_reciprocal_rank": clean_rr,
                "poisoned_hit_at_3": poisoned_hit,
                "poisoned_reciprocal_rank": poisoned_rr,
                "poison_hit_at_3": poison["poison_hit_at_3"],
                "poisoned_chunks_in_top_3": poison["poisoned_chunks_in_top_3"],
                "clean_answer_correctness": clean_correctness,
                "poisoned_answer_correctness": poisoned_correctness,
                "clean_faithfulness": clean_faithfulness,
                "poisoned_faithfulness": poisoned_faithfulness,
                "rag_attack_success": attack_success["rag_attack_success"],
                "clean_top_3": _describe_top3(clean_sources),
                "poisoned_top_3": _describe_top3(poisoned_sources),
            }
        )

    manifest_summary = get_summary()

    aggregate = {
        "question_count": len(questions),
        "clean_hit_at_3_rate": _mean_or_none(clean_hits),
        "poisoned_hit_at_3_rate": _mean_or_none(poisoned_hits),
        "clean_mrr": _mean_or_none(clean_rrs),
        "poisoned_mrr": _mean_or_none(poisoned_rrs),
        "poison_hit_at_3_rate": _mean_or_none(poison_hits),
        "mean_semantic_similarity": (
            manifest_summary.get("mean_semantic_similarity") if manifest_summary else None
        ),
        "mean_modification_rate": (
            manifest_summary.get("mean_modification_rate") if manifest_summary else None
        ),
        "mean_clean_correctness": _mean_or_none(clean_correctness_scores),
        "mean_poisoned_correctness": _mean_or_none(poisoned_correctness_scores),
        "mean_clean_faithfulness": _mean_or_none(clean_faithfulness_scores),
        "mean_poisoned_faithfulness": _mean_or_none(poisoned_faithfulness_scores),
        "rag_attack_success_rate": (
            _mean_or_none([1.0 if success else 0.0 for success in rag_attack_successes])
            if rag_attack_successes
            else None
        ),
        "pwws_surrogate_asr": _pwws_surrogate_asr(),
    }

    return {
        "aggregate": aggregate,
        "per_question": per_question,
        "paired_metrics": build_paired_metrics(score_observations),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    report = run_evaluation()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
