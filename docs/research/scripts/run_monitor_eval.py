"""Live evaluation of the runtime verification monitor (policy runtime-monitor-v1, ADR-009).

Conditions, paired by schedule index with the main run (44 questions x 3 repetitions; each
repetition visits every question once, so repetitions 2 and 3 meet the same attack again):
  monitor              PWWS-poisoned collection, mode verify (trusted data only checks)
  monitor_restore      PWWS-poisoned collection, mode restore (trusted entry may be added as a source)
  clean_monitor        clean collection, mode verify (cost and false quarantines)
  textfooler_monitor   TextFooler-poisoned collection, mode verify (second attack)
Each condition has its own append-only quarantine memory (memory-<condition>.jsonl), starting empty.
Judges, model, temperature, timeouts and record format are those of run_defence_eval.py.

Usage (from backend/, Qdrant running, LLM_API_KEY set):
  PYTHONPATH=. python ../docs/research/scripts/run_monitor_eval.py ../pilot-runs/<MAIN_RUN_ID> ../pilot-runs
Pass an existing run folder instead of ../pilot-runs to resume it in place (records and memories are kept).
Set AEGIS_MONITOR_BLAME=contextual for policy v3 (blame with the contextual synonym gap); default is v2.
"""

import json
import os
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app import config
from app.defence import runtime_monitor as rm
from app.evaluation.pilot_records import sha256, utc_now, write_new_json

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_defence_eval import TIMEOUT, judge, llm_factory

ALL_CONDITIONS = {
    "monitor": ("poisoned", "verify"),
    "monitor_restore": ("poisoned", "restore"),
    "clean_monitor": ("clean", "verify"),
    "textfooler_monitor": ("textfooler", "verify"),
    # Restore mode on the clean corpus: how much of the restore gain is rescuing answers the clean
    # system already refused, rather than repairing poisoning (review point).
    "clean_monitor_restore": ("clean", "restore"),
}
# AEGIS_MONITOR_CONDITIONS=a,b selects conditions; the default is the original four.
CONDITIONS = {
    c: ALL_CONDITIONS[c]
    for c in os.environ.get(
        "AEGIS_MONITOR_CONDITIONS",
        "monitor,monitor_restore,clean_monitor,textfooler_monitor",
    ).split(",")
}
BLAME = os.environ.get("AEGIS_MONITOR_BLAME", "rare_words")
POLICY = rm.POLICY_VERSION_CONTEXTUAL if BLAME == "contextual" else rm.POLICY_VERSION
CODE = [
    "backend/app/defence/runtime_monitor.py",
    "backend/app/generation/prompt.py",
    "backend/app/generation/rag_chain.py",
    "backend/app/evaluation/llm_judge.py",
    "docs/research/scripts/run_monitor_eval.py",
    "docs/research/scripts/run_defence_eval.py",
]
if BLAME == "contextual":
    CODE += [
        "backend/app/defence/contextual_filter.py",
        "backend/app/defence/entropy_filter.py",
    ]


