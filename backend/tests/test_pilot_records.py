"""Disposable synthetic record/provenance fixtures; no research data writes."""

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.evaluation import pilot_records as records


def test_create_only_files_and_run_directories(tmp_path, monkeypatch):
    target = tmp_path / "report.json"
    records.write_new_json(target, {"original": True})
    with pytest.raises(FileExistsError):
        records.write_new_json(target, {"replacement": True})
    assert json.loads(target.read_text()) == {"original": True}

    class FixedDate:
        @staticmethod
        def now(zone):
            return datetime(2026, 9, 13, tzinfo=timezone.utc)

    monkeypatch.setattr(records, "datetime", FixedDate)
    monkeypatch.setattr(records.uuid, "uuid4", lambda: SimpleNamespace(hex="fixed"))
    manifest = {"schema_version": 1, "expected_records": []}
    first = records.RunStore(tmp_path, manifest)
    with pytest.raises(FileExistsError):
        records.RunStore(tmp_path, manifest)
    assert (first.path / "manifest.json").exists()


def test_strict_json_retains_nonfinite_and_malformed_values(tmp_path):
    path = tmp_path / "scores.json"
    records.write_new_json(path, {"nan": float("nan"), "inf": float("inf"),
                                  "bool": False, "string": "0.5", "object": object()})
    saved = json.loads(path.read_text(), parse_constant=lambda _: pytest.fail("Non-standard JSON"))
    assert saved["nan"] == {"__pilot_nonfinite__": "nan"}
    assert saved["inf"] == {"__pilot_nonfinite__": "inf"}
    assert saved["bool"] is False
    assert saved["string"] == "0.5"
    assert saved["object"] == {"__pilot_malformed_type__": "object"}


def test_allowlist_rejects_credentials_and_credential_urls():
    config = dict.fromkeys(records.CONFIG_KEYS, "value")
    config["QDRANT_URL"] = "http://localhost:6333"
    assert records.allowlisted_config(config) == config
    with pytest.raises(ValueError):
        records.allowlisted_config({**config, "LLM_API_KEY": "never-export"})
    for url in ("https://user:password@example.test", "https://example.test?token=secret"):
        with pytest.raises(ValueError):
            records.allowlisted_config({**config, "QDRANT_URL": url})


def test_snapshot_fingerprints_are_local_and_do_not_read_environment(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.md").write_text("# Source\nEvidence")
    (root / ".env").write_text("DO_NOT_READ=this-is-a-test")
    first = records.snapshot_corpus(root)
    assert set(first["documents"]) == {"a.md"}
    assert first["indexed_content_sha256"] is None
    assert first["indexed_content_status"] == "unverified"
    assert records.snapshot_corpus(root)["sha256"] == first["sha256"]
    (root / "a.md").write_text("# Source\nChanged")
    assert records.snapshot_corpus(root)["sha256"] != first["sha256"]


def test_documented_groups_merge_shared_references_and_reject_ambiguity():
    def doc(key, reference):
        return {"text": f"# Title\n## Metadata\n- Attack key: `{key}`\n- ATT&CK ID: `{reference}`\n## Body\ntext"}
    corpus = {"documents": {"first/a.md": doc("a", "T1"), "second/b.md": doc("b", "T1"),
                             "third/c.md": doc("c", "T2")}}
    questions = [{"id": key, "expected_attack_type": key} for key in "abc"]
    result = records.documented_groups(questions, corpus, "synthetic")
    assert len(result["groups"]) == 2
    assert result["question_groups"]["a"] == result["question_groups"]["b"]
    assert result["question_groups"]["a"] != result["question_groups"]["c"]
    corpus["documents"]["duplicate/a.md"] = doc("a", "T3")
    with pytest.raises(ValueError, match="Ambiguous"):
        records.documented_groups(questions, corpus, "synthetic")


@pytest.mark.parametrize("damage", ["record_truncated", "record_missing", "completion_missing", "checksum_changed"])
def test_incomplete_or_modified_runs_are_explicit(tmp_path, damage):
    name = "000000-clean-rag.json"
    store = records.RunStore(tmp_path, {"schema_version": 1, "expected_records": [name]})
    store.write(name, {"schema_version": 1, "answer": "synthetic"})
    store.finish([name])
    assert records.read_run(store.path)[2] == []
    target = store.path / "observations" / name
    if damage == "record_truncated":
        target.write_text('{"schema_version":')
    elif damage == "record_missing":
        target.unlink()
    elif damage == "completion_missing":
        (store.path / "completion.json").unlink()
    else:
        target.write_text('{"schema_version": 1, "answer": "changed"}')
    assert records.read_run(store.path)[2]


def test_manifest_truncation_and_record_name_traversal_are_rejected(tmp_path):
    store = records.RunStore(tmp_path, {"schema_version": 1, "expected_records": []})
    with pytest.raises(ValueError):
        store.write("../report.json", {})
    (store.path / "manifest.json").write_text('{"schema_version":')
    manifest, _, issues = records.read_run(store.path)
    assert manifest is None and issues


def test_code_provenance_includes_untracked_relevant_bytes_without_env(tmp_path, monkeypatch):
    source = tmp_path / "backend/app/evaluation/pilot_runner.py"
    source.parent.mkdir(parents=True)
    source.write_text("# untracked source")
    monkeypatch.setattr(records.subprocess, "check_output", lambda *args, **kwargs: "?? synthetic\n")
    result = records.code_provenance(tmp_path)
    assert result["file_sha256"]["backend/app/evaluation/pilot_runner.py"] == records.sha256(source.read_bytes())
    assert all(".env" not in name for name in result["file_sha256"])
