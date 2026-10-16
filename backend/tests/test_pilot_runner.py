"""Mocked pilot rehearsal and capture regressions. No inference or downloads."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from app.evaluation import pilot_runner as pilot
from app.evaluation.pilot_records import CONFIG_KEYS, read_run
from langchain_core.documents import Document


@pytest.fixture
def specification(tmp_path, monkeypatch):
    # Twelve synthetic questions, six documents, one documented shared source.
    questions = []
    roots = {state: tmp_path / state for state in ("clean", "poisoned")}
    for root in roots.values():
        root.mkdir()
        for index in range(6):
            reference = "Tshared" if index < 2 else f"T{index}"
            (root / f"attack{index}.md").write_text(
                f"# Attack\n## Metadata\n- Attack key: `attack{index}`\n- ATT&CK ID: `{reference}`\n"
                "## Attack description\nSynthetic evidence."
            )
    for index in range(12):
        questions.append({"id": f"q{index}", "question": f"Question {index}?",
                          "expected_attack_type": f"attack{index // 2}",
                          "expected_sections": ["attack_description"], "reference_facts": ["Synthetic fact"]})
    benchmark = tmp_path / "questions.json"
    benchmark.write_text(json.dumps(questions))
    attack = tmp_path / "attack.jsonl"
    attack.write_text(json.dumps({"file": "attack0.md", "section": "attack description", "success": True,
                                  "original_text": "Synthetic", "adversarial_text": "Changed"}) + "\n")
    config = dict.fromkeys(CONFIG_KEYS, "synthetic")
    config.update(QDRANT_URL="http://localhost:6333", LLM_TEMPERATURE=0, RETRIEVAL_TOP_K=3,
                  CHUNK_SIZE=500, CHUNK_OVERLAP=100, QDRANT_COLLECTIONS={"clean": "clean", "poisoned": "poisoned"})
    spec = {"schema_version": 1, "benchmark": str(benchmark), "repetitions": 3,
            "dataset_namespace": "synthetic", "corpus_roots": {k: str(v) for k, v in roots.items()},
            "source_group_policy": "shared_documented_ids_v1", "attack_manifest": str(attack),
            "attack_summary": None, "expected_config": config,
            "requests": {"timeout_seconds": 60, "max_retries": 0, "retrieval_timeout_seconds": 15}}
    path = tmp_path / "pilot.json"
    path.write_text(json.dumps(spec))
    monkeypatch.setattr(pilot, "code_provenance", lambda root: {"revision": None, "file_sha256": {}})
    return path


class MockServices:
    kind = "mock"

    def __init__(self, plan, fail_generation=False):
        self.plan = plan
        self.effective_config = plan["requested_config"]
        self.calls = []
        self.fail_generation = fail_generation

    def answer(self, question, condition, capture):
        self.calls.append((question, condition, "generation"))
        index = int(question.split()[1][:-1])
        source = {"source": self.plan["corpora"][condition]["root"] + f"/attack{index // 2}.md",
                  "content": "Synthetic evidence.", "score": 0.9,
                  "metadata": {"attack_type": f"attack{index // 2}", "start_index": 0}}
        capture.update(sources=[source], retrieval_status="ok", request_attempts=1)
        if self.fail_generation and question == "Question 0?" and condition == "clean":
            capture["generation_status"] = "unavailable"
            raise TimeoutError("synthetic generation failure")
        capture["generation_status"] = "ok"
        return {"answer": condition, "sources": [source]}

    def judge(self, stage, question, sources, answer, capture):
        assert answer is not None
        self.calls.append((question["question"], answer, stage))
        score = 1.0 if answer == "clean" else 0.5
        capture.update(raw_score=score, status="valid", reason="mocked", request_attempts=1,
                       raw_response=json.dumps({"score": score, "reason": "mocked"}))
        return {"score": score, "reason": "mocked"}

    def retrieval_metrics(self, question, sources, condition):
        return {"hit_at_3": 1, "reciprocal_rank": 1.0,
                "poison_exposure": {"poison_hit_at_3": 1} if condition == "poisoned" else None}

    def attack_success(self, poison_hit, clean, poisoned):
        # This boundary is mocked; real execution delegates to build_attack_success.
        return {"rag_attack_success": None if clean is None or poisoned is None else True}


def test_dry_run_counterbalances_preserves_groups_and_reports_retry_bounds(specification, monkeypatch, capsys):
    forbidden = Mock(side_effect=AssertionError("Live execution forbidden"))
    monkeypatch.setattr(pilot, "LiveServices", forbidden)
    assert pilot.main(["--dry-run", "--spec", str(specification)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["nominal_logical_calls"] == {"generation": 72, "judge": 144}
    assert plan["maximum_model_attempts"] == {"generation": 72, "judge": 144}
    assert len(plan["schedule"]) == 36
    assert len(plan["source_groups"]["groups"]) == 5
    assert sum(unit["condition_order"][0] == "clean" for unit in plan["schedule"]) == 18
    for qid in ("q0", "q1"):
        units = [unit for unit in plan["schedule"] if unit["question_id"] == qid]
        assert [unit["repetition"] for unit in units] == [1, 2, 3]
        assert units[0]["condition_order"] == units[2]["condition_order"] != units[1]["condition_order"]
        assert units[0]["source_group_ids"] == units[1]["source_group_ids"] == units[2]["source_group_ids"]
    forbidden.assert_not_called()
    assert not (specification.parent / "runs").exists()


def test_mocked_12_question_three_repetition_rehearsal_and_offline_replay(specification, tmp_path, monkeypatch):
    plan = pilot.prepare(specification)
    services = MockServices(plan)
    path = pilot.execute(plan, tmp_path / "runs", services=services)
    report = pilot.aggregate(path)
    assert report["complete"] is True
    assert report["execution_backend"] == "mock"
    assert report["scheduled_pairs"] == 36
    assert report["model_attempts_recorded"] == {"generation": 72, "judge": 144}
    assert report["paired_metrics"]["correctness"]["paired_valid_count"] == 36
    assert report["paired_metrics"]["correctness"]["mean_delta"] == -0.5
    assert report["document_overlap"]["valid_count"] == 36
    assert report["document_overlap"]["mean_jaccard"] == 1.0
    manifest, records, issues = read_run(path)
    assert not issues and len(records) == 324
    assert manifest["attack_manifest"]["entries"][0]["adversarial_text"] == "Changed"
    assert "Synthetic evidence" in manifest["corpora"]["clean"]["documents"]["attack0.md"]["text"]
    assert records["000000-clean-retrieval.json"]["inputs"]["question"]["reference_facts"]
    assert records["000000-pair.json"]["attack_inputs"]["threshold"] == 0.25
    generation_calls = [(q, c) for q, c, stage in services.calls if stage == "generation"]
    assert generation_calls == [(f"Question {int(unit['question_id'][1:])}?", condition)
                                for unit in plan["schedule"] for condition in unit["condition_order"]]
    for corpus in plan["corpora"].values():
        shutil.rmtree(corpus["root"])
    Path(plan["attack_manifest"]["path"]).unlink()
    Path(plan["benchmark"]["path"]).unlink()
    monkeypatch.setattr(pilot, "LiveServices", Mock(side_effect=AssertionError("Offline only")))
    assert pilot.aggregate(path) == report


def test_generation_failure_retains_evidence_and_skips_both_judges(specification, tmp_path):
    plan = pilot.prepare(specification)
    services = MockServices(plan, fail_generation=True)
    path = pilot.execute(plan, tmp_path / "runs", services=services)
    report = pilot.aggregate(path)
    assert report["complete"] is True  # All scheduled outcomes recorded, including failures.
    assert report["error_record_count"] == 3
    assert report["paired_metrics"]["correctness"]["paired_valid_count"] == 33
    _, records, _ = read_run(path)
    assert records["000000-clean-rag.json"]["answer"] is None
    assert records["000000-clean-rag.json"]["capture"]["sources"]
    for stage in ("correctness", "faithfulness"):
        assert records[f"000000-clean-{stage}.json"]["capture"]["unavailable_reason"] == "generation_unavailable_not_judged"
    assert not any(q == "Question 0?" and c == "clean" and stage != "generation" for q, c, stage in services.calls)


def test_interruption_and_truncation_report_incomplete(specification, tmp_path):
    plan = pilot.prepare(specification)
    services = MockServices(plan)
    services.answer = Mock(side_effect=KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):
        pilot.execute(plan, tmp_path / "interrupted", services=services)
    path = next((tmp_path / "interrupted").iterdir())
    report = pilot.aggregate(path)
    assert report["complete"] is False and report["issues"]
    path = pilot.execute(plan, tmp_path / "finished", services=MockServices(plan))
    (path / "observations/000000-clean-rag.json").write_text('{"schema_version":')
    assert pilot.aggregate(path)["complete"] is False


@pytest.mark.parametrize("retries,expected_calls", [(0, 1), (1, 2), (2, 3)])
def test_retry_attempts_are_explicit_and_bounded(retries, expected_calls):
    invoke = Mock(side_effect=TimeoutError)
    capture = {}
    with pytest.raises(TimeoutError):
        pilot.bounded_invoke(invoke, "prompt", max_retries=retries, capture=capture)
    assert invoke.call_count == capture["request_attempts"] == expected_calls


def test_retry_success_and_nonretryable_error():
    capture = {}
    invoke = Mock(side_effect=[TimeoutError(), "answer"])
    assert pilot.bounded_invoke(invoke, "prompt", max_retries=1, capture=capture) == "answer"
    assert capture["request_attempts"] == 2
    invoke = Mock(side_effect=ValueError)
    with pytest.raises(ValueError):
        pilot.bounded_invoke(invoke, "prompt", max_retries=3, capture={})
    assert invoke.call_count == 1


@pytest.fixture
def captured_modules(monkeypatch):
    search = ModuleType("app.retrieval.search")
    search.search_knowledge_base = Mock()
    factory = ModuleType("app.generation.llm_factory")
    factory.create_llm = Mock()
    prompt = ModuleType("app.generation.prompt")
    prompt.RAG_PROMPT = MagicMock()
    for dependency in (search, factory, prompt):
        monkeypatch.setitem(sys.modules, dependency.__name__, dependency)
    modules = []
    for name in ("generation/rag_chain", "evaluation/llm_judge"):
        path = Path(__file__).resolve().parents[1] / "app" / (name + ".py")
        spec = importlib.util.spec_from_file_location(name.replace("/", "_"), path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    return modules


def test_rag_capture_free_behaviour_and_partial_generation_failure(captured_modules):
    rag, _ = captured_modules
    doc = Document(page_content="Evidence", metadata={"source": "synthetic.md", "start_index": 0})
    rag.search_knowledge_base.return_value = [(doc, 0.9)]
    chain = rag.RAG_PROMPT.__or__.return_value
    chain.invoke.return_value = SimpleNamespace(content="Answer")
    plain = rag.answer_question("Question?")
    capture = {}
    traced = rag.answer_question("Question?", capture=capture)
    assert plain == traced
    assert capture["sources"] == plain["sources"]
    chain.invoke.side_effect = TimeoutError
    capture = {}
    with pytest.raises(TimeoutError):
        rag.answer_question("Question?", capture=capture)
    assert capture["retrieval_status"] == "ok" and capture["sources"]
    assert capture["generation_status"] == "unavailable"
    assert capture["error"] == {"stage": "generation", "type": "TimeoutError"}


@pytest.mark.parametrize("raw,expected,status", [
    ('{"score": 0.75, "reason": "ok"}', {"score": 0.75, "reason": "ok"}, "valid"),
    ('{"score": "0.75"}', {"score": 0.75, "reason": ""}, "malformed"),
    ('{"score": true}', {"score": 1.0, "reason": ""}, "malformed"),
    ('{"score": NaN}', {"score": 1.0, "reason": ""}, "malformed"),
    ('{"score": 2}', {"score": 1.0, "reason": ""}, "valid"),
    ('{"score": null}', None, "missing"), ('{}', None, "missing"), ('not JSON', None, "malformed"),
])
def test_judge_capture_preserves_legacy_parsing_and_raw_availability(captured_modules, raw, expected, status):
    _, judge = captured_modules
    assert judge._parse_judge_response(raw) == expected
    capture = {}
    assert judge._parse_judge_response(raw, capture=capture) == expected
    assert capture["status"] == status and capture["raw_response"] == raw


def test_judge_capture_free_calls_and_errors_are_preserved(captured_modules):
    _, judge = captured_modules
    judge.create_llm.return_value.invoke.return_value = SimpleNamespace(content='{"score": 0.5}')
    assert judge.evaluate_correctness("Q", ["fact"], "answer") == {"score": 0.5, "reason": ""}
    judge.create_llm.assert_called_once_with(temperature=0)
    judge.create_llm.return_value.invoke.side_effect = TimeoutError("sensitive detail not persisted")
    assert judge.evaluate_faithfulness("Q", "context", "answer") is None
    capture = {}
    assert judge.evaluate_faithfulness("Q", "context", "answer", capture=capture) is None
    assert capture["error"] == {"stage": "judge", "type": "TimeoutError"}
    assert "sensitive" not in str(capture)


def test_model_adapter_sets_timeout_and_disables_sdk_retries(monkeypatch):
    module = ModuleType("langchain_openai")
    module.ChatOpenAI = Mock()
    module.ChatOpenAI.return_value.invoke.return_value = "response"
    monkeypatch.setitem(sys.modules, "langchain_openai", module)
    service = object.__new__(pilot.LiveServices)
    service.config = SimpleNamespace(LLM_MODEL="synthetic", LLM_API_KEY="dummy", LLM_TEMPERATURE=0.25)
    service.plan = {"requests": {"timeout_seconds": 7, "max_retries": 0}}
    capture = {}
    assert service.factory(capture)(temperature=0).invoke("prompt") == "response"
    module.ChatOpenAI.assert_called_once_with(model="synthetic", api_key="dummy", temperature=0,
                                             timeout=7, max_retries=0)
    assert capture["request_attempts"] == 1

@pytest.mark.parametrize('raw', [-0.01, 1.01, True, '0.5', float('inf')])
def test_pilot_rejects_invalid_rubric_scores(raw):
    assert pilot.pilot_score(raw)[0] is None


def test_invalid_raw_scores_are_excluded_from_paired_results(specification, tmp_path):
    class InvalidJudge(MockServices):
        def judge(self, stage, question, sources, answer, capture):
            result = super().judge(stage, question, sources, answer, capture)
            if answer == 'clean':
                capture['raw_score'] = 2
            return result
    plan = pilot.prepare(specification)
    run = pilot.execute(plan, tmp_path / 'runs', services=InvalidJudge(plan))
    report = pilot.aggregate(run)
    assert report['paired_metrics']['correctness']['paired_valid_count'] == 0
    assert report['attack_success']['valid_count'] == 0
    assert report['document_overlap']['valid_count'] == 36


def test_offline_overlap_replays_evidence_not_saved_summary(specification, tmp_path, monkeypatch):
    plan = pilot.prepare(specification)
    run = pilot.execute(plan, tmp_path / 'runs', services=MockServices(plan))
    manifest, records, issues = read_run(run)
    records['000000-pair.json']['document_overlap']['jaccard'] = 0
    monkeypatch.setattr(pilot, 'read_run', lambda path: (manifest, records, issues))
    report = pilot.aggregate(run)
    assert report['document_overlap']['mean_jaccard'] == 1
    assert 'overlap_replay_mismatch:0' in report['issues']
    assert report['complete'] is False


@pytest.mark.parametrize('value', [[], None, 3])
def test_malformed_completion_is_reported(specification, tmp_path, value):
    plan = pilot.prepare(specification)
    run = pilot.execute(plan, tmp_path / 'runs', services=MockServices(plan))
    (run / 'completion.json').write_text(json.dumps(value))
    report = pilot.aggregate(run)
    assert report['complete'] is False
    assert any(issue.startswith('completion_unreadable:') for issue in report['issues'])
