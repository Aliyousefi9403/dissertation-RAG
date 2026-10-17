"""Live evaluation of the entropy-filter defence (policy entropy-filter-v1).

Two conditions, paired by schedule index with an existing main run:
  defended        PWWS-poisoned collection behind the entropy filter
  clean_filtered  clean collection behind the same filter (measures the defence's cost)

Everything else is identical to the main run: benchmark (questions_v1.json),
prompt, model, temperature 0, top-3 context, judges, 60 s timeouts and no SDK
retries. Records are create-only JSON with a completion checksum file.

Usage (from backend/, Qdrant running, LLM_API_KEY set):
  AEGIS_BENCHMARK_FILE=$PWD/data/evaluation/questions_v1.json PYTHONPATH=. \\
    python ../docs/research/scripts/run_defence_eval.py ../pilot-runs/<MAIN_RUN_ID> ../pilot-runs
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
TIMEOUT = 60


def llm_factory(temperature=None):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=config.LLM_MODEL, api_key=config.LLM_API_KEY,
                      temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
                      timeout=TIMEOUT, max_retries=0)


def main(main_run_dir, output_root):
    main_run = Path(main_run_dir)
    main_manifest = json.loads((main_run / "manifest.json").read_text())
    benchmark_path = Path(config.PROJECT_ROOT) / "data/evaluation/questions_v1.json"
    benchmark_bytes = benchmark_path.read_bytes()
    assert sha256(benchmark_bytes) == main_manifest["benchmark"]["sha256"], "benchmark differs from the main run"
    questions = {q["id"]: q for q in json.loads(benchmark_bytes)}
    project = Path(config.PROJECT_ROOT).parent
    code_files = ["backend/app/defence/entropy_filter.py", "backend/app/generation/rag_chain.py",
                  "backend/app/generation/prompt.py", "backend/app/evaluation/llm_judge.py",
                  "docs/research/scripts/run_defence_eval.py"]
    run = Path(output_root) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-defence-") + uuid.uuid4().hex)
    (run / "observations").mkdir(parents=True)
    write_new_json(run / "manifest.json", {
        "schema_version": 1, "run_id": run.name, "started_at": utc_now(),
        "purpose": "Live evaluation of the entropy-filter defence, paired with the main run by schedule index",
        "paired_main_run": main_manifest["run_id"], "benchmark_sha256": sha256(benchmark_bytes),
        "conditions": CONDITIONS, "schedule": main_manifest["schedule"],
        "defence": {"policy_version": ef.POLICY_VERSION, "score": ef.SCORE_NAME, "threshold_bits": ef.THRESHOLD_BITS,
                    "candidate_k": ef.CANDIDATE_K, "keep": ef.KEEP, "lambda": ef.LAMBDA, "floor": ef.FLOOR},
        "config": {"LLM_MODEL": config.LLM_MODEL, "LLM_TEMPERATURE": config.LLM_TEMPERATURE,
                   "EMBEDDING_MODEL": config.EMBEDDING_MODEL, "CHUNK_SIZE": config.CHUNK_SIZE,
                   "CHUNK_OVERLAP": config.CHUNK_OVERLAP, "RETRIEVAL_TOP_K": config.RETRIEVAL_TOP_K,
                   "timeout_seconds": TIMEOUT, "sdk_retries": 0},
        "code_sha256": {f: sha256((project / f).read_bytes()) for f in code_files},
    })
    written = []
    for unit in main_manifest["schedule"]:
        q = questions[unit["question_id"]]
        for condition, source_state in CONDITIONS.items():
            prefix = f"{unit['index']:06d}-{condition}"
            capture = {"request_attempts": 1}
            started = time.perf_counter()
            try:
                result = rag_chain.answer_question(
                    q["question"], system_state=condition, capture=capture, llm_factory=llm_factory,
                    retrieval_fn=ef.make_filtered_retrieval(source_state, capture=capture))
                answer = result["answer"]
            except Exception as error:  # recorded, never hidden
                answer = None
                capture.setdefault("error", {"stage": "rag", "type": type(error).__name__})
            base = {"schema_version": 1, "run_id": run.name, **unit, "condition": condition}
            write_new_json(run / "observations" / f"{prefix}-rag.json",
                           {**base, "stage": "rag", "latency_seconds": time.perf_counter() - started,
                            "answer": answer, "capture": capture})
            written.append(f"{prefix}-rag.json")
            sources = capture.get("sources") or []
            for stage in ("correctness", "faithfulness"):
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
                write_new_json(run / "observations" / f"{prefix}-{stage}.json", {**base, "stage": stage, "capture": audit})
                written.append(f"{prefix}-{stage}.json")
        print(f"pair {unit['index'] + 1}/{len(main_manifest['schedule'])}", flush=True)
    write_new_json(run / "completion.json", {
        "finished_at": utc_now(), "manifest_sha256": sha256((run / "manifest.json").read_bytes()),
        "record_sha256": {n: sha256((run / "observations" / n).read_bytes()) for n in written}})
    print(run)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
