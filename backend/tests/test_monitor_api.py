"""API tests for Verified mode, the monitor memory endpoints and the optional rate limit (ADR-010)."""

import json

import pytest
from app import access
from app.defence import monitor_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def memory_file(tmp_path, monkeypatch):
    path = tmp_path / "runtime" / "memory.jsonl"
    monkeypatch.setattr(monitor_router, "MEMORY_PATH", path)
    return path


def test_chat_verified_returns_the_monitor_trace_and_other_states_are_unchanged(
    monkeypatch, memory_file
):
    from app import main

    calls = []

    def fake_verified(question, trusted_fallback=False):
        calls.append((question, trusted_fallback))
        return {
            "question": question,
            "answer": "a",
            "sources": [],
            "system_state": "verified",
            "monitor": {"outcome": "released", "rounds": []},
        }

    monkeypatch.setattr(main, "verified_answer", fake_verified)
    monkeypatch.setattr(
        main,
        "answer_question",
        lambda q, **kw: {
            "question": q,
            "answer": "b",
            "sources": [],
            "system_state": kw["system_state"],
        },
    )
    monkeypatch.setattr(main, "_record_chat_history", lambda *a, **k: None)
    client = TestClient(main.app)
    r = client.post(
        "/chat",
        json={"question": "q", "system_state": "verified", "trusted_fallback": True},
    )
    assert r.status_code == 200 and r.json()["monitor"]["outcome"] == "released"
    assert calls == [("q", True)]
    r = client.post("/chat", json={"question": "q", "system_state": "clean"})
    assert (
        r.status_code == 200
        and r.json()["monitor"] is None
        and r.json()["answer"] == "b"
    )


def test_memory_endpoints_list_and_archive_without_deleting(memory_file):
    app = FastAPI()
    app.include_router(monitor_router.router)
    client = TestClient(app)
    assert client.get("/monitor/memory").json()["count"] == 0
    memory_file.parent.mkdir(parents=True)
    memory_file.write_text(
        json.dumps(
            {
                "key": "a" * 64,
                "source": "/x/data/poisoned/knowledge_base/malware/backdoor.md",
                "words": ["engraft"],
                "specs": ["phi1_lexical"],
                "question": "q",
                "round": 0,
                "at": 1.0,
            }
        )
        + "\n"
    )
    body = client.get("/monitor/memory").json()
    assert body["count"] == 1 and body["entries"][0]["source"] == "malware/backdoor.md"
    archived = client.post("/monitor/memory/reset").json()["archived"]
    assert (
        archived
        and (memory_file.parent / archived).exists()
        and not memory_file.exists()
    )
    assert client.get("/monitor/memory").json()["count"] == 0


def test_verified_answer_runs_the_monitor_on_the_poisoned_collection(
    memory_file, monkeypatch
):
    seen = {}

    def fake_monitored(
        question, state, *, memory, llm_factory, mode, search_fn, capture
    ):
        seen.update(state=state, mode=mode, memory=memory.path)
        capture["monitor"] = {"outcome": "restored"}
        return {"answer": "x", "sources": []}

    monkeypatch.setattr(monitor_router.rm, "monitored_answer", fake_monitored)
    out = monitor_router.verified_answer("q", True, llm_factory=object)
    assert seen == {"state": "poisoned", "mode": "restore", "memory": memory_file}
    assert (
        out["monitor"]["trusted_fallback"] is True and out["system_state"] == "verified"
    )
    with pytest.raises(ValueError):
        monitor_router.verified_answer("  ", llm_factory=object)


def test_rate_limit_is_off_by_default_and_refuses_after_the_limit(monkeypatch):
    monkeypatch.delenv("AEGIS_RATE_LIMIT_PER_HOUR", raising=False)
    assert access.rate_limit() == 0
    monkeypatch.setenv("AEGIS_RATE_LIMIT_PER_HOUR", "2")
    assert access.rate_limit() == 2
    now = [0.0]
    app = FastAPI()
    app.add_middleware(access.RateLimitMiddleware, limit=2, clock=lambda: now[0])
    app.post("/chat")(lambda: {"ok": True})
    app.get("/health")(lambda: {"ok": True})
    client = TestClient(app)
    assert [client.post("/chat").status_code for _ in range(3)] == [200, 200, 429]
    assert client.get("/health").status_code == 200
    now[0] = 3601.0
    assert client.post("/chat").status_code == 200
