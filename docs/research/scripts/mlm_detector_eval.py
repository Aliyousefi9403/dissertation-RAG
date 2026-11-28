"""Bidirectional (masked language model) detectors for word-substitution poisoning.

Suggested by N. Komninos: a transformer that reads the context on both sides of a word, such as
DistilBERT, should suit substitution edits better than distilgpt2, which sees only the words
before it. Same chunks, labels, development/held-out split and candidate words as
entropy_family_eval.py; only the language model and the way a word is scored change.

  mlm_syngap_top3   For the 10 words with the largest domain synonym gap and their 5 most
                    domain-probable WordNet synonyms s: mask the word's word pieces and score
                    log2 p(word | both sides); do the same with s in its place. Gap = score(s) -
                    score(word), in bits; per word keep the best synonym; passage score = mean of
                    the 3 largest gaps. The bidirectional version of ctx_syngap_top3.
  mlm_mean_pll      Mean masked-token surprisal (pseudo-log-likelihood, each token masked in turn).
  mlm_top5_pll      Mean of the 5 largest masked-token surprisals: the bidirectional counterpart
                    of the windowed-perplexity baseline (lm_top5_surprisal).

The pre-trained distilbert-base-uncased masked LM is used; it is not the DistilBERT classifier the
attacker fools. Wall-clock seconds per passage are recorded for the cost comparison. Offline.

Usage (from backend/):
  PYTHONPATH=. python ../docs/research/scripts/mlm_detector_eval.py OUT.json CORPUS [FAMILY.json]
CORPUS as in entropy_family_eval.py (including kb_v2). FAMILY.json (optional): that script's output for the same
corpus; rows are matched by (document, start) to compare with the distilgpt2 scores.
"""

import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from app.config import get_knowledge_base_path
from app.ingestion.load_documents import add_document_metadata, split_documents
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from transformers import AutoModelForMaskedLM, AutoTokenizer
from wordfreq import word_frequency

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entropy_detection_eval import (
    FLOOR,
    LAMBDA,
    STOPWORDS,
    auroc,
    edited_spans,
    synonyms,
    threshold_for_fpr,
    tokens,
    tpr_at_fpr,
)
from entropy_family_eval import held_out_documents

ROOT = Path(__file__).resolve().parents[3] / "backend"
MLM_NAME = "distilbert-base-uncased"
CANDIDATE_WORDS, CANDIDATE_SYNONYMS, TOP = 10, 5, 3
BATCH, MAX_TOKENS = 32, 256
SEED, B = 20261016, 2000
torch.manual_seed(0)
torch.set_num_threads(int(os.environ.get("AEGIS_THREADS", "2")))


class MaskedLM:
    def __init__(self):
        self.tok = AutoTokenizer.from_pretrained(MLM_NAME)
        self.model = AutoModelForMaskedLM.from_pretrained(MLM_NAME).eval()

    def encode(self, text):
        return self.tok(
            text,
            return_offsets_mapping=True,
            truncation=True,
            max_length=MAX_TOKENS,
        )

    @torch.no_grad()
    def score(self, jobs):
        """jobs: (input_ids, positions to mask). Returns sum of log2 p(original | masked) per job."""
        out = []
        for i in range(0, len(jobs), BATCH):
            part = jobs[i : i + BATCH]
            width = max(len(ids) for ids, _ in part)
            ids = torch.full((len(part), width), self.tok.pad_token_id)
            att = torch.zeros((len(part), width), dtype=torch.long)
            for r, (seq, pos) in enumerate(part):
                ids[r, : len(seq)] = torch.tensor(seq)
                att[r, : len(seq)] = 1
                for p in pos:
                    ids[r, p] = self.tok.mask_token_id
            logp = torch.log_softmax(
                self.model(input_ids=ids, attention_mask=att).logits, -1
            ) / math.log(2)
            for r, (seq, pos) in enumerate(part):
                out.append(sum(float(logp[r, p, seq[p]]) for p in pos))
        return out


def first_span(text, word):
    m = re.search(rf"\b{re.escape(word)}\b", text, flags=re.IGNORECASE)
    return (m.start(), m.end(), m.group(0)) if m else None


def piece_positions(enc, start, end):
    return [
        i
        for i, (a, b) in enumerate(enc["offset_mapping"])
        if b > a >= start and b <= end
    ]


def keep_case(new, like):
    return new.capitalize() if like[:1].isupper() else new


def word_job(mlm, text, start, end):
    enc = mlm.encode(text)
    pos = piece_positions(enc, start, end)
    return (enc["input_ids"], pos) if pos else None


