"""Offline tests for the experimental evidence guard.

Retrieval, the draft model and the verifier model are all replaced with
in-process fakes. These tests prove the validation, policy and audit logic;
they do NOT demonstrate live verification quality.
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from app.defence import evidence_guard as guard

SQLI = (
    "SQL injection occurs when untrusted input is concatenated into a "
    "database query. Parameterized queries prevent SQL injection."
)
DDOS = "A distributed denial-of-service attack floods a target with traffic from many hosts."
SETTINGS = {"model": "fake-model", "max_retries": 1}


def _results():
    return [
        (Document(page_content=SQLI, metadata={"source": "injection.md", "start_index": 0}), 0.82),
        (Document(page_content=DDOS, metadata={"source": "ddos.md", "start_index": 40}), 0.41),
    ]


def _sources():
    return [
        {"source_number": 1, "source": "injection.md", "score": 0.82, "content": SQLI, "metadata": {}},
        {"source_number": 2, "source": "ddos.md", "score": 0.41, "content": DDOS, "metadata": {}},
    ]


def _verifier_json(*claims, abstention=False):
    return json.dumps({"abstention": abstention, "claims": list(claims)})


def _claim(verdict="supported", source_ids=("S1",), quote="Parameterized queries prevent SQL injection", quote_source="S1"):
    quotes = [] if quote is None else [{"source_id": quote_source, "text": quote}]
    return {
        "claim": "Parameterized queries prevent SQL injection.",
        "verdict": verdict,
        "source_ids": list(source_ids),
        "quotes": quotes,
        "explanation": "test",
    }


class FakeVerifier:
    def __init__(self, content=None, error=None):
        self.content, self.error, self.prompts = content, error, []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content, response_metadata={"model_name": "fake-verifier"})


def _run(tmp_path, *, verifier=None, results=None, draft="Use parameterized queries [Source 1].",
         draft_llm=None, retrieval_error=None, audit_writer=guard.write_audit_record):
    def retrieval(question, system_state):
        if retrieval_error:
            raise retrieval_error
        return _results() if results is None else results

    return guard.run_guarded_chat(
        "How can SQL injection be prevented?",
        "poisoned",
        retrieval_fn=retrieval,
        draft_llm_factory=lambda: draft_llm or FakeListChatModel(responses=[draft]),
        verifier_llm_factory=lambda: verifier,
        audit_dir=tmp_path,
        audit_writer=audit_writer,
        settings=SETTINGS,
    )


# ---------------------------------------------------------------- parsing

def test_quote_matching_is_whitespace_and_case_tolerant_but_verbatim():
    assert guard.quote_in_source("parameterized   QUERIES prevent sql injection", SQLI)
    assert not guard.quote_in_source("prepared statements prevent SQL injection", SQLI)
    assert not guard.quote_in_source("SQL", SQLI)  # too short to count as evidence


def test_supported_claim_with_verified_quote():
    findings = guard.parse_verifier_output(_verifier_json(_claim()), _sources())
    assert findings[0]["status"] == "supported"
    assert findings[0]["quotes"][0]["verified"] is True


def test_fabricated_quote_downgrades_claim_to_unavailable():
    claim = _claim(quote="Input validation alone always stops SQL injection")
    finding = guard.parse_verifier_output(_verifier_json(claim), _sources())[0]
    assert finding["verifier_verdict"] == "supported"
    assert finding["status"] == "unavailable"
    assert finding["quotes"][0]["verified"] is False


def test_quote_from_a_different_source_than_cited_is_not_verified():
    claim = _claim(source_ids=("S2",), quote_source="S1")
    finding = guard.parse_verifier_output(_verifier_json(claim), _sources())[0]
    assert finding["status"] == "unavailable"


def test_unknown_source_id_is_flagged():
    claim = _claim(source_ids=("S9",), quote_source="S9")
    finding = guard.parse_verifier_output(_verifier_json(claim), _sources())[0]
    assert finding["status"] == "unavailable"
    assert any("unknown source" in p for p in finding["problems"])


def test_supported_without_quote_is_not_a_pass():
    finding = guard.parse_verifier_output(_verifier_json(_claim(quote=None)), _sources())[0]
    assert finding["status"] == "unavailable"


def test_code_fenced_json_is_accepted():
    raw = "```json\n" + _verifier_json(_claim()) + "\n```"
    assert guard.parse_verifier_output(raw, _sources())[0]["status"] == "supported"


@pytest.mark.parametrize(
    "raw",
    [
        "Everything looks supported.",
        "Sure! " + _verifier_json(_claim()),
        json.dumps([_claim()]),
        json.dumps({"abstention": False, "claims": [_claim()], "confidence": 0.9}),
        json.dumps({"claims": [_claim()]}),
        json.dumps({"abstention": "no", "claims": [_claim()]}),
        json.dumps({"claims": [{**_claim(), "verdict": "probably"}]}),
        json.dumps({"claims": [{**_claim(), "claim": ""}]}),
        json.dumps({"claims": [{**_claim(), "quotes": [{"source_id": "S1"}]}]}),
        json.dumps({"claims": "none"}),
    ],
)
def test_malformed_verifier_output_raises(raw):
    with pytest.raises(guard.VerifierOutputError):
        guard.parse_verifier_output(raw, _sources())


def test_verifier_prompt_contains_only_question_draft_and_source_text():
    sources = _sources()
    sources[0]["source"] = "/repo/backend/data/poisoned/knowledge_base/injection/sql_injection.md"
    sources[0]["metadata"] = {"attack_type": "sql_injection", "origin": "poisoned", "poisoning_method": "PWWS"}
    prompt = guard.build_verifier_prompt("Q?", "draft text", sources)
    assert "[S1]\n" + SQLI in prompt and "[S2]\n" + DDOS in prompt
    for forbidden in ("poisoned", "pwws", "attack_type", "sql_injection.md", "knowledge_base", "reference answer"):
        assert forbidden not in prompt.lower()


# ---------------------------------------------------------------- policy

def test_policy_requires_every_claim_supported():
    supported = {"status": "supported"}
    assert guard.decide(sources=_sources(), findings=[supported]).released
    for bad in ("unsupported", "contradicted", "unavailable"):
        decision = guard.decide(sources=_sources(), findings=[supported, {"status": bad}])
        assert not decision.released and decision.outcome == bad


def test_contradiction_takes_precedence():
    findings = [{"status": "unsupported"}, {"status": "contradicted"}]
    assert guard.decide(sources=_sources(), findings=findings).outcome == "contradicted"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sources": [], "findings": [{"status": "supported"}]},
        {"sources": _sources(), "findings": []},
        {"sources": _sources(), "findings": None},
        {"sources": _sources(), "findings": [{"status": "supported"}], "failure_stage": "verification"},
    ],
)
def test_missing_evidence_or_failed_check_never_passes(kwargs):
    decision = guard.decide(**kwargs)
    assert decision.outcome == "unavailable" and not decision.released


# ---------------------------------------------------------------- end to end (fakes)

def test_supported_draft_is_released_and_audited(tmp_path):
    verifier = FakeVerifier(_verifier_json(_claim()))
    result = _run(tmp_path, verifier=verifier)

    assert result["outcome"] == "supported" and result["decision"] == "released"
    assert result["answer"] == "Use parameterized queries [Source 1]."
    assert [s["source_id"] for s in result["sources"]] == ["S1", "S2"]
    assert result["audit"]["saved"] is True

    record = json.loads(Path(result["audit"]["location"]).read_text())
    assert record["policy_version"] == guard.POLICY_VERSION
    assert record["question"] == "How can SQL injection be prevented?"
    assert record["system_state"] == "poisoned"
    assert record["draft"]["answer"] == result["answer"]
    assert record["verifier"]["prompt"] == verifier.prompts[0]
    assert record["verifier"]["raw_response"] == verifier.content
    assert record["findings"][0]["status"] == "supported"
    assert record["decision"]["released"] is True
    assert record["settings"] == SETTINGS
    assert set(record["timings_ms"]) == {"retrieval_ms", "draft_ms", "verification_ms", "total_ms"}


def test_unsupported_draft_is_withheld(tmp_path):
    claim = {**_claim(verdict="unsupported", source_ids=(), quote=None), "claim": "WAFs stop all injection."}
    result = _run(tmp_path, verifier=FakeVerifier(_verifier_json(_claim(), claim)))
    assert result["outcome"] == "unsupported"
    assert result["decision"] == "withheld" and result["answer"] is None
    assert "not stated" in result["explanation"]


def test_contradicted_draft_is_withheld(tmp_path):
    claim = _claim(verdict="contradicted")
    result = _run(tmp_path, verifier=FakeVerifier(_verifier_json(claim)))
    assert result["outcome"] == "contradicted" and result["answer"] is None


def test_fabricated_quotation_withholds_draft(tmp_path):
    claim = _claim(quote="Stored procedures are always immune to injection")
    result = _run(tmp_path, verifier=FakeVerifier(_verifier_json(claim)))
    assert result["outcome"] == "unavailable" and result["answer"] is None
    assert result["claims"][0]["quotes"][0]["verified"] is False


def test_malformed_verifier_output_is_unavailable_and_recorded(tmp_path):
    result = _run(tmp_path, verifier=FakeVerifier("All good, the answer is supported."))
    assert result["outcome"] == "unavailable" and result["answer"] is None
    assert result["failures"] == [{"stage": "verification", "type": "VerifierOutputError", "timeout": False}]
    record = json.loads(Path(result["audit"]["location"]).read_text())
    assert record["verifier"]["status"] == "malformed"
    assert record["verifier"]["raw_response"] == "All good, the answer is supported."


def test_verifier_timeout_is_unavailable(tmp_path):
    result = _run(tmp_path, verifier=FakeVerifier(error=TimeoutError("verifier timed out")))
    assert result["outcome"] == "unavailable" and result["answer"] is None
    assert result["failures"][0]["timeout"] is True


def test_draft_timeout_is_unavailable_and_verifier_not_called(tmp_path):
    def slow(_):
        raise TimeoutError("draft timed out")

    verifier = FakeVerifier(_verifier_json(_claim()))
    result = _run(tmp_path, verifier=verifier, draft_llm=RunnableLambda(slow))
    assert result["outcome"] == "unavailable" and result["answer"] is None
    assert result["failures"][0]["stage"] == "generation" and result["failures"][0]["timeout"]
    assert verifier.prompts == []


def test_empty_retrieval_is_unavailable_without_model_calls(tmp_path):
    verifier = FakeVerifier(_verifier_json(_claim()))
    result = _run(tmp_path, verifier=verifier, results=[])
    assert result["outcome"] == "unavailable" and result["answer"] is None
    assert "No evidence" in result["explanation"]
    assert verifier.prompts == []
    assert result["audit"]["saved"] is True


def test_retrieval_failure_is_unavailable(tmp_path):
    result = _run(tmp_path, verifier=FakeVerifier("{}"), retrieval_error=ConnectionError("qdrant down"))
    assert result["outcome"] == "unavailable"
    assert result["failures"][0]["stage"] == "retrieval"


def test_audit_write_failure_is_reported_not_hidden(tmp_path):
    def broken_writer(record, directory):
        raise PermissionError("read-only")

    result = _run(tmp_path, verifier=FakeVerifier(_verifier_json(_claim())), audit_writer=broken_writer)
    assert result["audit"]["saved"] is False
    assert result["audit"]["location"] is None
    assert "NOT saved" in result["audit"]["error"]
    assert list(tmp_path.iterdir()) == []


def test_audit_writes_are_create_only(tmp_path):
    record = {"run_id": "fixed-id", "value": 1}
    path = guard.write_audit_record(record, tmp_path)
    with pytest.raises(FileExistsError):
        guard.write_audit_record({"run_id": "fixed-id", "value": 2}, tmp_path)
    assert json.loads(path.read_text())["value"] == 1
    assert [p.name for p in tmp_path.iterdir()] == ["fixed-id.json"]


def test_audit_never_contains_credentials(tmp_path, monkeypatch):
    from app import config

    secret = "sk-proj-THISisAfakeKEYforTESTING1234567890"
    monkeypatch.setattr(config, "LLM_API_KEY", secret)
    verifier = FakeVerifier(error=RuntimeError(f"auth failed for key {secret}"))
    result = _run(tmp_path, verifier=verifier)
    text = Path(result["audit"]["location"]).read_text()
    assert secret not in text and "[REDACTED]" in text
    assert secret not in json.dumps(result)


def test_guarded_route_rejects_defended_state(tmp_path):
    with pytest.raises(ValueError):
        guard.run_guarded_chat("q", "defended", audit_dir=tmp_path)


def test_guarded_llm_has_timeout_and_bounded_retries(monkeypatch):
    from app import config

    monkeypatch.setattr(config, "LLM_API_KEY", "sk-test-not-real-000000000000")
    llm = guard.create_guarded_llm(temperature=0, timeout=7)
    assert llm.request_timeout == 7
    assert llm.max_retries == guard.MODEL_MAX_RETRIES
    assert os.environ.get("OPENAI_API_KEY") != "sk-test-not-real-000000000000"


# ---------------------------------------------------------------- policy v2 fixes

@pytest.mark.parametrize(
    "quote",
    [
        "Parameterized queries prevent SQL injection.",
        '"Parameterized queries prevent SQL injection"',
        "...parameterized queries prevent SQL injection",
        "Parameterized queries prevent SQL injection\u2026",
    ],
)
def test_quote_edge_punctuation_is_ignored(quote):
    assert guard.quote_in_source(quote, SQLI)


def test_inner_words_must_still_match_verbatim():
    assert not guard.quote_in_source("Parameterized queries stop SQL injection.", SQLI)
    assert not guard.quote_in_source("... SQL ...", SQLI)


def test_trailing_full_stop_regression_from_live_run():
    source = "with the intent to deny legitimate users access to a service by consuming resources"
    assert guard.quote_in_source("with the intent to deny legitimate users access to a service.", source)


def test_abstention_is_released_as_refusal():
    decision = guard.decide(sources=_sources(), findings=[], abstention=True)
    assert decision.outcome == "abstained" and decision.released


def test_abstention_with_supported_meta_claims_is_abstained():
    decision = guard.decide(sources=_sources(), findings=[{"status": "supported"}], abstention=True)
    assert decision.outcome == "abstained"


@pytest.mark.parametrize("bad", ["contradicted", "unsupported", "unavailable"])
def test_abstention_flag_cannot_launder_bad_claims(bad):
    decision = guard.decide(sources=_sources(), findings=[{"status": "supported"}, {"status": bad}], abstention=True)
    assert decision.outcome == bad and not decision.released


def test_abstention_without_evidence_is_still_unavailable():
    decision = guard.decide(sources=[], findings=[], abstention=True)
    assert decision.outcome == "unavailable"


def test_end_to_end_abstention_releases_refusal_and_records_flag(tmp_path):
    refusal = "The retrieved context does not describe HTTP floods."
    result = _run(tmp_path, verifier=FakeVerifier(_verifier_json(abstention=True)), draft=refusal)
    assert result["outcome"] == "abstained" and result["decision"] == "released"
    assert result["answer"] == refusal
    record = json.loads(Path(result["audit"]["location"]).read_text())
    assert record["verifier"]["abstention"] is True
    assert record["policy_version"] == "evidence-guard-policy-v2"
