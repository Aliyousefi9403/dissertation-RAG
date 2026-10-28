"""Retrieval-level comparison of drop (entropy-filter-v1) and repair-then-rescore (entropy-repair-v1).

Uses the deployed functions (app.defence.entropy_filter.filter_results) on the same
10 candidates per question. Measures Hit@3 and edited-text exposure for clean and
poisoned corpora. Exposure is conservative for repair: a kept chunk counts as
exposed if it overlaps any PWWS-edited span, even when the edited words in it were
repaired; the number of substitutions still unrepaired in kept chunks is reported
separately. No LLM calls.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/repair_retrieval_eval.py OUT.json
"""

import json
import statistics as st
import sys
from difflib import SequenceMatcher
from pathlib import Path

from app.config import get_knowledge_base_path
from app.defence.entropy_filter import (
    CANDIDATE_K,
    KEEP,
    _relative_document,
    filter_results,
    tokens,
)
from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from app.generation.rag_chain import build_sources
from app.retrieval.search import search_knowledge_base

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse_defence import edited_spans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def substitutes_by_file():
    root = get_knowledge_base_path("poisoned")
    subs = {}
    for line in (root.parent / "pwws_attack_manifest.jsonl").read_text().splitlines():
        e = json.loads(line)
        if e.get("success"):
            o, a = tokens(e["original_text"]), tokens(e["adversarial_text"])
            for tag, i1, i2, j1, j2 in SequenceMatcher(
                None, o, a, autojunk=False
            ).get_opcodes():
                if tag == "replace":
                    subs.setdefault(e["file"], set()).update(
                        w for w in a[j1:j2] if w not in o[i1:i2]
                    )
    return subs


def main(out):
    questions = json.loads(
        (ROOT / "backend/data/evaluation/questions_v1.json").read_text()
    )
    _, spans = edited_spans()
    subs = substitutes_by_file()
    summary, rows = {}, []
    for state in ("clean", "poisoned"):
        root = get_knowledge_base_path(state)
        per_policy = {"unfiltered": [], "drop": [], "repair": []}
        for q in questions:
            candidates = search_knowledge_base(
                query=q["question"], k=CANDIDATE_K, system_state=state
            )
            chosen = {
                "unfiltered": candidates[:KEEP],
                "drop": filter_results(candidates, root)[0],
                "repair": filter_results(candidates, root, repair=True)[0],
            }
            row = {"state": state, "id": q["id"], "split": q["split"]}
            for policy, docs in chosen.items():
                sources = build_sources(docs)
                hit, rr = hit_at_3_and_reciprocal_rank(
                    sources, q["expected_attack_type"], q["expected_sections"]
                )
                exposed, residual, repaired = 0, 0, 0
                for s in sources:
                    name = _relative_document(s["source"], root)
                    a = s["metadata"]["start_index"]
                    original_len = len(
                        next(
                            d
                            for d, _ in candidates
                            if d.metadata.get("start_index") == a
                            and _relative_document(d.metadata.get("source", ""), root)
                            == name
                        ).page_content
                    )
                    if state == "poisoned" and any(
                        x < a + original_len and a < y for x, y in spans.get(name, [])
                    ):
                        exposed = 1
                        residual += sum(
                            w in subs.get(name, ()) for w in set(tokens(s["content"]))
                        )
                    repaired += len(
                        s["metadata"].get("entropy_filter", {}).get("repairs", [])
                    )
                per_policy[policy].append(
                    {
                        "hit3": hit,
                        "rr": rr,
                        "exposure": exposed,
                        "unrepaired_substitutes": residual,
                        "repaired_words": repaired,
                    }
                )
                row[policy] = per_policy[policy][-1]
            rows.append(row)
        summary[state] = {
            p: {m: round(st.mean(r[m] for r in v), 4) for m in v[0]}
            for p, v in per_policy.items()
        }
    payload = {
        "questions": len(questions),
        "candidate_k": CANDIDATE_K,
        "keep": KEEP,
        "summary": summary,
        "rows": rows,
        "note": "exposure is conservative for repair (counts any overlap with an edited span, repaired or not)",
    }
    Path(out).open("x").write(json.dumps(payload, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
