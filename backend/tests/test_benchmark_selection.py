"""The benchmark file is configurable without changing the pilot default."""

import importlib
import json
from pathlib import Path

import app.evaluation.retrieval_metrics as rm

ROOT = Path(__file__).resolve().parents[1]


def _reload(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("AEGIS_BENCHMARK_FILE", raising=False)
    else:
        monkeypatch.setenv("AEGIS_BENCHMARK_FILE", str(value))
    module = importlib.reload(rm)
    module.load_questions.cache_clear()
    return module


def test_default_is_unchanged_pilot_benchmark(monkeypatch):
    module = _reload(monkeypatch, None)
    assert module.QUESTIONS_FILE == ROOT / "data/evaluation/questions.json"
    assert len(module.load_questions()) == 12


def test_env_selects_frozen_v1(monkeypatch):
    v1 = ROOT / "data/evaluation/questions_v1.json"
    module = _reload(monkeypatch, v1)
    assert module.QUESTIONS_FILE == v1
    questions = module.load_questions()
    assert len(questions) == 44
    assert (
        module.find_ground_truth(questions[0]["question"])["id"] == questions[0]["id"]
    )
    _reload(monkeypatch, None)


def test_v1_matches_its_frozen_record():
    import hashlib

    record = json.loads((ROOT / "data/evaluation/benchmark_v1_record.json").read_text())
    data = (ROOT / "data/evaluation/questions_v1.json").read_bytes()
    assert hashlib.sha256(data).hexdigest() == record["questions_v1_sha256"]
    questions = json.loads(data)
    assert (
        len({q["id"] for q in questions}) == len(questions) == record["question_count"]
    )
    assert {q["split"] for q in questions} == {"development", "held_out"}
    held = set(record["held_out_documents"])
    assert all(
        (q["source_document"] in held) == (q["split"] == "held_out") for q in questions
    )
    assert not held & set(record["pilot_documents"])
