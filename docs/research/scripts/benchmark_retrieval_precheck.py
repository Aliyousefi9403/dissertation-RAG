"""Retrieval-only pre-check of a draft benchmark: no LLM calls, read-only.

Usage (Qdrant running, clean and poisoned collections indexed):
  cd backend && PYTHONPATH=. python ../docs/research/scripts/benchmark_retrieval_precheck.py QUESTIONS.json OUT.json
"""

import collections
import json
import sys

from app.evaluation.pwws_manifest import load_manifest
from app.evaluation.retrieval_metrics import (
    hit_at_3_and_reciprocal_rank,
    poison_hit_at_3,
)
from app.generation.rag_chain import build_sources, retrieve_documents
from app.ingestion.section_metadata import normalize_heading

qs = json.load(open(sys.argv[1]))
attacked = collections.defaultdict(dict)  # file -> slug -> success
for e in load_manifest():
    attacked[e["file"]][normalize_heading(e["section"])] = e["success"]
rows = []
for q in qs:
    r = {
        "id": q["id"],
        "type": q["expected_attack_type"],
        "cat": q["question_category"],
    }
    f = q["source_evidence"]["corpus_relative_path"]
    slug = q["expected_sections"][0]
    r["target_section_pwws"] = {True: "successful", False: "failed_or_skipped"}.get(
        attacked[f].get(slug), "not_attacked"
    )
    for state in ("clean", "poisoned"):
        src = build_sources(retrieve_documents(q["question"], system_state=state))
        hit, rr = hit_at_3_and_reciprocal_rank(
            src, q["expected_attack_type"], q["expected_sections"]
        )
        r[state + "_hit"], r[state + "_rr"] = hit, rr
        r[state + "_top"] = [
            s["source"].split("knowledge_base/")[-1]
            + "@"
            + str(s["metadata"].get("start_index"))
            for s in src
        ]
        r[state + "_types"] = [s["metadata"].get("attack_type") for s in src]
        if state == "poisoned":
            r["poison_hit"] = poison_hit_at_3(src)["poison_hit_at_3"]
    r["ref_chars"] = len(q["reference_facts"][0])
    rows.append(r)
json.dump(rows, open(sys.argv[2], "x"), indent=1)
