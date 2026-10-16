"""
CRUD operations for recorded experiments, backed by `database.py`.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.history.database import get_connection
from app.history.models import ExperimentCreate, ExperimentRecord, ExperimentStats

_JSON_FIELDS = (
    "clean_sources",
    "poisoned_sources",
    "defended_sources",
    "metadata",
    "research_metrics",
)

_COLUMNS = (
    "question",
    "mode",
    "attack_method",
    "clean_answer",
    "poisoned_answer",
    "defended_answer",
    "clean_sources",
    "poisoned_sources",
    "defended_sources",
    "clean_top_score",
    "poisoned_top_score",
    "defended_top_score",
    "retrieval_shift",
    "top_k_overlap",
    "top_score_delta",
    "shared_chunks",
    "answer_changed",
    "clean_latency",
    "poisoned_latency",
    "defended_latency",
    "metadata",
    "research_metrics",
)


def _row_to_record(row: dict[str, Any]) -> ExperimentRecord:
    data = dict(row)
    for field in _JSON_FIELDS:
        raw = data.get(field)
        data[field] = json.loads(raw) if raw is not None else None
    data["answer_changed"] = (
        bool(data["answer_changed"]) if data.get("answer_changed") is not None else None
    )
    return ExperimentRecord(**data)


def save_experiment(payload: ExperimentCreate) -> ExperimentRecord:
    timestamp = datetime.now(timezone.utc).isoformat()
    values = payload.model_dump()

    for field in _JSON_FIELDS:
        value = values.get(field)
        values[field] = json.dumps(value) if value is not None else None

    if values.get("answer_changed") is not None:
        values["answer_changed"] = int(values["answer_changed"])

    columns_sql = ", ".join(("timestamp", *_COLUMNS))
    placeholders = ", ".join(["?"] * (len(_COLUMNS) + 1))
    params = [timestamp, *(values[column] for column in _COLUMNS)]

    with get_connection() as connection:
        cursor = connection.execute(
            f"INSERT INTO experiments ({columns_sql}) VALUES ({placeholders})",
            params,
        )
        experiment_id = cursor.lastrowid

    return get_experiment(experiment_id)  # type: ignore[return-value]


def list_experiments(
    mode: Optional[str] = None,
    attack_method: Optional[str] = None,
    answer_changed: Optional[bool] = None,
    limit: int = 50,
) -> list[ExperimentRecord]:
    clauses: list[str] = []
    params: list[Any] = []

    if mode is not None:
        clauses.append("mode = ?")
        params.append(mode)
    if attack_method is not None:
        clauses.append("attack_method = ?")
        params.append(attack_method)
    if answer_changed is not None:
        clauses.append("answer_changed = ?")
        params.append(int(answer_changed))

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM experiments {where_sql} "
            "ORDER BY timestamp DESC, id DESC LIMIT ?",
            params,
        ).fetchall()

    return [_row_to_record(dict(row)) for row in rows]


def get_experiment(experiment_id: int) -> Optional[ExperimentRecord]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,),
        ).fetchone()

    return _row_to_record(dict(row)) if row is not None else None


def delete_experiment(experiment_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM experiments WHERE id = ?",
            (experiment_id,),
        )
    return cursor.rowcount > 0


def get_stats() -> ExperimentStats:
    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
        mode_rows = connection.execute(
            "SELECT mode, COUNT(*) FROM experiments GROUP BY mode"
        ).fetchall()
        changed = connection.execute(
            "SELECT COUNT(*) FROM experiments WHERE answer_changed = 1"
        ).fetchone()[0]

    counts = {mode: count for mode, count in mode_rows}

    return ExperimentStats(
        total=total,
        clean=counts.get("clean", 0),
        poisoned=counts.get("poisoned", 0),
        compare=counts.get("compare", 0),
        defended=counts.get("defended", 0),
        answer_changed=changed,
    )
