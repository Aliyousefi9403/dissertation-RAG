"""Synthetic offline measurement tests. No services or real research writes."""

import copy
import importlib.util
import json
import socket
import sqlite3
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import dotenv
import pytest
from app.evaluation import edited_text_exposure as exposure
from app.evaluation.pilot_records import RunStore, sha256


@pytest.fixture(autouse=True)
def block_services(monkeypatch):
    blocked = Mock(side_effect=AssertionError("Offline measurement cannot access external services"))
    for owner, name in ((socket.socket, "connect"), (socket.socket, "connect_ex"),
                        (socket, "create_connection"), (sqlite3, "connect")):
        monkeypatch.setattr(owner, name, blocked)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    yield
    blocked.assert_not_called()


def corpus(text, root):
    docs = {"injection/sample.md": {"text": text, "sha256": sha256(text.encode())}}
    fingerprint = sha256(json.dumps({k: v["sha256"] for k, v in docs.items()}, sort_keys=True).encode())
    return {"root": root, "documents": docs, "sha256": fingerprint,
            "indexed_content_sha256": None, "indexed_content_status": "unverified"}


def attack_snapshot(entries):
    text = "".join(json.dumps(entry) + "\n" for entry in entries)
    return {"text": text, "entries": entries, "sha256": sha256(text.encode())}


@pytest.fixture
def inputs():
    original = "The attacker sends bad input. The unchanged tail stays here."
    adversarial = original.replace("bad", "harmful")
    template = "# Sample\n\n## Attack description\n\n{}\n\n## Consequences\n\nOther content.\n"
    return {"namespace": "synthetic.dataset",
            "clean_corpus": corpus(template.format(original), "/archived/clean"),
            "poisoned_corpus": corpus(template.format(adversarial), "/archived/poisoned"),
            "attack_manifest": attack_snapshot([{"file": "injection/sample.md", "section": "attack description",
                                                 "success": True, "original_text": original,
                                                 "adversarial_text": adversarial}])}


def source(inputs, content):
    poisoned = inputs["poisoned_corpus"]
    text = poisoned["documents"]["injection/sample.md"]["text"]
    path = poisoned["root"] + "/injection/sample.md"
    return {"source": path, "content": content,
            "metadata": {"source": path, "start_index": text.index(content)}}


def measure(inputs, sources):
    return exposure.edited_text_exposure_at_3(
        sources, index=exposure.build_edit_index(**inputs), poisoned_corpus=inputs["poisoned_corpus"])


@pytest.mark.parametrize("content", ["## Attack description", "The attacker sends ",
                                    "The unchanged tail stays here.", "Other content."])
def test_heading_and_unchanged_text_are_not_edited_evidence(inputs, content):
    value = measure(inputs, [source(inputs, content)])
    assert value["edited_text_hit_at_3"] == 0
    assert value["known_unedited_source_count"] == 1
    assert value["unknown_source_count"] == 0


def test_actual_edited_characters_and_half_open_chunk_boundaries(inputs):
    index = exposure.build_edit_index(**inputs)
    spans = index["entries"][0]["edited_spans"]
    text = inputs["poisoned_corpus"]["documents"]["injection/sample.md"]["text"]
    start, end = spans[0]
    for a, b, hit in ((start, end, 1), (start - 1, start, 0), (end - 1, end, 1)):
        s = source(inputs, "harmful")
        s["content"], s["metadata"]["start_index"] = text[a:b], a
        assert measure(inputs, [s])["edited_text_hit_at_3"] == hit
    assert index["entries"][0]["status"] == "verified"


def test_legacy_section_exposure_still_counts_heading_and_unchanged_text(inputs, tmp_path, monkeypatch):
    # Import the existing module with only its manifest service mocked. Its
    # section metric is intentionally preserved, including the audited case.
    stub = ModuleType("app.evaluation.pwws_manifest")
    stub.get_successful_entries_by_file = lambda: {"injection/sample.md": inputs["attack_manifest"]["entries"]}
    monkeypatch.setitem(sys.modules, "app.evaluation.pwws_manifest", stub)
    module_path = Path(exposure.__file__).with_name("retrieval_metrics.py")
    spec = importlib.util.spec_from_file_location("legacy_exposure_test", module_path)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    monkeypatch.setattr(legacy, "_relative_poisoned_path", lambda p: "injection/sample.md")
    path = tmp_path / "sample.md"
    path.write_text(inputs["poisoned_corpus"]["documents"]["injection/sample.md"]["text"])
    for text in ("## Attack description", "The unchanged tail stays here.", "harmful"):
        s = source(inputs, text)
        old_source = copy.deepcopy(s)
        old_source["source"] = old_source["metadata"]["source"] = str(path)
        assert legacy.poison_hit_at_3([old_source]) == {
            "poison_hit_at_3": 1, "poisoned_chunks_in_top_3": 1, "poisoned_chunk_ranks": [1]}
        assert measure(inputs, [s])["edited_text_hit_at_3"] == int(text == "harmful")


