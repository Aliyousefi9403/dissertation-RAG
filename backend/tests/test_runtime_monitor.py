"""Tests for the runtime verification monitor (app/defence/runtime_monitor.py, ADR-009)."""

import hashlib
import json

import pytest
from langchain_core.documents import Document

from app.defence import entropy_filter as ef
from app.defence import runtime_monitor as rm

try:
    ef._wordnet()
    rm._zipf()
except ef.DetectorUnavailable:  # pragma: no cover
    pytest.skip("WordNet or wordfreq not installed", allow_module_level=True)


@pytest.fixture
def ontology(tmp_path):
    bundle = {"objects": [
        {"type": "attack-pattern", "name": "Malicious File Upload",
         "description": "An adversary uploads a malicious file to a web server and then executes it.",
         "x_capec_prerequisites": ["The server accepts uploaded files without validation."],
         "external_references": [{"source_name": "capec", "external_id": "CAPEC-17"}]},
        {"type": "attack-pattern", "name": "Supply Chain Implant",
         "description": "The adversary implants malicious software in the supply chain distribution channel.",
         "external_references": [{"source_name": "capec", "external_id": "CAPEC-523"}]},
    ]}
    path = tmp_path / "stix.json"
    path.write_text(json.dumps(bundle))
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text("attacks:\n"
                       "  uploading:\n    display_name: Malicious File Upload\n"
                       "    primary_source: {system: CAPEC, id: CAPEC-17}\n"
                       "  backdoor:\n    display_name: Backdoor\n"
                       "    primary_source: {system: CAPEC, id: CAPEC-523}\n"
                       "  unknown:\n    display_name: Quantum Attack\n"
                       "    primary_source: {system: CAPEC, id: CAPEC-999}\n")
    return rm.TrustedOntology({path: hashlib.sha256(path.read_bytes()).hexdigest()}, mapping)


def test_base_forms_merge_inflections_and_adverbs():
    assert rm.base_form("prerequisites") == "prerequisite"
    assert rm.base_form("implants") == "implant"
    assert rm.base_form("asynchronously") == "asynchronous"


def test_hash_mismatch_fails_closed(tmp_path):
    path = tmp_path / "stix.json"
    path.write_text("{}")
    with pytest.raises(ef.DetectorUnavailable):
        rm.TrustedOntology({path: "0" * 64})
    with pytest.raises(ef.DetectorUnavailable):
        rm.TrustedOntology({tmp_path / "missing.json": "0" * 64})


def test_lexical_spec_flags_rare_words_absent_from_the_trusted_reference(ontology):
    q = "How does Backdoor work, according to the knowledge base?"
    bad = rm.check("The attacker will engraft malicious package into the system.", q, "backdoor", ontology)
    assert [v.spec for v in bad] == ["phi1_lexical"] and bad[0].witnesses == ["engraft"]
    assert rm.check("The adversary implants malicious software in the supply chain.", q, "backdoor", ontology) == []


def test_words_in_the_question_are_allowed(ontology):
    q = "What does the knowledge base say about engraft attacks?"
    assert rm.check("Engraft is not described.", q, None, ontology) == []


def test_availability_spec_fires_only_when_the_trusted_reference_covers_the_attack(ontology):
    refusal = "The retrieved context does not provide enough information to answer."
    assert [v.spec for v in rm.check(refusal, "How does Backdoor work?", "backdoor", ontology)] == ["phi2_availability"]
    assert rm.check(refusal, "How does Quantum Attack work?", "unknown", ontology) == []
    assert rm.check(refusal, "Something else?", None, ontology) == []


def test_attack_is_taken_from_the_question_then_from_the_passages(ontology):
    assert ontology.attack_for("What conditions are required for Malicious File Upload?") == "uploading"
    docs = [Document(page_content="x", metadata={"attack_type": "backdoor"})]
    assert ontology.attack_for("What is this?", docs) == "backdoor"
    assert ontology.attack_for("What is this?") is None


def test_diagnosis_points_at_the_passage_that_contains_the_witness(ontology):
    poisoned = Document(page_content="An attacker engraft malicious package into the system.", metadata={"source": "p", "start_index": 0})
    clean = Document(page_content="The adversary uploads a malicious file.", metadata={"source": "c", "start_index": 0})
    viol = rm.check("They engraft a package.", "How does Backdoor work?", "backdoor", ontology)
    assert rm.diagnose(viol, [poisoned, clean], ontology) == {rm.passage_key(poisoned): ["engraft"]}


def test_memory_is_append_only_and_survives_reload(tmp_path):
    memory = rm.QuarantineMemory(tmp_path / "m.jsonl")
    assert memory.add("k1", reason="x") and not memory.add("k1")
    assert "k1" in rm.QuarantineMemory(tmp_path / "m.jsonl")
    assert len((tmp_path / "m.jsonl").read_text().splitlines()) == 1


class StubLLM:
    """Returns scripted answers in order and records the prompts it was given."""

    def __init__(self, answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self):
        return self

    def invoke(self, value):
        from langchain_core.messages import AIMessage
        self.prompts.append(value.to_string() if hasattr(value, "to_string") else str(value))
        return AIMessage(content=self.answers.pop(0))


