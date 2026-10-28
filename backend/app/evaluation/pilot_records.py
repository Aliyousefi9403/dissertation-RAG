"""Small, local-only pilot records."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

CONFIG_KEYS = (
    "LLM_PROVIDER", "LLM_MODEL", "LLM_TEMPERATURE", "EMBEDDING_MODEL",
    "CHUNK_SIZE", "CHUNK_OVERLAP", "RETRIEVAL_TOP_K", "QDRANT_URL", "QDRANT_COLLECTIONS",
)
RELEVANT_FILES = (
    "pyproject.toml", "backend/app/config.py", "backend/app/generation/rag_chain.py",
    "backend/app/generation/prompt.py", "backend/app/generation/llm_factory.py",
    "backend/app/retrieval/search.py", "backend/app/vectorstore/qdrant_store.py",
    "backend/app/ingestion/section_metadata.py", "backend/app/evaluation/llm_judge.py",
    "backend/app/evaluation/retrieval_metrics.py", "backend/app/evaluation/compare_metrics.py",
    "backend/app/evaluation/paired_metrics.py", "backend/app/evaluation/source_identity.py",
    "backend/app/evaluation/pwws_manifest.py", "backend/app/evaluation/pilot_runner.py",
    "backend/app/evaluation/pilot_records.py", "backend/app/kb_builder/source_mapping.yaml",
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes):
    return hashlib.sha256(data).hexdigest()


def json_safe(value):
    """Retain malformed values without emitting non-standard JSON NaN/Infinity."""
    if isinstance(value, float) and not math.isfinite(value):
        return {"__pilot_nonfinite__": repr(value)}
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    return {"__pilot_malformed_type__": type(value).__name__}


def write_new_json(path: Path, value):
    # Serialize before opening so a serialization error cannot leave an empty file.
    data = json.dumps(json_safe(value), indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(data)
        stream.flush()


def allowlisted_config(values):
    if set(values) != set(CONFIG_KEYS):
        raise ValueError("Configuration must contain exactly CONFIG_KEYS; credentials are forbidden")
    result = {key: values[key] for key in CONFIG_KEYS}
    url = urlsplit(result["QDRANT_URL"])
    if url.username or url.password or url.query or url.fragment:
        raise ValueError("Qdrant URL must not embed credentials, queries, or fragments")
    return result


def snapshot_json(path: Path):
    if path.suffix != ".json" or path.is_symlink():
        raise ValueError("Expected a regular JSON input")
    raw = path.read_bytes()
    return {"path": str(path), "sha256": sha256(raw), "text": raw.decode("utf-8"),
            "data": json.loads(raw)}


def snapshot_corpus(root: Path):
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Corpus root must be an existing non-symlink directory")
    files = {}
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root):
            raise ValueError("Symlink corpus entries require explicit provenance review")
        raw = path.read_bytes()
        files[relative.as_posix()] = {"sha256": sha256(raw), "text": raw.decode("utf-8")}
    if not files:
        raise ValueError("Corpus contains no Markdown documents")
    fingerprint = sha256(json.dumps(
        {key: value["sha256"] for key, value in files.items()}, sort_keys=True
    ).encode())
    return {"root": str(root), "sha256": fingerprint, "documents": files,
            "indexed_content_sha256": None, "indexed_content_status": "unverified"}


def code_provenance(project_root: Path):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(project_root), *args], text=True).strip()

    try:
        revision = git("rev-parse", "HEAD")
        dirty = git("status", "--porcelain", "--untracked-files=all", "--", *RELEVANT_FILES)
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    files = {}
    for name in RELEVANT_FILES:
        path = project_root / name
        files[name] = sha256(path.read_bytes()) if path.is_file() and not path.is_symlink() else None
    versions = {"python": platform.python_version()}
    for name in ("langchain-core", "langchain-openai", "qdrant-client", "sentence-transformers"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {"revision": revision, "relevant_dirty_status": dirty, "file_sha256": files,
            "versions": versions}


def documented_groups(questions, corpus, namespace):
    """Components of shared CAPEC/ATT&CK IDs in generated document metadata."""
    catalog = {}
    for path, document in corpus["documents"].items():
        metadata = document["text"].split("## Metadata", 1)
        if len(metadata) != 2:
            continue
        metadata = metadata[1].split("\n## ", 1)[0]
        key = re.search(r"Attack key:\s*`([^`]+)`", metadata)
        if key:
            catalog.setdefault(key[1], []).append((path, sorted(set(re.findall(
                r"(?:CAPEC ID|ATT&CK ID):\s*`([^`]+)`", metadata
            )))))
    documents = {}
    question_paths = {}
    for question in questions:
        candidates = catalog.get(question["expected_attack_type"], [])
        if len(candidates) != 1 or not candidates[0][1]:
            raise ValueError(f"Ambiguous or undocumented source mapping for {question['id']}")
        path, references = candidates[0]
        question_paths[question["id"]] = path
        documents[path] = references
    remaining = set(documents)
    groups = {}
    while remaining:
        component = {min(remaining)}
        while True:
            refs = {ref for path in component for ref in documents[path]}
            expanded = component | {path for path in remaining if refs.intersection(documents[path])}
            if expanded == component:
                break
            component = expanded
        remaining -= component
        group_id = namespace + ":group:" + sha256("\n".join(sorted(component)).encode())[:12]
        groups[group_id] = {"documents": sorted(component),
                            "documented_references": sorted({ref for p in component for ref in documents[p]})}
    mapping = {qid: [gid for gid, group in groups.items() if path in group["documents"]]
               for qid, path in question_paths.items()}
    return {"policy": "shared_documented_ids_v1", "question_groups": mapping, "groups": groups,
            "limitation": "Only relationships documented in generated metadata are known; independence is not established"}


class RunStore:
    def __init__(self, root: Path, manifest):
        self.path = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex)
        self.path.mkdir(parents=True, exist_ok=False)
        (self.path / "observations").mkdir()
        write_new_json(self.path / "manifest.json", {**manifest, "run_id": self.path.name})

    def write(self, name, record):
        if not re.fullmatch(r"\d{6}-(?:(?:clean|poisoned)-(?:rag|retrieval|correctness|faithfulness)|pair)\.json", name):
            raise ValueError("Invalid observation filename")
        write_new_json(self.path / "observations" / name, record)

    def finish(self, expected):
        hashes = {name: sha256((self.path / "observations" / name).read_bytes()) for name in expected}
        write_new_json(self.path / "completion.json", {
            "finished_at": utc_now(), "manifest_sha256": sha256((self.path / "manifest.json").read_bytes()),
            "record_sha256": hashes,
        })


def read_run(path: Path):
    issues = []
    try:
        manifest = json.loads((path / "manifest.json").read_text())
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise ValueError("Unsupported manifest version")
        expected = manifest["expected_records"]
        if not isinstance(expected, list) or any(not isinstance(name, str) for name in expected):
            raise ValueError("Invalid expected record list")
        if len(expected) != len(set(expected)) or any(Path(name).name != name for name in expected):
            raise ValueError("Invalid expected record names")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return None, {}, [f"manifest_unreadable:{type(exc).__name__}"]
    try:
        completion = json.loads((path / "completion.json").read_text())
        if not isinstance(completion, dict) or not isinstance(completion.get("record_sha256"), dict):
            raise ValueError("Invalid completion record")
        if completion.get("manifest_sha256") != sha256((path / "manifest.json").read_bytes()):
            return None, {}, ["manifest_checksum_mismatch"]
    except (OSError, ValueError) as exc:
        completion = {}
        issues.append(f"completion_unreadable:{type(exc).__name__}")
    records = {}
    for name in expected:
        try:
            raw = (path / "observations" / name).read_bytes()
            record = json.loads(raw)
            if not isinstance(record, dict) or record.get("schema_version") != 1:
                raise ValueError("Invalid record")
            if completion and completion.get("record_sha256", {}).get(name) != sha256(raw):
                issues.append(f"record_checksum_mismatch:{name}")
                continue
            records[name] = record
        except (OSError, ValueError) as exc:
            issues.append(f"record_unreadable:{name}:{type(exc).__name__}")
    extra = {p.name for p in (path / "observations").glob("*")} - set(expected)
    issues.extend(f"unexpected_record:{name}" for name in sorted(extra))
    return manifest, records, issues