@pytest.mark.parametrize("kind,reason", [
    ("no_offset", "source_offset_or_content_unavailable"),
    ("bool_offset", "source_offset_or_content_unavailable"),
    ("negative_offset", "source_offset_or_content_unavailable"),
    ("shifted_offset", "source_offset_text_mismatch"),
    ("changed_content", "source_offset_text_mismatch"),
    ("offset_conflict", "source_offsets_conflict"),
    ("unknown_root", "source_identity_unknown_or_conflicting"),
    ("conflicting_path", "source_identity_unknown_or_conflicting"),
    ("basename_collision", "document_snapshot_missing"),
])
def test_missing_conflicting_or_unverified_source_mapping(inputs, kind, reason):
    s = source(inputs, "harmful")
    if kind == "no_offset":
        del s["metadata"]["start_index"]
    elif kind == "bool_offset":
        s["metadata"]["start_index"] = True
    elif kind == "negative_offset":
        s["metadata"]["start_index"] = -1
    elif kind == "shifted_offset":
        s["metadata"]["start_index"] += 1
    elif kind == "changed_content":
        s["content"] = "different"
    elif kind == "offset_conflict":
        s["start_index"] = 0
    elif kind == "unknown_root":
        s["source"] = s["metadata"]["source"] = "/unknown/injection/sample.md"
    elif kind == "conflicting_path":
        s["metadata"]["source"] = "/archived/poisoned/other/sample.md"
    elif kind == "basename_collision":
        s["source"] = s["metadata"]["source"] = "/archived/poisoned/other/sample.md"
    result = measure(inputs, [s])
    assert result["edited_text_hit_at_3"] is None
    assert result["unknown_source_count"] == 1
    assert result["sources"][0]["reason"] == reason


@pytest.mark.parametrize("kind,reason", [
    ("missing_manifest", "attack_manifest_missing"),
    ("manifest_hash", "attack_manifest_checksum_mismatch"),
    ("manifest_entries", "attack_manifest_entries_mismatch"),
    ("duplicate_entry", "conflicting_or_duplicate_manifest_entries"),
    ("conflicting_entry", "conflicting_or_duplicate_manifest_entries"),
    ("original_mismatch", "original_text_mismatch"),
    ("adversarial_mismatch", "adversarial_text_mismatch"),
    ("missing_clean", "document_snapshot_missing"),
    ("document_hash", "document_snapshot_checksum_mismatch"),
    ("duplicate_heading", "section_missing_or_ambiguous"),
    ("unmapped_section", "section_missing_or_ambiguous"),
    ("invalid_path", "manifest_document_identity_unknown"),
])
def test_manifest_mapping_failures_remain_unknown(inputs, kind, reason):
    s = source(inputs, "harmful")
    entries = inputs["attack_manifest"]["entries"]
    if kind == "missing_manifest":
        inputs["attack_manifest"] = None
    elif kind == "manifest_hash":
        inputs["attack_manifest"]["sha256"] = "wrong"
    elif kind == "manifest_entries":
        entries.clear()  # Does not agree with the saved raw JSONL.
    elif kind in {"duplicate_entry", "conflicting_entry"}:
        entries.append(copy.deepcopy(entries[0]))
        if kind == "conflicting_entry":
            entries[-1]["adversarial_text"] = "Conflicting text"
    elif kind == "original_mismatch":
        entries[0]["original_text"] = "Not the saved original"
    elif kind == "adversarial_mismatch":
        entries[0]["adversarial_text"] = "Not the saved poison"
    elif kind == "missing_clean":
        inputs["clean_corpus"]["documents"].clear()
    elif kind == "document_hash":
        inputs["clean_corpus"]["documents"]["injection/sample.md"]["sha256"] = "wrong"
    elif kind == "duplicate_heading":
        clean = inputs["clean_corpus"]
        text = clean["documents"]["injection/sample.md"]["text"] + "\n## Attack description\nMore text.\n"
        inputs["clean_corpus"] = corpus(text, clean["root"])
    elif kind == "unmapped_section":
        entries[0]["section"] = "unknown section"
    elif kind == "invalid_path":
        entries[0]["file"] = "../injection/sample.md"
    if kind not in {"missing_manifest", "manifest_hash", "manifest_entries"}:
        inputs["attack_manifest"] = attack_snapshot(entries)
    index = exposure.build_edit_index(**inputs)
    result = exposure.edited_text_exposure_at_3([s], index=index, poisoned_corpus=inputs["poisoned_corpus"])
    assert result["edited_text_hit_at_3"] is None
    reasons = index["issues"] + [entry["reason"] for entry in index["entries"]]
    assert any(r and r.startswith(reason) for r in reasons)


