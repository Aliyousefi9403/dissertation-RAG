"""Live evaluation of the entropy-filter defence (policy entropy-filter-v1).

Two conditions, paired by schedule index with an existing main run:
  defended        PWWS-poisoned collection behind the entropy filter
  clean_filtered  clean collection behind the same filter (measures the defence's cost)

Everything else is identical to the main run: benchmark (questions_v1.json),
prompt, model, temperature 0, top-3 context, judges, 60 s timeouts and no SDK
retries. Records are create-only JSON with a completion checksum file.

With a third argument `contextual`, the conditions are `contextual` and `clean_contextual`
(policy contextual-filter-v1: the drop defence with a language-model reference q).
With a third argument `repair`, the conditions are `repaired` and `clean_repaired`
(policy entropy-repair-v1: repair words above 9.5 bits, rescore, keep if under the
same threshold); everything else is identical.

Usage (from backend/, Qdrant running, LLM_API_KEY set):
  AEGIS_BENCHMARK_FILE=$PWD/data/evaluation/questions_v1.json PYTHONPATH=. \\
    python ../docs/research/scripts/run_defence_eval.py ../pilot-runs/<MAIN_RUN_ID> ../pilot-runs [repair]

To continue an interrupted run in place, pass its folder instead of the output root
(and the same mode). The code hashes must match the run's manifest; records already
written are kept unchanged (create-only), a missing judge record is produced from the
saved answer and sources, and each resume is appended to <run>/run_log.jsonl.
"""

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.defence import entropy_filter as ef
from app.evaluation import llm_judge
from app.evaluation.pilot_records import sha256, utc_now, write_new_json
from app.generation import rag_chain

CONDITIONS = {"defended": "poisoned", "clean_filtered": "clean"}
REPAIR_CONDITIONS = {"repaired": "poisoned", "clean_repaired": "clean"}
CONTEXTUAL_CONDITIONS = {"contextual": "poisoned", "clean_contextual": "clean"}
TIMEOUT = 60
# Code changes shown not to alter a run's behaviour, so a run may resume across them.
# contextual_filter.py: LanguageModel gained an optional max_tokens (default unchanged, used by the
# adaptive_lm attack); replaying the first 12 records reproduced every score exactly
# (pilot-runs/20261018T180113Z-contextual-*/resume_equivalence_check.json).
EQUIVALENT_CHANGES = {
    "backend/app/defence/contextual_filter.py": (
        "1d68b522bd76bf36bcadd09a36dad84b57a0571d9992ba466aa08ea429c3fdcf",
        "3dece334d00c193a426705c40fef4aa4d4fa6e215281e809d488ac9cb640000b"),
}


def llm_factory(temperature=None):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=config.LLM_MODEL, api_key=config.LLM_API_KEY,
                      temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
                      timeout=TIMEOUT, max_retries=0)


def main(main_run_dir, output_root, mode="drop"):
    repair, contextual = mode == "repair", mode == "contextual"
    conditions = REPAIR_CONDITIONS if repair else CONTEXTUAL_CONDITIONS if contextual else CONDITIONS
    if contextual:
        from app.defence import contextual_filter as cxf
    main_run = Path(main_run_dir)
    main_manifest = json.loads((main_run / "manifest.json").read_text())
    benchmark_path = Path(config.PROJECT_ROOT) / "data/evaluation/questions_v1.json"
    benchmark_bytes = benchmark_path.read_bytes()
    assert sha256(benchmark_bytes) == main_manifest["benchmark"]["sha256"], "benchmark differs from the main run"
    questions = {q["id"]: q for q in json.loads(benchmark_bytes)}
    project = Path(config.PROJECT_ROOT).parent
    code_files = ["backend/app/defence/entropy_filter.py", "backend/app/defence/contextual_filter.py", "backend/app/generation/rag_chain.py",
                  "backend/app/generation/prompt.py", "backend/app/evaluation/llm_judge.py",
                  "docs/research/scripts/run_defence_eval.py"]
    resumed = (Path(output_root) / "manifest.json").exists()
    if resumed:
        return resume(Path(output_root), main_manifest, questions, conditions, project, code_files,
                      cxf.make_filtered_retrieval if contextual else None, repair)
    run = Path(output_root) / (datetime.now(timezone.utc).strftime(f"%Y%m%dT%H%M%SZ-{'repair' if repair else 'contextual' if contextual else 'defence'}-") + uuid.uuid4().hex)
    (run / "observations").mkdir(parents=True)
    write_new_json(run / "manifest.json", {
        "schema_version": 1, "run_id": run.name, "started_at": utc_now(),
        "purpose": f"Live evaluation of the {'entropy-repair' if repair else 'contextual-filter' if contextual else 'entropy-filter'} defence, paired with the main run by schedule index",
        "paired_main_run": main_manifest["run_id"], "benchmark_sha256": sha256(benchmark_bytes),
        "conditions": conditions, "schedule": main_manifest["schedule"],
        "defence": {"policy_version": ef.REPAIR_POLICY_VERSION if repair else cxf.POLICY_VERSION if contextual else ef.POLICY_VERSION,
                    **({"contextual_threshold_bits": cxf.THRESHOLD_BITS, "lm": cxf.LM_NAME,
                        "candidate_words": cxf.CANDIDATE_WORDS, "candidate_synonyms": cxf.CANDIDATE_SYNONYMS} if contextual else {}),
                    **({"word_repair_bits": ef.WORD_REPAIR_BITS} if repair else {}), "score": ef.SCORE_NAME, "threshold_bits": ef.THRESHOLD_BITS,
                    "candidate_k": ef.CANDIDATE_K, "keep": ef.KEEP, "lambda": ef.LAMBDA, "floor": ef.FLOOR},
        "config": {"LLM_MODEL": config.LLM_MODEL, "LLM_TEMPERATURE": config.LLM_TEMPERATURE,
                   "EMBEDDING_MODEL": config.EMBEDDING_MODEL, "CHUNK_SIZE": config.CHUNK_SIZE,
                   "CHUNK_OVERLAP": config.CHUNK_OVERLAP, "RETRIEVAL_TOP_K": config.RETRIEVAL_TOP_K,
                   "timeout_seconds": TIMEOUT, "sdk_retries": 0},
        "code_sha256": {f: sha256((project / f).read_bytes()) for f in code_files},
    })
    execute(run, main_manifest, questions, conditions, contextual and cxf.make_filtered_retrieval, repair)


