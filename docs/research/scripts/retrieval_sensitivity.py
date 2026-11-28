"""Retrieval sensitivity: does the 'lost evidence' effect depend on top-k and chunk size?

The main harm of poisoning is that the passage holding the answer falls out of the top-k. This script
re-chunks each corpus at several chunk sizes (overlap 20%), embeds the passages and the 44 benchmark
questions with the pipeline's embedding model (all-MiniLM-L6-v2, normalised, cosine similarity,
exact search), and reports for every (chunk size, k):

  hit       share of questions whose top-k contains a passage from the source document that
            overlaps one of the expected sections (Hit@k, as in the paper)
  hit drop  poisoned minus clean Hit@k, with a 95% question-level bootstrap interval
  exposure  share of questions whose top-k contains attacker-edited text (attacked corpora)

The pipeline's setting is chunk size 500, overlap 100, k = 3. Offline; no generator or judge calls.
Retrieval only: it says how often the evidence is displaced, not how the answers change.

Usage (from backend/):  PYTHONPATH=. python ../docs/research/scripts/retrieval_sensitivity.py OUT.json
"""

import json
import random
import sys
from pathlib import Path

import numpy as np
from app.ingestion.section_metadata import _heading_ranges
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entropy_detection_eval import edited_spans

ROOT = Path(__file__).resolve().parents[3] / "backend"
CORPORA = {
    "clean": ("data/raw/knowledge_base", None),
    "pwws": (
        "data/poisoned/knowledge_base",
        "data/poisoned/pwws_attack_manifest.jsonl",
    ),
    "textfooler": (
        "data/poisoned_textfooler/knowledge_base",
        "data/poisoned_textfooler/pwws_attack_manifest.jsonl",
    ),
}
CHUNK_SIZES = (300, 500, 800)
KS = (1, 3, 5, 10)
SEED, B = 20261016, 10000


def load(corpus, size):
    folder, manifest = CORPORA[corpus]
    root = ROOT / folder
    docs = DirectoryLoader(
        str(root),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    ).load()
    texts = {
        Path(d.metadata["source"]).relative_to(root).as_posix(): d.page_content
        for d in docs
    }
    spans = {name: [] for name in texts}
    if manifest:
        for entry in (
            json.loads(x)
            for x in (ROOT / manifest).read_text().splitlines()
            if x.strip()
        ):
            if entry.get("success"):
                spans[entry["file"]] += edited_spans(
                    texts[entry["file"]], entry, "adversarial"
                )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=size // 5, add_start_index=True
    )
    passages = []
    for chunk in splitter.split_documents(docs):
        name = Path(chunk.metadata["source"]).relative_to(root).as_posix()
        start, end = (
            chunk.metadata["start_index"],
            chunk.metadata["start_index"] + len(chunk.page_content),
        )
        sections = {
            s for a, b, s in _heading_ranges(texts[name]) if a < end and start < b
        }
        passages.append(
            {
                "document": name,
                "sections": sections,
                "edited": any(a < end and start < b for a, b in spans[name]),
                "text": chunk.page_content,
            }
        )
    return passages


def boot(diffs):
    rng, vals = random.Random(SEED), []
    for _ in range(B):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        vals.append(sum(sample) / len(sample))
    vals.sort()
    return [round(vals[int(0.025 * B)], 3), round(vals[int(0.975 * B) - 1], 3)]


def main(out):
    questions = json.loads((ROOT / "data/evaluation/questions_v1.json").read_text())
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    qv = model.encode([q["question"] for q in questions], normalize_embeddings=True)
    results = {}
    for size in CHUNK_SIZES:
        per = {}
        for corpus in CORPORA:
            passages = load(corpus, size)
            pv = model.encode(
                [p["text"] for p in passages], normalize_embeddings=True, batch_size=64
            )
            order = np.argsort(-(qv @ pv.T), axis=1)
            per[corpus] = {"passages": len(passages)}
            for k in KS:
                hits, exposed = [], []
                for qi, q in enumerate(questions):
                    top = [passages[i] for i in order[qi, :k]]
                    hits.append(
                        int(
                            any(
                                p["document"] == q["source_document"]
                                and p["sections"] & set(q["expected_sections"])
                                for p in top
                            )
                        )
                    )
                    exposed.append(int(any(p["edited"] for p in top)))
                per[corpus][k] = {"hits": hits, "exposed": exposed}
        cell = {}
        for k in KS:
            clean = per["clean"][k]["hits"]
            row = {"clean_hit": round(sum(clean) / len(clean), 3)}
            for attacked in ("pwws", "textfooler"):
                hits = per[attacked][k]["hits"]
                diffs = [h - c for h, c in zip(hits, clean)]
                row[attacked] = {
                    "hit": round(sum(hits) / len(hits), 3),
                    "hit_drop": round(sum(diffs) / len(diffs), 3),
                    "hit_drop_ci95": boot(diffs),
                    "exposure": round(sum(per[attacked][k]["exposed"]) / len(hits), 3),
                }
            cell[f"k={k}"] = row
        results[f"chunk={size}"] = {
            "passages": {c: per[c]["passages"] for c in CORPORA},
            **cell,
        }
        print(size, json.dumps(cell))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with Path(out).open("x") as handle:
        handle.write(
            json.dumps(
                {
                    "embedding": "sentence-transformers/all-MiniLM-L6-v2",
                    "chunk_sizes": CHUNK_SIZES,
                    "overlap": "20% of chunk size",
                    "ks": KS,
                    "questions": len(questions),
                    "bootstrap": {"B": B, "seed": SEED, "resample": "questions"},
                    "results": results,
                },
                indent=1,
            )
            + "\n"
        )


if __name__ == "__main__":
    main(sys.argv[1])
