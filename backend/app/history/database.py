"""Lightweight SQLite persistence for the Experiment History feature."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import PROJECT_ROOT

DB_PATH = PROJECT_ROOT / "data" / "aegisrag_history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    question TEXT NOT NULL,
    mode TEXT NOT NULL,
    attack_method TEXT,

    clean_answer TEXT,
    poisoned_answer TEXT,
    defended_answer TEXT,

    clean_sources TEXT,
    poisoned_sources TEXT,
    defended_sources TEXT,

    clean_top_score REAL,
    poisoned_top_score REAL,
    defended_top_score REAL,

    retrieval_shift REAL,
    top_k_overlap REAL,
    top_score_delta REAL,
    shared_chunks INTEGER,
    answer_changed INTEGER,

    clean_latency REAL,
    poisoned_latency REAL,
    defended_latency REAL,

    metadata TEXT
);
"""

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_experiments_mode ON experiments(mode);",
    "CREATE INDEX IF NOT EXISTS idx_experiments_timestamp ON experiments(timestamp);",
)

# Columns added after the initial schema above.
_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("research_metrics", "ALTER TABLE experiments ADD COLUMN research_metrics TEXT"),
)


def _run_migrations(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(experiments)")
    }
    for column_name, statement in _MIGRATIONS:
        if column_name not in existing_columns:
            connection.execute(statement)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(_SCHEMA)
        for statement in _INDEXES:
            connection.execute(statement)
        _run_migrations(connection)


init_db()