def main(main_run_dir, output):
    main_run = Path(main_run_dir)
    main_manifest = json.loads((main_run / "manifest.json").read_text())
    project = Path(config.PROJECT_ROOT).parent
    benchmark = (
        Path(config.PROJECT_ROOT) / "data/evaluation/questions_v1.json"
    ).read_bytes()
    assert sha256(benchmark) == main_manifest["benchmark"]["sha256"], (
        "benchmark differs from the main run"
    )
    questions = {q["id"]: q for q in json.loads(benchmark)}
    current = {f: sha256((project / f).read_bytes()) for f in CODE}
    out = Path(output)
    if (out / "manifest.json").exists():
        manifest = json.loads((out / "manifest.json").read_text())
        assert not (out / "completion.json").exists(), "run is already complete"
        changed = [
            f
            for f in CODE
            if manifest["code_sha256"].get(f) != current[f]
            and not f.endswith("run_monitor_eval.py")
        ]
        assert manifest["monitor"]["policy_version"] == POLICY, "blame setting differs"
        assert not changed, f"code changed since the run started: {changed}"
        with (out / "run_log.jsonl").open("a") as log:
            log.write(
                json.dumps(
                    {
                        "event": "resume",
                        "at": utc_now(),
                        "records_already_written": len(
                            list((out / "observations").glob("*.json"))
                        ),
                    }
                )
                + "\n"
            )
    else:
        out = out / (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-monitor-") + uuid.uuid4().hex
        )
        (out / "observations").mkdir(parents=True)
        write_new_json(
            out / "manifest.json",
            {
                "schema_version": 1,
                "run_id": out.name,
                "started_at": utc_now(),
                "purpose": "Live evaluation of the runtime verification monitor, paired with the main run by schedule index",
                "paired_main_run": main_manifest["run_id"],
                "benchmark_sha256": sha256(benchmark),
                "conditions": {
                    c: {"source_state": s, "mode": m}
                    for c, (s, m) in CONDITIONS.items()
                },
                "schedule": main_manifest["schedule"],
                "monitor": {
                    "policy_version": POLICY,
                    "blame": BLAME,
                    "rare_zipf": rm.RARE_ZIPF,
                    "max_rounds": rm.MAX_ROUNDS,
                    "candidate_k": rm.CANDIDATE_K,
                    "keep": rm.KEEP,
                    "trusted_files_sha256": {
                        Path(p).name: h for p, h in rm.TRUSTED_FILES.items()
                    },
                },
                "config": {
                    "LLM_MODEL": config.LLM_MODEL,
                    "LLM_TEMPERATURE": config.LLM_TEMPERATURE,
                    "EMBEDDING_MODEL": config.EMBEDDING_MODEL,
                    "CHUNK_SIZE": config.CHUNK_SIZE,
                    "CHUNK_OVERLAP": config.CHUNK_OVERLAP,
                    "RETRIEVAL_TOP_K": config.RETRIEVAL_TOP_K,
                    "timeout_seconds": TIMEOUT,
                    "sdk_retries": 0,
                },
                "code_sha256": current,
            },
        )
    memories = {c: rm.QuarantineMemory(out / f"memory-{c}.jsonl") for c in CONDITIONS}
    written = []
    for unit in main_manifest["schedule"]:
        q = questions[unit["question_id"]]
        for condition, (source_state, mode) in CONDITIONS.items():
            prefix = f"{unit['index']:06d}-{condition}"
            rag_file = out / "observations" / f"{prefix}-rag.json"
            if rag_file.exists():
                record = json.loads(rag_file.read_text())
            else:
                capture, started = {"request_attempts": 1}, time.perf_counter()
                try:
                    answer = rm.monitored_answer(
                        q["question"],
                        source_state,
                        memory=memories[condition],
                        llm_factory=llm_factory,
                        mode=mode,
                        capture=capture,
                        blame=BLAME,
                    )["answer"]
                except Exception as error:  # noqa: BLE001  recorded, never hidden
                    answer = None
                    capture.setdefault(
                        "error",
                        {
                            "stage": "monitor",
                            "type": type(error).__name__,
                            "message": str(error)[:300],
                        },
                    )
                record = {
                    "schema_version": 1,
                    "run_id": out.name,
                    **unit,
                    "condition": condition,
                    "stage": "rag",
                    "latency_seconds": time.perf_counter() - started,
                    "answer": answer,
                    "capture": capture,
                }
                write_new_json(rag_file, record)
            written.append(rag_file.name)
            judge(out, q, record, prefix, written)
        print(f"pair {unit['index'] + 1}/{len(main_manifest['schedule'])}", flush=True)
    write_new_json(
        out / "completion.json",
        {
            "finished_at": utc_now(),
            "manifest_sha256": sha256((out / "manifest.json").read_bytes()),
            "record_sha256": {
                n: sha256((out / "observations" / n).read_bytes()) for n in written
            },
            "memory_sha256": {
                f"memory-{c}.jsonl": sha256(m.path.read_bytes())
                if m.path.exists()
                else None
                for c, m in memories.items()
            },
        },
    )
    print(out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
