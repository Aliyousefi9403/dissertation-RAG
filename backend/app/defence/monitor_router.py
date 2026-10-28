"""Verified mode for the interface: the runtime verification monitor."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.defence import runtime_monitor as rm

router = APIRouter(tags=["runtime monitor"])

MEMORY_PATH = Path(
    os.getenv(
        "AEGIS_MONITOR_MEMORY", str(rm.BACKEND / "runtime" / "quarantine-memory.jsonl")
    )
)
SOURCE_STATE = "poisoned"


def _relative(source: str | None) -> str | None:
    if not source:
        return source
    marker = "/knowledge_base/"
    source = source.replace("\\", "/")
    return source.split(marker, 1)[1] if marker in source else source


def verified_answer(
    question: str, trusted_fallback: bool = False, *, llm_factory=None, search_fn=None
) -> dict[str, Any]:
    """Answer under the monitor; the response carries the monitor's trace for the interface."""
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")
    if llm_factory is None:
        from app.generation.llm_factory import create_llm as llm_factory
    capture: dict[str, Any] = {}
    result = rm.monitored_answer(
        question,
        SOURCE_STATE,
        memory=rm.QuarantineMemory(MEMORY_PATH),
        llm_factory=llm_factory,
        mode="restore" if trusted_fallback else "verify",
        search_fn=search_fn,
        capture=capture,
    )
    monitor = capture["monitor"]
    return {
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"],
        "system_state": "verified",
        "monitor": {**monitor, "trusted_fallback": trusted_fallback},
    }


def _entries() -> list[dict[str, Any]]:
    if not MEMORY_PATH.exists():
        return []
    out = []
    for line in MEMORY_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            e = json.loads(line)
            out.append(
                {
                    "key": e["key"][:12],
                    "source": _relative(e.get("source")),
                    "words": e.get("words", []),
                    "specs": e.get("specs", []),
                    "question": e.get("question"),
                    "round": e.get("round"),
                    "at": e.get("at"),
                }
            )
    return out


@router.get("/monitor/memory")
def monitor_memory() -> dict[str, Any]:
    entries = _entries()
    return {
        "policy_version": rm.POLICY_VERSION,
        "count": len(entries),
        "entries": entries,
    }


@router.post("/monitor/memory/reset")
def reset_monitor_memory() -> dict[str, Any]:
    archived = None
    if MEMORY_PATH.exists():
        target = MEMORY_PATH.with_name(
            f"{MEMORY_PATH.stem}-archived-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
        )
        MEMORY_PATH.rename(target)
        archived = target.name
    return {"archived": archived, "count": 0}