def resume(run, main_manifest, questions, conditions, project, code_files, contextual_retrieval, repair):
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["paired_main_run"] == main_manifest["run_id"], "run is paired with a different main run"
    assert manifest["conditions"] == conditions, "run was started in a different mode"
    assert not (run / "completion.json").exists(), "run is already complete"
    current = {f: sha256((project / f).read_bytes()) for f in code_files}
    runner = "docs/research/scripts/run_defence_eval.py"  # may gain resume support; logged, not checked
    changed = [f for f in code_files if f != runner and manifest["code_sha256"].get(f) != current[f]
               and EQUIVALENT_CHANGES.get(f) != (manifest["code_sha256"].get(f), current[f])]
    assert not changed, f"code changed since the run started: {changed}"
    done = sorted(p.name for p in (run / "observations").glob("*.json"))
    with (run / "run_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "resume", "at": utc_now(), "records_already_written": len(done),
                                 "runner_sha256_at_start": manifest["code_sha256"].get(runner),
                                 "runner_sha256_now": current[runner]}) + "\n")
    execute(run, main_manifest, questions, conditions, contextual_retrieval, repair)


def execute(run, main_manifest, questions, conditions, contextual_retrieval, repair):
    written = []
    for unit in main_manifest["schedule"]:
        q = questions[unit["question_id"]]
        for condition, source_state in conditions.items():
            prefix = f"{unit['index']:06d}-{condition}"
            rag_file = run / "observations" / f"{prefix}-rag.json"
            if rag_file.exists():
                record = json.loads(rag_file.read_text())
                written.append(rag_file.name)
                judge(run, q, record, prefix, written)
                continue
            capture = {"request_attempts": 1}
            started = time.perf_counter()
            try:
                result = rag_chain.answer_question(
                    q["question"], system_state=condition, capture=capture, llm_factory=llm_factory,
                    retrieval_fn=(contextual_retrieval(source_state, capture=capture) if contextual_retrieval
                                  else ef.make_filtered_retrieval(source_state, capture=capture, repair=repair)))
                answer = result["answer"]
            except Exception as error:  # recorded, never hidden
                answer = None
                capture.setdefault("error", {"stage": "rag", "type": type(error).__name__})
            base = {"schema_version": 1, "run_id": run.name, **unit, "condition": condition}
            record = {**base, "stage": "rag", "latency_seconds": time.perf_counter() - started,
                      "answer": answer, "capture": capture}
            write_new_json(rag_file, record)
            written.append(rag_file.name)
            judge(run, q, record, prefix, written)
        print(f"pair {unit['index'] + 1}/{len(main_manifest['schedule'])}", flush=True)
    write_new_json(run / "completion.json", {
        "finished_at": utc_now(), "manifest_sha256": sha256((run / "manifest.json").read_bytes()),
        "record_sha256": {n: sha256((run / "observations" / n).read_bytes()) for n in written}})
    print(run)


def judge(run, q, record, prefix, written):
    answer, sources = record["answer"], record["capture"].get("sources") or []
    base = {k: v for k, v in record.items() if k not in ("stage", "latency_seconds", "answer", "capture")}
    for stage in ("correctness", "faithfulness"):
        target = run / "observations" / f"{prefix}-{stage}.json"
        written.append(target.name)
        if target.exists():
            continue
        audit = {"raw_score": None, "status": "missing"}
        if answer is not None:
            try:
                if stage == "correctness":
                    llm_judge.evaluate_correctness(q["question"], q["reference_facts"], answer,
                                                   capture=audit, llm_factory=llm_factory)
                else:
                    context = "\n\n".join(f"[Source {i}]\n{s.get('content', '')}" for i, s in enumerate(sources, 1))
                    llm_judge.evaluate_faithfulness(q["question"], context, answer,
                                                    capture=audit, llm_factory=llm_factory)
            except Exception as error:
                audit["error"] = {"stage": stage, "type": type(error).__name__}
        write_new_json(target, {**base, "stage": stage, "capture": audit})


if __name__ == "__main__":
    main(*sys.argv[1:4])
