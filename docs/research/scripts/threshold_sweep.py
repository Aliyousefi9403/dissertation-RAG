"""Safety/utility frontier of the entropy filter: sweep the threshold and the candidate depth.

Descriptive only. The deployed threshold (entropy-filter-v1, 7.2262 bits) stays frozen;
this script shows where it sits on the curve, it does not choose a new one.

For each benchmark question and each corpus (clean, poisoned), retrieve the top 20
candidates once, score every candidate with the deployed scorer
(app.defence.entropy_filter.score_text, leave-one-document-out reference), then
replay the filter for every (threshold, k) pair: keep the first 3 unflagged
candidates among the top k. Measures per question: Hit@3, reciprocal rank,
edited-text exposure (poisoned only), and whether fewer than 3 passages survive.
No LLM calls.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/threshold_sweep.py OUT_DIR
"""

import json
import statistics as st
import sys
from pathlib import Path

from app.config import QDRANT_URL, get_knowledge_base_path, get_qdrant_collection
from app.defence.entropy_filter import (
    KEEP,
    POLICY_VERSION,
    THRESHOLD_BITS,
    _relative_document,
    reference_for,
    score_text,
)
from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from app.generation.rag_chain import build_sources
from app.vectorstore.qdrant_store import get_embeddings
from langchain_qdrant import QdrantVectorStore

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse_defence import edited_spans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MAX_K = 20
DEPTHS = (3, 5, 10, 15, 20)
THRESHOLDS = [round(4 + 0.25 * i, 2) for i in range(33)] + [
    THRESHOLD_BITS
]  # 4.00 .. 12.00 bits, plus deployed


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    questions = json.loads(
        (ROOT / "backend/data/evaluation/questions_v1.json").read_text()
    )
    poisoned_root, spans = edited_spans()
    embeddings = get_embeddings()
    candidates = {}
    for state in ("clean", "poisoned"):
        root = get_knowledge_base_path(state)
        reference = reference_for(str(root))
        store = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            collection_name=get_qdrant_collection(state),
            url=QDRANT_URL,
        )
        for q in questions:
            sources = build_sources(
                store.similarity_search_with_score(q["question"], k=MAX_K)
            )
            for s in sources:
                name = _relative_document(s["source"], root)
                s["_score"] = score_text(s["content"], name, reference)["score_bits"]
                a = s["metadata"]["start_index"]
                s["_edited"] = state == "poisoned" and any(
                    x < a + len(s["content"]) and a < y for x, y in spans.get(name, [])
                )
            candidates[(state, q["id"])] = sources

    def replay(state, q, threshold, k):
        kept = [
            s for s in candidates[(state, q["id"])][:k] if s["_score"] <= threshold
        ][:KEEP]
        hit, rr = hit_at_3_and_reciprocal_rank(
            kept, q["expected_attack_type"], q["expected_sections"]
        )
        return {
            "hit3": hit,
            "rr": rr,
            "exposure": int(any(s["_edited"] for s in kept)),
            "short": int(len(kept) < KEEP),
        }

    grid = []
    for k in DEPTHS:
        for threshold in sorted(set(THRESHOLDS)):
            row = {
                "k": k,
                "threshold_bits": threshold,
                "deployed": k == 10 and threshold == THRESHOLD_BITS,
            }
            for state in ("clean", "poisoned"):
                for split in ("all", "development", "held_out"):
                    qs = [q for q in questions if split == "all" or q["split"] == split]
                    per_q = [replay(state, q, threshold, k) for q in qs]
                    for m in ("hit3", "rr", "exposure", "short"):
                        if m == "exposure" and state == "clean":
                            continue
                        row[f"{state}_{split}_{m}"] = round(
                            st.mean(r[m] for r in per_q), 4
                        )
            grid.append(row)
    unfiltered = {
        f"{state}_{m}": round(
            st.mean(replay(state, q, float("inf"), 3)[m] for q in questions), 4
        )
        for state in ("clean", "poisoned")
        for m in ("hit3", "rr", "exposure")
        if not (state == "clean" and m == "exposure")
    }
    per_candidate = [
        {
            "state": state,
            "question_id": qid,
            "rank": i + 1,
            "score_bits": s["_score"],
            "edited": s["_edited"],
            "source": s["source"].split("knowledge_base/")[-1],
            "start_index": s["metadata"]["start_index"],
        }
        for (state, qid), sources in candidates.items()
        for i, s in enumerate(sources)
    ]
    payload = {
        "policy_version": POLICY_VERSION,
        "deployed_threshold_bits": THRESHOLD_BITS,
        "deployed_k": 10,
        "keep": KEEP,
        "max_k": MAX_K,
        "questions": len(questions),
        "unfiltered_top3": unfiltered,
        "grid": grid,
        "note": "descriptive sweep; the deployed threshold was frozen on development chunks before this analysis and is not re-tuned",
    }
    (out / "sweep.json").open("x").write(json.dumps(payload, indent=1) + "\n")
    (out / "candidates.json").open("x").write(
        json.dumps(per_candidate, indent=0) + "\n"
    )
    for row in grid:
        if row["k"] == 10 and row["threshold_bits"] in (
            5.0,
            6.0,
            7.0,
            THRESHOLD_BITS,
            8.0,
            9.0,
            10.0,
            12.0,
        ):
            print(
                row["threshold_bits"],
                {
                    k: v
                    for k, v in row.items()
                    if k.endswith("all_hit3")
                    or k.endswith("all_exposure")
                    or k.endswith("all_short")
                },
            )
    print("unfiltered", unfiltered)


if __name__ == "__main__":
    main(sys.argv[1])
