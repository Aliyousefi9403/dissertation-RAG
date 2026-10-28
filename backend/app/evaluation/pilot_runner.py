"""Minimal supervised pilot: --dry-run, --execute, or --aggregate RUN_DIR."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from statistics import mean
from time import perf_counter

from app.evaluation.paired_metrics import build_paired_metrics, classify_score
from app.evaluation.pilot_records import (
    CONFIG_KEYS,
    RunStore,
    allowlisted_config,
    code_provenance,
    documented_groups,
    json_safe,
    read_run,
    sha256,
    snapshot_corpus,
    snapshot_json,
    utc_now,
    write_new_json,
)
from app.evaluation.source_identity import build_document_overlap, resolve_document_identity

PROJECT_ROOT = Path(__file__).absolute().parents[3]
METRIC_VERSIONS = {
    "paired_metrics": 1, "document_overlap": 1,
    "retrieval": "section_overlap_v1", "poison_exposure": "successful_section_overlap_v1",
    "attack_success": "poison_hit_and_correctness_drop_0.25_v1",
    "judge_availability": "raw_finite_unit_interval_v2",
}
STAGES = ("rag", "retrieval", "correctness", "faithfulness")


def pilot_score(value):
    """Pilot-only rubric validation; legacy/general score contracts stay intact."""
    score, status = classify_score(value)
    if status == "valid" and not 0 <= score <= 1:
        return None, "malformed"
    return score, status


def paired_score_value(raw):
    score, status = pilot_score(raw)
    return {"invalid_pilot_score": json_safe(raw)} if status == "malformed" else score


def record_name(unit, condition, stage):
    return f"{unit['index']:06d}-{condition}-{stage}.json"


def prepare(spec_path: Path, project_root=PROJECT_ROOT):
    """Validate and snapshot local inputs only; no output or external calls."""
    spec_snapshot = snapshot_json(spec_path)
    spec = spec_snapshot["data"]
    required = {"schema_version", "benchmark", "repetitions", "dataset_namespace", "corpus_roots",
                "source_group_policy", "attack_manifest", "attack_summary", "expected_config", "requests"}
    if set(spec) != required or spec["schema_version"] != 1:
        raise ValueError("Pilot specification requires exactly the documented version-1 fields")
    if type(spec["repetitions"]) is not int or spec["repetitions"] < 1:
        raise ValueError("repetitions must be an explicit positive integer")
    if not isinstance(spec["dataset_namespace"], str) or not spec["dataset_namespace"].strip():
        raise ValueError("A dataset namespace is required")
    if spec["source_group_policy"] != "shared_documented_ids_v1":
        raise ValueError("Source groups require the documented metadata relationship policy")
    if set(spec["corpus_roots"]) != {"clean", "poisoned"}:
        raise ValueError("Pilot requires clean and poisoned roots only")
    requests = spec["requests"]
    if set(requests) != {"timeout_seconds", "max_retries", "retrieval_timeout_seconds"}:
        raise ValueError("Explicit model timeout, retry limit and retrieval timeout are required")
    for key in ("timeout_seconds", "retrieval_timeout_seconds"):
        if type(requests[key]) not in (int, float) or not math.isfinite(requests[key]) or requests[key] <= 0:
            raise ValueError("Timeouts must be finite positive numbers")
    if type(requests["max_retries"]) is not int or not 0 <= requests["max_retries"] <= 3:
        raise ValueError("max_retries must be between 0 and 3")

    def input_path(value):
        return Path(value) if Path(value).is_absolute() else project_root / value

    benchmark = snapshot_json(input_path(spec["benchmark"]))
    questions = benchmark["data"]
    if not isinstance(questions, list) or not questions:
        raise ValueError("Benchmark must contain questions")
    for item in questions:
        if not all(isinstance(item.get(key), str) and item[key] for key in ("id", "question", "expected_attack_type")):
            raise ValueError("Question identity and expected attack type are required")
        if not isinstance(item.get("expected_sections"), list) or not isinstance(item.get("reference_facts"), list):
            raise ValueError("Expected sections and reference facts are required")
    if len({item["id"] for item in questions}) != len(questions):
        raise ValueError("Duplicate question IDs")
    corpora = {state: snapshot_corpus(input_path(root)) for state, root in spec["corpus_roots"].items()}
    groups = documented_groups(questions, corpora["clean"], spec["dataset_namespace"])
    manifest_path = input_path(spec["attack_manifest"])
    if manifest_path.suffix != ".jsonl" or manifest_path.is_symlink():
        raise ValueError("Attack manifest must be a regular JSONL input")
    raw = manifest_path.read_bytes()
    attack_manifest = {"path": str(manifest_path), "sha256": sha256(raw), "text": raw.decode(),
                       "entries": [json.loads(line) for line in raw.decode().splitlines() if line.strip()]}
    attack_summary = snapshot_json(input_path(spec["attack_summary"])) if spec["attack_summary"] else None
    schedule = []
    for repetition in range(spec["repetitions"]):
        for position, question in enumerate(questions):
            # Odd repetitions cannot balance each question exactly. Alternating
            # the starting condition across questions balances an even benchmark.
            order = ["clean", "poisoned"] if (repetition + position) % 2 == 0 else ["poisoned", "clean"]
            schedule.append({"index": len(schedule), "question_id": question["id"],
                             "repetition": repetition + 1, "source_group_ids": groups["question_groups"][question["id"]],
                             "condition_order": order})
    expected = []
    for unit in schedule:
        expected.extend(record_name(unit, condition, stage) for condition in unit["condition_order"] for stage in STAGES)
        expected.append(f"{unit['index']:06d}-pair.json")
    logical = {"generation": 2 * len(schedule), "judge": 4 * len(schedule)}
    return {
        "schema_version": 1, "prepared_at": utc_now(), "specification": spec_snapshot,
        "benchmark": benchmark, "corpora": corpora, "source_groups": groups,
        "attack_manifest": attack_manifest, "attack_summary": attack_summary,
        "requested_config": allowlisted_config(spec["expected_config"]),
        "effective_config_verified": False, "code": code_provenance(project_root),
        "requests": {**requests, "sdk_model_retries": 0, "retrieval_adapter_retries": 0},
        "nominal_logical_calls": logical,
        "maximum_model_attempts": {key: value * (1 + requests["max_retries"]) for key, value in logical.items()},
        "retrieval_logical_operations": logical["generation"],
        "schedule": schedule, "expected_records": expected, "metric_versions": METRIC_VERSIONS,
        "model_seed": None, "model_seed_status": "not_configured_or_guaranteed",
        "local_model_revision": None, "local_model_revision_status": "not_verified",
    }


def bounded_invoke(invoke, prompt, *, max_retries, capture):
    """Model transport retry loop. SDK retries must be disabled by the caller."""
    for attempt in range(max_retries + 1):
        capture["request_attempts"] = attempt + 1
        try:
            return invoke(prompt)
        except Exception as exc:
            capture.setdefault("attempt_errors", []).append({"attempt": attempt + 1, "type": type(exc).__name__})
            status = getattr(exc, "status_code", None)
            retryable = isinstance(exc, (TimeoutError, ConnectionError)) or type(exc).__name__ in {
                "APITimeoutError", "APIConnectionError",
            } or (isinstance(status, int) and (status == 429 or status >= 500))
            if not retryable or attempt == max_retries:
                raise


class LiveServices:
    kind = "live"

    def __init__(self, plan):
        # Downloads are forbidden even in the explicitly executed pilot.
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        from app import config
        from app.evaluation import compare_metrics, llm_judge, pwws_manifest, retrieval_metrics
        from app.generation import rag_chain
        from app.ingestion import section_metadata

        self.config, self.plan = config, plan
        self.rag, self.judges = rag_chain, llm_judge
        self.metrics, self.attack = retrieval_metrics, compare_metrics
        self.sections = section_metadata
        effective = allowlisted_config({key: getattr(config, key) for key in CONFIG_KEYS})
        if effective != plan["requested_config"] or config.LLM_PROVIDER.lower() != "openai":
            raise ValueError("Effective runtime configuration differs from the reviewed specification")
        for state, corpus in plan["corpora"].items():
            if str(config.KNOWLEDGE_BASE_PATHS[state]) != corpus["root"]:
                raise ValueError("Runtime corpus root differs from snapshot")
        for configured, snapshot in ((retrieval_metrics.QUESTIONS_FILE, plan["benchmark"]),
                                     (pwws_manifest.MANIFEST_FILE, plan["attack_manifest"])):
            if str(configured) != snapshot["path"] or sha256(configured.read_bytes()) != snapshot["sha256"]:
                raise ValueError("Runtime benchmark/manifest differs from snapshot")
        retrieval_metrics.load_questions.cache_clear()
        pwws_manifest.get_successful_entries_by_file.cache_clear()
        self.embeddings = None
        self.effective_config = effective

    def factory(self, capture):
        def create(temperature=None):
            from langchain_core.runnables import RunnableLambda
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(
                model=self.config.LLM_MODEL, api_key=self.config.LLM_API_KEY,
                temperature=self.config.LLM_TEMPERATURE if temperature is None else temperature,
                timeout=self.plan["requests"]["timeout_seconds"], max_retries=0,
            )
            return RunnableLambda(lambda prompt: bounded_invoke(
                model.invoke, prompt, max_retries=self.plan["requests"]["max_retries"], capture=capture
            ))
        return create

    def retrieve(self, question, system_state):
        # Same existing embedding implementation and dense similarity retrieval;
        # only the pilot transport timeout is explicitly supplied here.
        from langchain_qdrant import QdrantVectorStore

        from app.vectorstore.qdrant_store import get_embeddings

        if self.embeddings is None:
            self.embeddings = get_embeddings()
        store = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings, collection_name=self.config.get_qdrant_collection(system_state),
            url=self.config.QDRANT_URL, timeout=self.plan["requests"]["retrieval_timeout_seconds"],
        )
        return store.similarity_search_with_score(question, k=self.config.RETRIEVAL_TOP_K)

    def answer(self, question, condition, capture):
        return self.rag.answer_question(question, system_state=condition, capture=capture,
                                       llm_factory=self.factory(capture), retrieval_fn=self.retrieve)

    def judge(self, stage, question, sources, answer, capture):
        if stage == "correctness":
            return self.judges.evaluate_correctness(question["question"], question["reference_facts"], answer,
                                                    capture=capture, llm_factory=self.factory(capture))
        context = "\n\n".join(f"[Source {i}]\n{s.get('content', '')}" for i, s in enumerate(sources, 1))
        return self.judges.evaluate_faithfulness(question["question"], context, answer,
                                                capture=capture, llm_factory=self.factory(capture))

    def retrieval_metrics(self, question, sources, condition):
        roots = {value["root"]: self.plan["specification"]["data"]["dataset_namespace"]
                 for value in self.plan["corpora"].values()}
        # Refuse to let old query-time section lookup read an arbitrary path or
        # silently calculate against bytes different from the archived inputs.
        for source in sources[:3]:
            if resolve_document_identity(source, corpus_roots=roots) is None:
                raise ValueError("Unresolved source identity; retrieval metric unavailable")
            path = Path(source.get("source") or source["metadata"]["source"])
            for corpus in self.plan["corpora"].values():
                if path.is_relative_to(corpus["root"]):
                    expected = corpus["documents"].get(path.relative_to(corpus["root"]).as_posix())
                    if expected is None or sha256(path.read_bytes()) != expected["sha256"]:
                        raise ValueError("Source bytes changed or were not snapshotted")
        manifest = self.plan["attack_manifest"]
        if sha256(Path(manifest["path"]).read_bytes()) != manifest["sha256"]:
            raise ValueError("Attack manifest changed")
        self.sections._read_file.cache_clear()
        hit, rr = self.metrics.hit_at_3_and_reciprocal_rank(
            sources, question["expected_attack_type"], question["expected_sections"]
        )
        poison = self.metrics.poison_hit_at_3(sources) if condition == "poisoned" else None
        return {"hit_at_3": hit, "reciprocal_rank": rr, "poison_exposure": poison}

    def attack_success(self, poison_hit, clean, poisoned):
        return self.attack.build_attack_success(
            {"poison_hit_at_3": poison_hit},
            {"clean_answer_correctness": clean, "poisoned_answer_correctness": poisoned},
        )


def execute(plan, output_root: Path, *, services=None):
    """Called only by --execute or an explicitly injected mocked rehearsal."""
    services = services if services is not None else LiveServices(plan)
    manifest = {**plan, "started_at": utc_now(), "execution_backend": services.kind,
                "effective_config": services.effective_config, "effective_config_verified": services.kind == "live"}
    store = RunStore(output_root, manifest)
    questions = {item["id"]: item for item in plan["benchmark"]["data"]}
    roots = {corpus["root"]: plan["specification"]["data"]["dataset_namespace"] for corpus in plan["corpora"].values()}
    for unit in plan["schedule"]:
        question = questions[unit["question_id"]]
        outcomes = {}
        for position, condition in enumerate(unit["condition_order"], 1):
            base = {"schema_version": 1, "run_id": store.path.name, **unit, "condition": condition,
                    "execution_position": position, "metric_versions": METRIC_VERSIONS}
            capture = {"request_attempts": 0}
            started = utc_now()
            clock = perf_counter()
            try:
                result = services.answer(question["question"], condition, capture)
                answer = result["answer"]
            except Exception as exc:
                answer = None
                capture.setdefault("error", {"stage": "rag", "type": type(exc).__name__})
                capture.setdefault("generation_status", "unavailable")
            rag = {**base, "stage": "rag", "started_at": started, "finished_at": utc_now(),
                   "latency_seconds": perf_counter() - clock, "answer": answer, "capture": capture}
            store.write(record_name(unit, condition, "rag"), rag)
            sources = capture.get("sources") if capture.get("retrieval_status") == "ok" else None
            retrieval = {**base, "stage": "retrieval", "value": None,
                         "inputs": {"question": question, "sources": sources,
                                    "source_documents": "manifest.corpora", "attack_manifest": "manifest.attack_manifest"}}
            if sources is not None:
                try:
                    retrieval["value"] = services.retrieval_metrics(question, sources, condition)
                except Exception as exc:
                    retrieval["error"] = {"stage": "retrieval_metrics", "type": type(exc).__name__}
            else:
                retrieval["unavailable_reason"] = "retrieval_did_not_return"
            store.write(record_name(unit, condition, "retrieval"), retrieval)
            judgments = {}
            for stage in ("correctness", "faithfulness"):
                audit = {"raw_score": None, "status": "missing", "request_attempts": 0}
                started = utc_now()
                clock = perf_counter()
                if answer is None:
                    audit["unavailable_reason"] = "generation_unavailable_not_judged"
                else:
                    try:
                        audit["legacy_result"] = services.judge(stage, question, sources or [], answer, audit)
                    except Exception as exc:
                        audit["error"] = {"stage": stage, "type": type(exc).__name__}
                record = {**base, "stage": stage, "started_at": started, "finished_at": utc_now(),
                          "latency_seconds": perf_counter() - clock, "capture": audit}
                store.write(record_name(unit, condition, stage), record)
                judgments[stage] = audit
            outcomes[condition] = {"sources": sources, "retrieval": retrieval["value"], "judgments": judgments}
        clean, poisoned = outcomes["clean"], outcomes["poisoned"]
        overlap = None
        if clean["sources"] is not None and poisoned["sources"] is not None:
            overlap = build_document_overlap(clean["sources"], poisoned["sources"], corpus_roots=roots)
        exposure = (poisoned["retrieval"] or {}).get("poison_exposure") or {}
        attack = services.attack_success(
            exposure.get("poison_hit_at_3"), pilot_score(clean["judgments"]["correctness"]["raw_score"])[0],
            pilot_score(poisoned["judgments"]["correctness"]["raw_score"])[0],
        )
        store.write(f"{unit['index']:06d}-pair.json", {
            "schema_version": 1, "run_id": store.path.name, **unit, "metric_versions": METRIC_VERSIONS,
            "document_overlap": overlap, "overlap_unavailable_reason": None if overlap else "retrieval_did_not_return",
            "attack_success": attack,
            "attack_inputs": {"poison_hit_at_3": exposure.get("poison_hit_at_3"),
                              "clean_correctness": pilot_score(clean["judgments"]["correctness"]["raw_score"])[0],
                              "poisoned_correctness": pilot_score(poisoned["judgments"]["correctness"]["raw_score"])[0],
                              "threshold": 0.25},
        })
    store.finish(plan["expected_records"])
    return store.path


def aggregate(run_path: Path):
    """Offline only. No live metric modules, corpus reads, or model imports."""
    manifest, records, issues = read_run(run_path)
    if manifest is None:
        return {"complete": False, "issues": issues}
    score_rows, overlaps, successes = [], [], []
    errors, attempts = 0, {"generation": 0, "judge": 0}
    retrieval = {f"{condition}_{metric}": [] for condition in ("clean", "poisoned") for metric in ("hit_at_3", "reciprocal_rank")}
    for unit in manifest["schedule"]:
        row = {}
        for condition in ("clean", "poisoned"):
            for stage, field in (("correctness", "answer_correctness"), ("faithfulness", "faithfulness")):
                record = records.get(record_name(unit, condition, stage), {})
                audit = record.get("capture", {})
                row[f"{condition}_{field}"] = paired_score_value(audit.get("raw_score"))
                attempts["judge"] += audit.get("request_attempts", 0)
            rag = records.get(record_name(unit, condition, "rag"), {})
            attempts["generation"] += rag.get("capture", {}).get("request_attempts", 0)
            saved = records.get(record_name(unit, condition, "retrieval"), {}).get("value") or {}
            for metric in ("hit_at_3", "reciprocal_rank"):
                value, _ = classify_score(saved.get(metric))
                if value is not None:
                    retrieval[f"{condition}_{metric}"].append(value)
        score_rows.append(row)
        pair = records.get(f"{unit['index']:06d}-pair.json", {})
        roots = {corpus["root"]: manifest["specification"]["data"]["dataset_namespace"]
                 for corpus in manifest["corpora"].values()}
        captures = [records.get(record_name(unit, condition, "rag"), {}).get("capture", {})
                    for condition in ("clean", "poisoned")]
        overlap = None
        if all(capture.get("retrieval_status") == "ok" and isinstance(capture.get("sources"), list)
               for capture in captures):
            overlap = build_document_overlap(captures[0]["sources"], captures[1]["sources"], corpus_roots=roots)
        overlaps.append(overlap)
        if pair and pair.get("document_overlap") != overlap:
            issues.append(f"overlap_replay_mismatch:{unit['index']}")
        success = (pair.get("attack_success") or {}).get("rag_attack_success")
        # Never retain success based on invalid raw rubric scores.
        if any(pilot_score(row.get(f"{condition}_answer_correctness"))[0] is None
               for condition in ("clean", "poisoned")):
            success = None
        if type(success) is bool:
            successes.append(success)
    for record in records.values():
        errors += int(bool(record.get("error") or record.get("capture", {}).get("error")))
    evaluable = [item["jaccard"] for item in overlaps if item and item["jaccard"] is not None]
    return {
        "schema_version": 1, "run_id": manifest["run_id"], "execution_backend": manifest["execution_backend"],
        "complete": not issues, "issues": issues, "error_record_count": errors,
        "completion_meaning": "record integrity, not inference success",
        "distinct_question_count": len({unit["question_id"] for unit in manifest["schedule"]}),
        "source_group_limitation": manifest["source_groups"].get("limitation"),
        "analysis_score_policy": "raw_finite_unit_interval_v2",
        "scheduled_pairs": len(manifest["schedule"]), "source_group_count": len(manifest["source_groups"]["groups"]),
        "nominal_logical_calls": manifest["nominal_logical_calls"], "model_attempts_recorded": attempts,
        "paired_metrics": build_paired_metrics(score_rows),
        "document_overlap": {"observations": overlaps, "valid_count": len(evaluable),
                             "unavailable_count": len(overlaps) - len(evaluable),
                             "mean_jaccard": round(mean(evaluable), 4) if evaluable else None},
        "retrieval": {key: {"valid_count": len(values), "mean": round(mean(values), 4) if values else None}
                      for key, values in retrieval.items()},
        "attack_success": {"valid_count": len(successes), "rate": round(mean(successes), 4) if successes else None},
        "metric_versions": manifest["metric_versions"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--aggregate", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--output", type=Path, help="Create-only offline aggregate output; otherwise stdout")
    args = parser.parse_args(argv)
    if args.aggregate:
        result = aggregate(args.aggregate)
        if args.output:
            write_new_json(args.output, result)
        else:
            print(json.dumps(json_safe(result), indent=2, allow_nan=False))
        return 0 if result["complete"] else 2
    if not args.spec or args.output:
        parser.error("--spec is required; --output is only for aggregation")
    plan = prepare(args.spec)
    if args.dry_run:
        print(json.dumps(json_safe(plan), indent=2, allow_nan=False))
        return 0
    if not args.output_root:
        parser.error("--execute requires an explicit --output-root")
    print(execute(plan, args.output_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
