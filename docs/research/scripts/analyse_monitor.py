"""Analysis of the live runtime-monitor run (policy runtime-monitor-v1, ADR-009). Offline.

Pairs each monitor condition with its undefended counterpart by schedule index:
  monitor, monitor_restore -> poisoned (main run)      clean_monitor -> clean (main run)
  textfooler_monitor       -> textfooler (TextFooler run)
and also compares monitor with the contextual filter (contextual run) on the same corpus.
Metrics: correctness, faithfulness, Hit@3, edited-text exposure (PWWS or TextFooler manifest),
outcome categories; monitor outcomes and generations; quarantined passages and how many of them
contain attacker-edited text (false quarantines on clean); the memory effect across repetitions
(round-0 violations, generations, exposure and correctness in repetition 1 vs 2-3); and a replay
of the run trace checking phi3, G(quarantined(p) -> G not in_context(p)).
Statistics as analyse_defence.py: question-level means, cluster bootstrap (B=10000, seed 20261016),
two-sided Wilcoxon on non-zero question differences.

Usage (from backend/, Qdrant running for the passage lookup):
  PYTHONPATH=. python ../docs/research/scripts/analyse_monitor.py MONITOR_RUN OUT_DIR
"""

import json
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

from app.config import QDRANT_URL, get_qdrant_collection
from app.defence.runtime_monitor import passage_key
from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse_defence as ad  # noqa: E402
import analyse_textfooler_defence as atf  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MAIN = ROOT / "pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e"
TF = ROOT / "pilot-runs/20261019T200851Z-textfooler-33c7d2a707874d2ca57cb5b7851984e9"
CTX = ROOT / "pilot-runs/20261018T180113Z-contextual-a2eb543b82974c5aa4c1502de6e555a7"
METRICS = ("correctness", "faithfulness", "hit3", "exposure")


def corpus_passages(state):
    """Passage key -> (relative file, start, length) for every chunk of a collection."""
    client, out, offset = QdrantClient(url=QDRANT_URL), {}, None
    while True:
        points, offset = client.scroll(
            get_qdrant_collection(state), limit=256, offset=offset, with_payload=True
        )
        for p in points:
            meta = p.payload.get("metadata", {})
            doc = Document(
                page_content=p.payload.get("page_content", ""), metadata=meta
            )
            out[passage_key(doc)] = (
                meta.get("source", ""),
                meta.get("start_index"),
                len(doc.page_content),
            )
        if offset is None:
            return out


