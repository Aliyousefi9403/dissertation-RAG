"""Pure paired accounting for correctness and faithfulness."""

from __future__ import annotations

import math
from statistics import mean
from typing import Any, Literal


def classify_score(
    value: Any,
) -> tuple[int | float | None, Literal["valid", "missing", "malformed"]]:
    """Keep valid scores unchanged; classify unavailable values explicitly."""
    if value is None:
        return None, "missing"
    if type(value) is int or (type(value) is float and math.isfinite(value)):
        return value, "valid"
    return None, "malformed"


def _summarize_metric(
    observations: list[dict[str, Any]], clean_key: str, poisoned_key: str
) -> dict[str, Any]:
    summary = {
        "total_observations": len(observations),
        "clean_valid_count": 0,
        "poisoned_valid_count": 0,
        "paired_valid_count": 0,
        "clean_only_unavailable_count": 0,
        "poisoned_only_unavailable_count": 0,
        "both_unavailable_count": 0,
        "clean_missing_count": 0,
        "clean_malformed_count": 0,
        "poisoned_missing_count": 0,
        "poisoned_malformed_count": 0,
    }
    paired_clean: list[int | float] = []
    paired_poisoned: list[int | float] = []
    deltas: list[int | float] = []

    for observation in observations:
        clean, clean_status = classify_score(observation.get(clean_key))
        poisoned, poisoned_status = classify_score(observation.get(poisoned_key))
        summary[f"clean_{clean_status}_count"] += 1
        summary[f"poisoned_{poisoned_status}_count"] += 1

        if clean is not None and poisoned is not None:
            summary["paired_valid_count"] += 1
            paired_clean.append(clean)
            paired_poisoned.append(poisoned)
            deltas.append(poisoned - clean)
        elif clean is None and poisoned is not None:
            summary["clean_only_unavailable_count"] += 1
        elif poisoned is None and clean is not None:
            summary["poisoned_only_unavailable_count"] += 1
        else:
            summary["both_unavailable_count"] += 1

    return {
        **summary,
        "paired_clean_mean": round(mean(paired_clean), 4) if paired_clean else None,
        "paired_poisoned_mean": round(mean(paired_poisoned), 4) if paired_poisoned else None,
        "mean_delta": round(mean(deltas), 4) if deltas else None,
    }


def build_paired_metrics(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize raw same-question score rows without mutating them."""
    return {
        "schema_version": 1,
        "delta_direction": "poisoned_minus_clean",
        "correctness": _summarize_metric(
            observations, "clean_answer_correctness", "poisoned_answer_correctness"
        ),
        "faithfulness": _summarize_metric(
            observations, "clean_faithfulness", "poisoned_faithfulness"
        ),
    }
