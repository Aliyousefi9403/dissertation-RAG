"""Retrieval-time defence preview: drop chunks flagged by the synonym-gap detector.

For each benchmark question: retrieve the top 10 chunks, score each chunk with
syngap_top3_domain (leave-one-document-out reference built from the collection
being searched), drop chunks above the threshold, and keep the first 3 that
remain. Compare Hit@3 and edited-text exposure with the unfiltered top 3,
for clean and poisoned. The threshold is fixed from development chunks (FPR 10%)
in the detector evaluation output. No LLM calls.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/entropy_filter_retrieval.py DETECTOR_EVAL.json OUT.json
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

from langchain_qdrant import QdrantVectorStore

from app.config import QDRANT_URL, get_knowledge_base_path, get_qdrant_collection
from app.evaluation.retrieval_metrics import hit_at_3_and_reciprocal_rank
from app.generation.rag_chain import build_sources
from app.vectorstore.qdrant_store import get_embeddings

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entropy_detection_eval import LAMBDA, STOPWORDS, edited_spans, synonyms, tokens  # noqa: E402
from wordfreq import word_frequency  # noqa: E402

FLOOR = 1e-9
SCORE = "syngap_top3_domain"


def main(detector_eval, out):
    evaluation = json.loads(Path(detector_eval).read_text())
    threshold = evaluation["results"]["development"][SCORE]["threshold_fpr10"]
    questions = json.loads((Path(__file__).resolve().parents[3] / "backend/data/evaluation/questions_v1.json").read_text())
    manifest = [json.loads(l) for l in (get_knowledge_base_path("poisoned").parents[1] / "poisoned/pwws_attack_manifest.jsonl").read_text().splitlines() if l.strip()]
    embeddings = get_embeddings()
    summary, rows = {}, []
    for state in ("clean", "poisoned"):
        root = get_knowledge_base_path(state)
        texts = {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in root.rglob("*.md")}
        counts = {n: Counter(tokens(t)) for n, t in texts.items()}
        total = sum(counts.values(), Counter())
        spans = {n: [] for n in texts}
        if state == "poisoned":
            for e in manifest:
                if e.get("success"):
                    spans[e["file"]] += edited_spans(texts[e["file"]], e)

        def score(content, name):
            rest = total - counts[name]
            n = sum(rest.values())
            q = lambda w: LAMBDA * rest[w] / n + (1 - LAMBDA) * max(word_frequency(w, "en"), FLOOR)  # noqa: E731
            words = tokens(content)
            gaps = sorted((max(math.log2(q(s)) for s in synonyms(w)) - math.log2(q(w))
                           for w in set(words) if len(w) > 2 and w not in STOPWORDS and synonyms(w)), reverse=True)
            return sum(gaps[:3]) / 3 if gaps else 0.0

        store = QdrantVectorStore.from_existing_collection(embedding=embeddings, collection_name=get_qdrant_collection(state), url=QDRANT_URL)
        stats = Counter()
        for q in questions:
            sources = build_sources(store.similarity_search_with_score(q["question"], k=10))
            for s in sources:
                name = Path(s["source"]).relative_to(root).as_posix()
                s["_flag"] = score(s["content"], name) > threshold
                a = s["metadata"]["start_index"]
                s["_edited"] = any(x < a + len(s["content"]) and a < y for x, y in spans[name])
            kept = [s for s in sources if not s["_flag"]][:3]
            base = sources[:3]
            for label, chosen in (("unfiltered", base), ("filtered", kept)):
                hit, _ = hit_at_3_and_reciprocal_rank(chosen, q["expected_attack_type"], q["expected_sections"])
                stats[f"{label}_hit3"] += hit
                stats[f"{label}_edited_exposure"] += int(any(s["_edited"] for s in chosen))
            stats["flagged_in_top3"] += sum(s["_flag"] for s in base)
            stats["edited_in_top3"] += sum(s["_edited"] for s in base)
            stats["edited_flagged_in_top3"] += sum(s["_flag"] and s["_edited"] for s in base)
            rows.append({"state": state, "id": q["id"], "split": q["split"],
                         "base": [(s["source"].split("knowledge_base/")[-1], s["metadata"]["start_index"], s["_flag"], s["_edited"]) for s in base]})
        n = len(questions)
        summary[state] = {k: round(v / n, 4) if k.endswith(("hit3", "exposure")) else v for k, v in stats.items()}
        summary[state]["questions"] = n
    payload = {"score": SCORE, "threshold": threshold, "k_retrieved": 10, "summary": summary, "rows": rows}
    Path(out).open("x").write(json.dumps(payload, indent=1))
    print(json.dumps({"threshold": threshold, **summary}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