def test_only_verified_success_entries_supply_edited_spans(inputs):
    for success in (False, "true", None):
        entries = copy.deepcopy(inputs["attack_manifest"]["entries"])
        entries[0]["success"] = success
        inputs["attack_manifest"] = attack_snapshot(entries)
        assert measure(inputs, [source(inputs, "harmful")])["edited_text_hit_at_3"] == 0


def test_empty_manifest_is_not_missing_and_empty_retrieval_is_not_failure(inputs):
    inputs["attack_manifest"] = attack_snapshot([])
    assert measure(inputs, [source(inputs, "harmful")])["edited_text_hit_at_3"] == 0
    empty = measure(inputs, [])
    assert empty["edited_text_hit_at_3"] == 0 and empty["status"] == "ok"
    missing = measure(inputs, None)
    assert missing["edited_text_hit_at_3"] is None and missing["status"] == "retrieval_unavailable"


def test_top_three_duplicates_and_unknown_denominators(inputs):
    edited, unedited = source(inputs, "harmful"), source(inputs, "Other content.")
    assert measure(inputs, [unedited] * 3 + [edited])["edited_text_hit_at_3"] == 0
    duplicate = measure(inputs, [edited, edited])
    assert duplicate["known_edited_source_count"] == 2 and duplicate["edited_source_ranks"] == [1, 2]
    unknown = copy.deepcopy(edited)
    del unknown["metadata"]["start_index"]
    result = measure(inputs, [edited, unedited, unknown])
    assert result["edited_text_hit_at_3"] is None
    assert result["known_edited_source_count"] == result["known_unedited_source_count"] == result["unknown_source_count"] == 1
    assert result["evaluated_source_count"] == 3


@pytest.mark.parametrize("original,adversarial", [("Keep remove tail", "Keep tail"), ("Keep  tail", "Keep tail")])
def test_deletions_and_whitespace_do_not_supply_edited_evidence(original, adversarial):
    entry = {"original_text": original, "adversarial_text": adversarial, "section": "description"}
    result = exposure._entry_mapping(entry, "## Description\n" + original, "## Description\n" + adversarial)
    assert result["edited_spans"] == []
    assert result["deleted_character_count"] > 0


def test_unicode_offsets_are_characters_not_bytes(inputs):
    for key in ("clean_corpus", "poisoned_corpus"):
        old = inputs[key]
        inputs[key] = corpus("é🙂\n" + old["documents"]["injection/sample.md"]["text"], old["root"])
    assert measure(inputs, [source(inputs, "harmful")])["edited_text_hit_at_3"] == 1


def test_inserted_text_is_counted_but_added_whitespace_is_not():
    entry = {"original_text": "Keep tail", "adversarial_text": "Keep new tail", "section": "description"}
    poisoned = "## Description\n" + entry["adversarial_text"]
    result = exposure._entry_mapping(entry, "## Description\nKeep tail", poisoned)
    assert "".join(poisoned[a:b] for a, b in result["edited_spans"]) == "new"
    entry["adversarial_text"] = "Keep   tail"
    assert exposure._entry_mapping(entry, "## Description\nKeep tail", "## Description\nKeep   tail")["edited_spans"] == []


def test_index_cannot_be_reused_with_conflicting_corpus_version(inputs):
    index = exposure.build_edit_index(**inputs)
    old = inputs["poisoned_corpus"]
    text = old["documents"]["injection/sample.md"]["text"].replace("Other content.", "Updated content.")
    inputs["poisoned_corpus"] = corpus(text, old["root"])
    result = exposure.edited_text_exposure_at_3(
        [source(inputs, "harmful")], index=index, poisoned_corpus=inputs["poisoned_corpus"])
    assert result["edited_text_hit_at_3"] is None
    assert result["sources"][0]["reason"] == "source_snapshot_conflict"


def saved_run(tmp_path, inputs, chunks=("## Attack description", "harmful", None)):
    schedule = [{"index": i, "question_id": "related-question", "repetition": i + 1,
                 "source_group_ids": ["documented-group"], "condition_order": ["clean", "poisoned"]}
                for i in range(len(chunks))]
    names = [f"{i:06d}-poisoned-{stage}.json" for i in range(len(chunks)) for stage in ("rag", "retrieval")]
    manifest = {"schema_version": 1, "execution_backend": "synthetic", "expected_records": names,
                "schedule": schedule, "specification": {"data": {"dataset_namespace": inputs["namespace"]}},
                "corpora": {"clean": inputs["clean_corpus"], "poisoned": inputs["poisoned_corpus"]},
                "attack_manifest": inputs["attack_manifest"], "benchmark": {"sha256": "synthetic"}}
    store = RunStore(tmp_path, manifest)
    for unit, chunk in zip(schedule, chunks):
        base = {"schema_version": 1, "run_id": store.path.name, **unit, "condition": "poisoned"}
        capture = {"retrieval_status": "unavailable"} if chunk is None else {
            "retrieval_status": "ok", "sources": [source(inputs, chunk)], "generation_status": "unavailable"}
        store.write(f"{unit['index']:06d}-poisoned-rag.json", {**base, "stage": "rag", "capture": capture})
        store.write(f"{unit['index']:06d}-poisoned-retrieval.json", {
            **base, "stage": "retrieval", "value": {"poison_exposure": {
                "poison_hit_at_3": None if chunk is None else 1, "poisoned_chunk_ranks": [] if chunk is None else [1]}}})
    store.finish(names)
    return store.path