def corpus_root(corpus):
    if corpus == "kb_v2":
        return ROOT / "data/kb_v2/poisoned_pwws/knowledge_base"
    if corpus == "poisoned":
        return get_knowledge_base_path("poisoned")
    if corpus.startswith("poisoned"):
        return ROOT / f"data/{corpus}/knowledge_base"
    return ROOT / "data/control/knowledge_base"


def clustered_ci(rows, key, base=None):
    """Document-clustered bootstrap: AUROC interval, or the paired difference key - base."""
    docs = sorted({r["document"] for r in rows})
    by = {d: [r for r in rows if r["document"] == d] for d in docs}
    rng, vals = random.Random(SEED), []
    for _ in range(B):
        sample = [r for d in (rng.choice(docs) for _ in docs) for r in by[d]]
        labels = [r["label"] for r in sample]
        if len(set(labels)) < 2:
            continue
        a = auroc([r[key] for r in sample], labels)
        vals.append(a - auroc([r[base] for r in sample], labels) if base else a)
    vals.sort()
    return [
        round(vals[int(0.025 * len(vals))], 3),
        round(vals[int(0.975 * len(vals)) - 1], 3),
    ]


def main(out, corpus, family=None):
    attacked = corpus.startswith("poisoned") or corpus == "kb_v2"
    root = corpus_root(corpus)
    manifest = (
        root.parent / "pwws_attack_manifest.jsonl"
        if attacked and corpus != "poisoned"
        else ROOT / "data/poisoned/pwws_attack_manifest.jsonl"
    )
    documents = add_document_metadata(
        DirectoryLoader(
            str(root),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        ).load(),
        "poisoned",
    )
    chunks = split_documents(documents)
    texts = {
        Path(d.metadata["source"]).relative_to(root).as_posix(): d.page_content
        for d in documents
    }
    spans = {name: [] for name in texts}
    for entry in (
        json.loads(x) for x in manifest.read_text().splitlines() if x.strip()
    ):
        if entry.get("success"):
            spans[entry["file"]] += edited_spans(
                texts[entry["file"]], entry, "adversarial" if attacked else "original"
            )
    held_out = held_out_documents(corpus, texts)
    doc_counts = {name: Counter(tokens(t)) for name, t in texts.items()}
    total = sum(doc_counts.values(), Counter())
    total_n = sum(total.values())
    mlm = MaskedLM()
    rows = []
    for chunk in chunks:
        name = Path(chunk.metadata["source"]).relative_to(root).as_posix()
        start, content = chunk.metadata["start_index"], chunk.page_content
        words = tokens(content)
        if len(words) < 10:
            continue
        own = doc_counts[name]
        rest_n = total_n - sum(own.values())

        def q(w, own=own, rest_n=rest_n):
            return LAMBDA * (total[w] - own[w]) / rest_n + (1 - LAMBDA) * max(
                word_frequency(w, "en"), FLOOR
            )

        gaps = []
        for w in set(words):
            if len(w) > 2 and w not in STOPWORDS and synonyms(w):
                ranked = sorted(synonyms(w), key=q, reverse=True)
                gaps.append(
                    (
                        math.log2(q(ranked[0])) - math.log2(q(w)),
                        w,
                        ranked[:CANDIDATE_SYNONYMS],
                    )
                )
        gaps.sort(reverse=True)
        candidates = gaps[:CANDIDATE_WORDS]
        t0 = time.perf_counter()
        jobs, keys = [], []
        for _, w, syns in candidates:
            found = first_span(content, w)
            if not found:
                continue
            a, b, written = found
            job = word_job(mlm, content, a, b)
            if not job:
                continue
            jobs.append(job)
            keys.append((w, None))
            for s in syns:
                sub = keep_case(s.replace("_", " "), written)
                variant = content[:a] + sub + content[b:]
                job = word_job(mlm, variant, a, a + len(sub))
                if job:
                    jobs.append(job)
                    keys.append((w, s))
        scores = mlm.score(jobs)
        base, best = {}, {}
        for (w, s), lp in zip(keys, scores):
            if s is None:
                base[w] = lp
        for (w, s), lp in zip(keys, scores):
            if (
                s is not None
                and w in base
                and lp - base[w] > best.get(w, (-1e9, ""))[0]
            ):
                best[w] = (lp - base[w], s)
        ranked = sorted(best.items(), key=lambda kv: -kv[1][0])
        gap_seconds = time.perf_counter() - t0
        t1 = time.perf_counter()
        enc = mlm.encode(content)
        ids = enc["input_ids"]
        surprisals = [
            -x for x in mlm.score([(ids, [p]) for p in range(1, len(ids) - 1)])
        ]
        pll_seconds = time.perf_counter() - t1
        rows.append(
            {
                "document": name,
                "start": start,
                "label": int(
                    any(a < start + len(content) and start < b for a, b in spans[name])
                ),
                "split": "held_out" if name in held_out else "development",
                "mlm_syngap_top3": sum(g for _, (g, _) in ranked[:TOP]) / TOP
                if ranked
                else 0.0,
                "mlm_top_words": [
                    {"word": w, "likely_original": s, "gap_bits": round(g, 2)}
                    for w, (g, s) in ranked[:TOP]
                ],
                "mlm_mean_pll": sum(surprisals) / len(surprisals),
                "mlm_top5_pll": sum(sorted(surprisals, reverse=True)[:5]) / 5,
                "seconds_syngap": round(gap_seconds, 3),
                "seconds_pll": round(pll_seconds, 3),
            }
        )
        print(f"{len(rows)} chunks scored", end="\r", flush=True)

    scores = ["mlm_syngap_top3", "mlm_mean_pll", "mlm_top5_pll"]
    compare = []
    if family:
        fam = {
            (r["document"], r["start"]): r
            for r in json.loads(Path(family).read_text())["rows"]
        }
        for r in rows:
            f = fam.get((r["document"], r["start"]))
            if f:
                for k in ("ctx_syngap_top3", "lm_top5_surprisal", "syngap_top3_domain"):
                    r[k] = f[k]
        if all("ctx_syngap_top3" in r for r in rows):
            compare = ["ctx_syngap_top3", "lm_top5_surprisal", "syngap_top3_domain"]
    results = {}
    for split in ("development", "held_out", "all"):
        subset = [r for r in rows if split == "all" or r["split"] == split]
        labels = [r["label"] for r in subset]
        results[split] = {"chunks": len(subset), "positives": sum(labels)}
        if 0 < sum(labels) < len(labels):
            for s in scores + compare:
                results[split][s] = {
                    "auroc": round(auroc([r[s] for r in subset], labels), 4)
                }
            if split == "all":
                for s in scores:
                    results[split][s]["ci95"] = clustered_ci(subset, s)
                for s, base in (
                    ("mlm_syngap_top3", "ctx_syngap_top3"),
                    ("mlm_syngap_top3", "lm_top5_surprisal"),
                    ("mlm_top5_pll", "lm_top5_surprisal"),
                ):
                    if base in compare:
                        results[split][f"{s}_minus_{base}"] = {
                            "delta": round(
                                results[split][s]["auroc"]
                                - results[split][base]["auroc"],
                                4,
                            ),
                            "ci95": clustered_ci(subset, s, base),
                        }
    dev = [r for r in rows if r["split"] == "development"]
    held = [r for r in rows if r["split"] == "held_out"]
    if dev and 0 < sum(r["label"] for r in dev) < len(dev):
        for s in scores:
            t = threshold_for_fpr([r[s] for r in dev], [r["label"] for r in dev], 0.10)
            results["development"][s]["threshold_fpr10"] = round(t, 4)
            if held and 0 < sum(r["label"] for r in held) < len(held):
                results["held_out"][s]["tpr_fpr_at_dev_threshold"] = tpr_at_fpr(
                    [r[s] for r in held], [r["label"] for r in held], t
                )
    cost = {
        "mean_seconds_per_passage_syngap": round(
            sum(r["seconds_syngap"] for r in rows) / len(rows), 3
        ),
        "mean_seconds_per_passage_pll": round(
            sum(r["seconds_pll"] for r in rows) / len(rows), 3
        ),
        "threads": torch.get_num_threads(),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with Path(out).open("x") as handle:
        handle.write(
            json.dumps(
                {
                    "corpus": corpus,
                    "parameters": {
                        "mlm": MLM_NAME,
                        "candidate_words": CANDIDATE_WORDS,
                        "candidate_synonyms": CANDIDATE_SYNONYMS,
                        "top": TOP,
                        "bootstrap": {"B": B, "seed": SEED, "resample": "documents"},
                    },
                    "cost": cost,
                    "results": results,
                    "rows": rows,
                },
                indent=1,
            )
        )
    print()
    for split in ("development", "held_out", "all"):
        print(split, json.dumps({k: v for k, v in results[split].items()}))
    print("cost", cost)


if __name__ == "__main__":
    main(*sys.argv[1:4])