def _runnable(llm):
    from langchain_core.runnables import RunnableLambda
    return lambda: RunnableLambda(llm.invoke)


POISONED = Document(page_content="An attacker engraft malicious package into the arrangement.",
                    metadata={"source": "kb/backdoor.md", "start_index": 0})
CLEAN = [Document(page_content=f"The adversary implants malicious software, step {i}.",
                  metadata={"source": "kb/backdoor.md", "start_index": 100 * (i + 1)}) for i in range(4)]


def search(question, k):
    return [(POISONED, 0.9)] + [(d, 0.8 - i / 10) for i, d in enumerate(CLEAN)]


def test_violation_quarantines_regenerates_and_the_repeat_question_is_clean(ontology, tmp_path):
    memory = rm.QuarantineMemory(tmp_path / "m.jsonl")
    llm = StubLLM(["Steps: Engraft Malicious Package.", "The adversary implants malicious software [Source 1].",
                   "The adversary implants malicious software [Source 1]."])
    capture = {}
    q = "What are the execution steps of Backdoor?"
    first = rm.monitored_answer(q, "poisoned", memory=memory, llm_factory=_runnable(llm), ontology=ontology,
                                search_fn=search, capture=capture)
    assert first["outcome"] == "released" and "engraft" not in first["answer"].lower()
    assert rm.passage_key(POISONED) in memory
    assert capture["monitor"]["generations"] == 2
    assert all(s["content"] != POISONED.page_content for s in first["sources"])
    assert "Runtime monitor" in llm.prompts[1] and "Engraft Malicious Package" in llm.prompts[1]
    capture = {}
    second = rm.monitored_answer(q, "poisoned", memory=memory, llm_factory=_runnable(llm), ontology=ontology,
                                 search_fn=search, capture=capture)
    assert second["outcome"] == "released" and capture["monitor"]["generations"] == 1
    assert capture["monitor"]["rounds"][0]["skipped_quarantined"] == 1


def test_round_zero_uses_the_unchanged_pipeline_prompt(ontology, tmp_path):
    from app.generation.prompt import RAG_PROMPT
    from app.generation.rag_chain import format_context
    llm = StubLLM(["The adversary implants malicious software."])
    q = "How does Backdoor work?"
    rm.monitored_answer(q, "clean", memory=rm.QuarantineMemory(tmp_path / "m.jsonl"), llm_factory=_runnable(llm),
                        ontology=ontology, search_fn=lambda q_, k: [(d, 0.5) for d in CLEAN])
    expected = RAG_PROMPT.invoke({"question": q, "context": format_context([(d, 0.5) for d in CLEAN[:3]])})
    assert llm.prompts[0] == expected.to_string()


def test_unresolved_lexical_violation_withholds_the_answer(ontology, tmp_path):
    # Every candidate repeats the substituted word, so quarantining cannot remove it in time.
    tainted = [Document(page_content=f"An attacker will engraft it, variant {i}.", metadata={"source": "kb/b.md", "start_index": i})
               for i in range(10)]
    llm = StubLLM(["They engraft it."] * 3)
    out = rm.monitored_answer("How does Backdoor work?", "poisoned", memory=rm.QuarantineMemory(tmp_path / "m.jsonl"),
                              llm_factory=_runnable(llm), ontology=ontology,
                              search_fn=lambda q, k: [(d, 0.5) for d in tainted])
    assert out["outcome"] == "withheld" and out["answer"] == rm.WITHHELD


def test_v2_flags_only_rare_words_copied_from_the_context(ontology):
    q = "How does Backdoor work?"
    answer = "Attackers engraft packages, emphasizing stealth."
    assert rm.check(answer, q, "backdoor", ontology, ["The adversary implants software."]) == []
    copied = rm.check(answer, q, "backdoor", ontology, ["An attacker engraft malicious package."])
    assert [v.witnesses for v in copied] == [["engraft"]]
    assert rm.check(answer, q, "backdoor", ontology)[0].witnesses == ["emphasizing", "engraft"]  # v1 behaviour


def test_restore_adds_the_trusted_reference_only_in_restore_mode(ontology, tmp_path):
    refusal = "The retrieved context does not provide this information."
    for mode, expected in (("verify", "released_refusal"), ("restore", "restored")):
        llm = StubLLM([refusal] * 3 + ["The adversary implants malicious software in the supply chain."])
        capture = {}
        out = rm.monitored_answer("How does Backdoor work?", "poisoned", mode=mode,
                                  memory=rm.QuarantineMemory(tmp_path / f"{mode}.jsonl"), llm_factory=_runnable(llm),
                                  ontology=ontology, search_fn=lambda q, k: [(d, 0.5) for d in CLEAN], capture=capture)
        assert out["outcome"] == expected
        trusted = [s for s in out["sources"] if s["source"].startswith("trusted-mitre:")]
        assert bool(trusted) == (mode == "restore")