def main(run_dir, out_dir):
    run, out = Path(run_dir), Path(out_dir)
    manifest = json.loads((run / "manifest.json").read_text())
    main_manifest = json.loads((MAIN / "manifest.json").read_text())
    questions = {q["id"]: q for q in main_manifest["benchmark"]["data"]}
    _, pwws_spans = ad.edited_spans()
    tf_spans = atf.edited_spans(atf.manifest())

    def exposure(condition, sources):
        if condition.startswith("textfooler"):
            return atf.exposure(sources, tf_spans)
        return ad.exposure(sources, None, pwws_spans)

    sources_of = {"poisoned": MAIN, "clean": MAIN, "textfooler": TF, "contextual": CTX}
    conditions = list(manifest["conditions"]) + list(sources_of)

    def load(condition, index, stage):
        base = sources_of.get(condition, run)
        path = base / "observations" / f"{index:06d}-{condition}-{stage}.json"
        return json.loads(path.read_text()) if path.exists() else None

    rows = []
    for unit in manifest["schedule"]:
        q = questions[unit["question_id"]]
        row = {
            "index": unit["index"],
            "question_id": q["id"],
            "repetition": unit["repetition"],
        }
        for c in conditions:
            rag, corr, faith = (
                load(c, unit["index"], s)
                for s in ("rag", "correctness", "faithfulness")
            )
            cap = (rag or {}).get("capture") or {}
            ok = cap.get("retrieval_status") == "ok"
            src = [
                s
                for s in cap.get("sources") or []
                if not str(s.get("source", "")).startswith("trusted-mitre:")
            ]
            hit = (
                hit_at_3_and_reciprocal_rank(
                    src, q["expected_attack_type"], q["expected_sections"]
                )[0]
                if ok
                else None
            )
            score = ((corr or {}).get("capture") or {}).get("raw_score")
            row.update(
                {
                    f"{c}_correctness": score,
                    f"{c}_faithfulness": ((faith or {}).get("capture") or {}).get(
                        "raw_score"
                    ),
                    f"{c}_hit3": hit,
                    f"{c}_exposure": exposure(c, src) if ok else None,
                    f"{c}_outcome": ad.outcome((rag or {}).get("answer"), score),
                    f"{c}_monitor": cap.get("monitor"),
                }
            )
        rows.append(row)

    def mean(values):
        values = [v for v in values if v is not None]
        return st.mean(values) if values else None

    def qmeans(subset):
        by_q = defaultdict(list)
        for r in subset:
            by_q[r["question_id"]].append(r)
        return {
            k: {
                f"{c}_{m}": mean(r[f"{c}_{m}"] for r in v)
                for c in conditions
                for m in METRICS
            }
            for k, v in by_q.items()
        }

    def compare(qm, a, b, m):
        qs = [
            v
            for v in qm.values()
            if v[f"{a}_{m}"] is not None and v[f"{b}_{m}"] is not None
        ]
        if not qs:
            return None
        diffs = [v[f"{a}_{m}"] - v[f"{b}_{m}"] for v in qs]
        rng = random.Random(ad.SEED)
        boot = sorted(st.mean(rng.choice(diffs) for _ in diffs) for _ in range(ad.B))
        nonzero = [d for d in diffs if d != 0]
        p = wilcoxon(nonzero).pvalue if len(nonzero) >= 5 else None
        return {
            "a": round(st.mean(v[f"{a}_{m}"] for v in qs), 4),
            "b": round(st.mean(v[f"{b}_{m}"] for v in qs), 4),
            "delta": round(st.mean(diffs), 4),
            "ci95": [
                round(boot[int(0.025 * ad.B)], 4),
                round(boot[int(0.975 * ad.B)], 4),
            ],
            "wilcoxon_p": None if p is None else round(float(p), 4),
            "questions": len(qs),
        }

    pairs = {
        "monitor_vs_poisoned": ("monitor", "poisoned"),
        "monitor_restore_vs_poisoned": ("monitor_restore", "poisoned"),
        "monitor_vs_contextual": ("monitor", "contextual"),
        "monitor_restore_vs_clean": ("monitor_restore", "clean"),
        "clean_monitor_vs_clean": ("clean_monitor", "clean"),
        "textfooler_monitor_vs_textfooler": ("textfooler_monitor", "textfooler"),
    }
    qm_all = qmeans(rows)
    comparisons = {
        n: {m: compare(qm_all, a, b, m) for m in METRICS} for n, (a, b) in pairs.items()
    }
    outcomes = {c: dict(Counter(r[f"{c}_outcome"] for r in rows)) for c in conditions}

    # Monitor behaviour, memory effect and the phi3 trace check
    lookup = {
        "poisoned": corpus_passages("poisoned"),
        "clean": corpus_passages("clean"),
        "textfooler": corpus_passages("textfooler"),
    }
    span_of = {"poisoned": pwws_spans, "textfooler": tf_spans}
    marker = {
        "poisoned": "/data/poisoned/knowledge_base/",
        "textfooler": "/data/poisoned_textfooler/knowledge_base/",
    }
    monitor = {}
    for c, spec in manifest["conditions"].items():
        state = spec["source_state"]
        mon = [r[f"{c}_monitor"] or {} for r in rows]
        quarantined_before, phi3_violations, by_rep = (
            set(),
            0,
            defaultdict(lambda: defaultdict(list)),
        )
        for r, m in zip(rows, mon):
            keys = []
            for step in m.get("rounds", []):
                # The restore generation reuses the last round's passages; runs before
                # strict_restore record no keys for it (the first analysis skipped it).
                keys = step.get("context_keys", keys)
                if set(keys) & quarantined_before:
                    phi3_violations += 1
                quarantined_before |= set(step.get("quarantined", []))
            rounds = m.get("rounds", [])
            rep = "repetition_1" if r["repetition"] == 1 else "repetitions_2_3"
            by_rep[rep]["round0_violation"].append(
                int(bool(rounds and rounds[0].get("violations")))
            )
            by_rep[rep]["round0_lexical"].append(
                int(
                    any(
                        v["spec"] == "phi1_lexical"
                        for v in (rounds[0].get("violations", []) if rounds else [])
                    )
                )
            )
            by_rep[rep]["generations"].append(m.get("generations", 0))
            by_rep[rep]["skipped_quarantined"].append(
                rounds[0].get("skipped_quarantined", 0) if rounds else 0
            )
            for metric in ("correctness", "exposure"):
                by_rep[rep][metric].append(r[f"{c}_{metric}"])
        memory_file = run / f"memory-{c}.jsonl"
        entries = (
            [json.loads(line) for line in memory_file.read_text().splitlines()]
            if memory_file.exists()
            else []
        )
        edited = 0
        for e in entries:
            src, start, length = lookup[state].get(e["key"], ("", None, 0))
            src = src.replace("\\", "/")
            if state in marker and marker[state] in src and start is not None:
                name = src.split(marker[state], 1)[1]
                edited += any(
                    x < start + length and start < y
                    for x, y in span_of[state].get(name, [])
                )
        monitor[c] = {
            "outcomes": dict(Counter(m.get("outcome") for m in mon)),
            "generations_total": sum(m.get("generations", 0) for m in mon),
            "quarantined_passages": len(entries),
            "quarantined_with_edited_text": edited,
            "quarantined_without_edited_text": len(entries) - edited,
            "phi3_trace_violations": phi3_violations,
            "by_repetition": {
                rep: {
                    k: round(mean(v), 4) if mean(v) is not None else None
                    for k, v in d.items()
                }
                for rep, d in by_rep.items()
            },
        }

    summary = {
        "monitor_run": manifest["run_id"],
        "main_run": main_manifest["run_id"],
        "pairs": len(rows),
        "comparisons": comparisons,
        "outcomes": outcomes,
        "monitor": monitor,
        "method": __doc__.split("Statistics as")[1].split("Usage")[0].strip(),
    }
    out.mkdir(parents=True, exist_ok=True)
    with (out / "summary.json").open("x") as handle:
        json.dump(summary, handle, indent=1)
    print(
        json.dumps(
            {
                "comparisons": {
                    n: {m: (v or {}).get("delta") for m, v in d.items()}
                    for n, d in comparisons.items()
                },
                "monitor": monitor,
                "outcomes": outcomes,
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main(*sys.argv[1:3])