def test_offline_replay_keeps_pairing_legacy_values_and_generation_failure_evidence(inputs, tmp_path, monkeypatch):
    run = saved_run(tmp_path, inputs)
    originals = {p: p.read_bytes() for p in run.rglob("*.json")}
    original_read = Path.read_bytes

    def only_saved_run(path):
        assert path.is_relative_to(run), "Must not consult present-day corpus/manifest files"
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", only_saved_run)
    report = exposure.analyze_run(run)
    assert report["record_integrity_complete"]
    assert report["mapping"]["verified_entry_count"] == 1
    assert report["summary"]["valid_observation_count"] == 2
    assert report["summary"]["unavailable_observation_count"] == 1
    assert report["summary"]["edited_text_hit_at_3_rate"] == .5
    assert report["summary"]["legacy_attacked_section_hit_at_3_rate"] == 1
    assert report["summary"]["legacy_hit_without_edited_text_count"] == 1
    assert [o["repetition"] for o in report["observations"]] == [1, 2, 3]
    assert all(o["source_group_ids"] == ["documented-group"] for o in report["observations"])
    assert report["observations"][0]["legacy_saved_poison_exposure"]["poisoned_chunk_ranks"] == [1]
    assert report["corpus_provenance"]["poisoned"]["indexed_content_sha256"] is None
    assert originals == {p: p.read_bytes() for p in originals}


@pytest.mark.parametrize("damage", ["missing_record", "truncated_record", "missing_completion", "manifest_checksum"])
def test_incomplete_saved_runs_are_explicit(inputs, tmp_path, damage):
    run = saved_run(tmp_path, inputs)
    rag = run / "observations/000001-poisoned-rag.json"
    if damage == "missing_record":
        rag.unlink()
    elif damage == "truncated_record":
        rag.write_text('{"schema_version":')
    elif damage == "missing_completion":
        (run / "completion.json").unlink()
    else:
        path = run / "manifest.json"
        path.write_text(path.read_text() + " ")
    report = exposure.analyze_run(run)
    assert not report["record_integrity_complete"] and report["issues"]
    if damage != "manifest_checksum":
        assert report["summary"]["scheduled_observation_count"] == 3
    if damage in {"missing_record", "truncated_record"}:
        assert report["observations"][1]["edited_text_exposure"]["edited_text_hit_at_3"] is None


def test_cli_is_create_only_and_never_writes_inside_original_run(inputs, tmp_path):
    run = saved_run(tmp_path, inputs)
    output = tmp_path / "separate-analysis.json"
    assert exposure.main(["--run", str(run), "--output", str(output)]) == 0
    data = output.read_bytes()
    assert json.loads(data)["metric_version"] == exposure.METRIC_VERSION
    with pytest.raises(FileExistsError):
        exposure.main(["--run", str(run), "--output", str(output)])
    assert output.read_bytes() == data
    with pytest.raises(SystemExit):
        exposure.main(["--run", str(run), "--output", str(run / "new-report.json")])
    assert not (run / "new-report.json").exists()


def test_failed_retrievals_have_null_rate_and_do_not_become_negative_results(inputs, tmp_path):
    report = exposure.analyze_run(saved_run(tmp_path, inputs, chunks=(None, None)))
    assert report["summary"]["valid_observation_count"] == 0
    assert report["summary"]["unavailable_observation_count"] == 2
    assert report["summary"]["edited_text_hit_at_3_rate"] is None


def test_mismatched_pairing_cannot_be_scored(inputs, tmp_path, monkeypatch):
    run = saved_run(tmp_path, inputs, chunks=("harmful",))
    manifest, records, issues = exposure.read_run(run)
    records["000000-poisoned-rag.json"]["question_id"] = "a-different-question"
    monkeypatch.setattr(exposure, "read_run", lambda p: (manifest, records, issues))
    result = exposure.analyze_run(run)
    assert not result["record_integrity_complete"]
    assert result["observations"][0]["edited_text_exposure"]["edited_text_hit_at_3"] is None
