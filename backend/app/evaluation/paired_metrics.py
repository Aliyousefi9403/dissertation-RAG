"""Pure paired accounting for correctness and faithfulness (schema version 1).

Each observation holds both conditions for the same question. Metrics use
their own valid pairs; scores are never filtered and zipped independently.
Delta is poisoned minus clean, computed per pair before any rounding.

None or an absent score is missing. Non-finite floats and types other than
built-in int/float (including bool) are malformed. Both are unavailable for
pairing, but condition-specific missing/malformed counts remain separate.
These statuses describe values, not unrecorded evaluator failure reasons.

For each metric, the counts satisfy:
  total_observations = paired_valid_count + clean_only_unavailable_count
                       + poisoned_only_unavailable_count + both_unavailable_count
  total_observations = clean_valid_count + clean_missing_count + clean_malformed_count
  total_observations = poisoned_valid_count + poisoned_missing_count
                       + poisoned_malformed_count

clean_only_unavailable_count means clean is unavailable and poisoned is
valid; poisoned_only_unavailable_count means the reverse. Total counts
supplied observations, not requests that failed before a row was created.
No score coercion, clipping, range restriction, I/O, or model calls occur.
"""

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
    """Summarize raw same-question score rows without mutating them.

    All three paired summaries are None when a metric has no valid pairs.
    Correctness availability never filters faithfulness, or vice versa.
    """
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
