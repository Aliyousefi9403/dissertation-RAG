"""HTTP contract tests for POST /guarded-chat (orchestration stubbed)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.defence import evidence_guard, router as router_module


def _payload(**overrides):
    base = {
        "run_id": "run-1",
        "question": "q",
        "system_state": "clean",
        "policy_version": evidence_guard.POLICY_VERSION,
        "label": evidence_guard.EXPERIMENT_LABEL,
        "outcome": "unsupported",
        "decision": "withheld",
        "answer": None,
        "explanation": "1 claim(s) are not stated in the retrieved sources.",
        "claims": [
            {
                "claim": "c",
                "status": "unsupported",
                "verifier_verdict": "unsupported",
                "source_ids": [],
                "quotes": [],
                "explanation": "",
                "problems": [],
            }
        ],
        "sources": [
            {"source_id": "S1", "source_number": 1, "source": "a.md", "score": 0.5, "content": "x", "metadata": {}}
        ],
        "failures": [],
        "audit": {"saved": True, "run_id": "run-1", "location": "/tmp/run-1.json", "error": None},
        "timings_ms": {"retrieval_ms": 1.0, "draft_ms": 2.0, "verification_ms": 3.0, "total_ms": 6.0},
    }
    base.update(overrides)
    return base


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router_module.router)
    return TestClient(app)


def test_route_returns_withheld_result(client, monkeypatch):
    calls = []

    def fake(question, system_state):
        calls.append((question, system_state))
        return _payload(question=question, system_state=system_state)

    monkeypatch.setattr(evidence_guard, "run_guarded_chat", fake)
    response = client.post("/guarded-chat", json={"question": "  q  ", "system_state": "poisoned"})

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "withheld" and body["answer"] is None
    assert calls == [("q", "poisoned")]


@pytest.mark.parametrize("state", ["defended", "compare", ""])
def test_route_rejects_other_states(client, state):
    response = client.post("/guarded-chat", json={"question": "q", "system_state": state})
    assert response.status_code == 422


@pytest.mark.parametrize("question", ["", "   "])
def test_route_rejects_empty_question(client, question):
    response = client.post("/guarded-chat", json={"question": question})
    assert response.status_code in (400, 422)


def test_route_maps_unexpected_errors_to_500(client, monkeypatch):
    def boom(question, system_state):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(evidence_guard, "run_guarded_chat", boom)
    response = client.post("/guarded-chat", json={"question": "q"})
    assert response.status_code == 500
    assert "secret internal detail" not in response.text


def test_response_model_rejects_invented_confidence(client, monkeypatch):
    monkeypatch.setattr(
        evidence_guard, "run_guarded_chat", lambda q, s: _payload(confidence=0.97)
    )
    response = client.post("/guarded-chat", json={"question": "q"})
    assert response.status_code == 200
    assert "confidence" not in response.json()
