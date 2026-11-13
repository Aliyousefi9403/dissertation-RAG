"""Entropy-family detectors for PWWS-poisoned chunks: better references q and symmetric divergences.

Extends entropy_detection_eval.py (same chunks, labels, split and AUROC) with:

  syngap_top3_domain      baseline: synonym gap, q = 0.5 domain (leave-one-document-out) + 0.5 English
  syngap_top3_dirichlet   synonym gap with a Dirichlet-prior reference
                          q(w) = (c_rest(w) + mu * q_en(w)) / (N_rest + mu), mu = 2000
  js_domain               Jensen-Shannon divergence JS(p_chunk, q_domain) in bits (symmetric, bounded by 1)
  lm_mean_surprisal       mean per-token surprisal -log2 p(token | left context) under a causal LM (distilgpt2)
  lm_top5_surprisal       mean of the 5 largest per-token surprisals
  ctx_syngap_top3         contextual synonym gap: for the 10 words with the largest domain synonym gap,
                          log2 p_LM(chunk with w -> s) - log2 p_LM(chunk) for its 5 most domain-probable
                          synonyms s; score = mean of the 3 largest gaps. The same log-ratio as the
                          synonym gap, with q replaced by a language model that sees the sentence.

No API calls; the LM runs locally. The PWWS manifest is used only for labels.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/entropy_family_eval.py OUT.json [poisoned|control|poisoned_adaptive|poisoned_pwws_rerun]
"""

import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

import torch
from app.config import get_knowledge_base_path
from app.ingestion.load_documents import add_document_metadata, split_documents
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from wordfreq import word_frequency

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entropy_detection_eval import (  # noqa: E402
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

ROOT = Path(__file__).resolve().parents[3] / "backend"
MU = 2000
LM_NAME = os.environ.get("AEGIS_LM", "distilgpt2")  # default is the deployed detector's model
CANDIDATE_WORDS, CANDIDATE_SYNONYMS = 10, 5
torch.manual_seed(0)


class LanguageModel:
    def __init__(self):
        self.tok = AutoTokenizer.from_pretrained(LM_NAME)
        self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(LM_NAME).eval()

    @torch.no_grad()
    def token_surprisals(self, texts, batch=16):
        """Per-token surprisal in bits for each text (first token excluded)."""
        out = []
        for i in range(0, len(texts), batch):
            enc = self.tok(
                [self.tok.bos_token + t for t in texts[i : i + batch]],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=256,
            )
            logits = self.model(**enc).logits[:, :-1]
            target = enc.input_ids[:, 1:]
            mask = enc.attention_mask[:, 1:].bool()
            nll = torch.nn.functional.cross_entropy(
                logits.transpose(1, 2), target, reduction="none"
            ) / math.log(2)
            out += [row[m].tolist() for row, m in zip(nll, mask)]
        return out

    def log2_prob(self, texts):
        return [-sum(s) for s in self.token_surprisals(texts)]


def replace_word(text, word, synonym):
    import re

    def keep_case(m):
        return synonym.capitalize() if m.group(0)[0].isupper() else synonym

    return re.sub(rf"\b{re.escape(word)}\b", keep_case, text, flags=re.IGNORECASE)


def main(out, corpus="poisoned"):
    attacked = corpus.startswith(
        "poisoned"
    )  # every attack corpus (data/poisoned*/ with an attack manifest)
    root = (
        get_knowledge_base_path("poisoned")
        if corpus == "poisoned"
        else ROOT / f"data/{corpus}/knowledge_base"
        if attacked
        else ROOT / "data/control/knowledge_base"
    )
    manifest_path = (
        ROOT / f"data/{corpus if attacked else 'poisoned'}/pwws_attack_manifest.jsonl"
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
        json.loads(line)
        for line in manifest_path.read_text().splitlines()
        if line.strip()
    ):
        if entry.get("success"):
            spans[entry["file"]] += edited_spans(
                texts[entry["file"]], entry, "adversarial" if attacked else "original"
            )
    held_out = set(
        json.loads((ROOT / "data/evaluation/benchmark_v1_record.json").read_text())[
            "held_out_documents"
        ]
    )
    doc_counts = {name: Counter(tokens(t)) for name, t in texts.items()}
    total = sum(doc_counts.values(), Counter())
    total_n = sum(total.values())
    lm = LanguageModel()

    def q_en(w):
        return max(word_frequency(w, "en"), FLOOR)

    rows = []
    for chunk in chunks:
        name = Path(chunk.metadata["source"]).relative_to(root).as_posix()
        start, content = chunk.metadata["start_index"], chunk.page_content
        words = tokens(content)
        if len(words) < 10:
            continue
        own = doc_counts[name]
        rest_n = total_n - sum(own.values())
        rest = lambda w: total[w] - own[w]  # noqa: E731
        q_dom = lambda w: LAMBDA * rest(w) / rest_n + (1 - LAMBDA) * q_en(w)  # noqa: E731
        q_dir = lambda w: (rest(w) + MU * q_en(w)) / (rest_n + MU)  # noqa: E731
        row = {
            "document": name,
            "start": start,
            "label": int(
                any(a < start + len(content) and start < b for a, b in spans[name])
            ),
            "split": "held_out" if name in held_out else "development",
        }
        candidates = []
        for key, q in (("domain", q_dom), ("dirichlet", q_dir)):
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
            row[f"syngap_top3_{key}"] = (
                sum(g for g, _, _ in gaps[:3]) / 3 if gaps else 0.0
            )
            if key == "domain":
                candidates = gaps[:CANDIDATE_WORDS]
        # Jensen-Shannon divergence between the chunk's word distribution and q_domain (renormalised
        # over the union vocabulary), in bits.
        p = Counter(words)
        vocab = set(p) | {w for w, c in total.items() if c - own[w] > 0}
        qv = {w: q_dom(w) for w in vocab}
        z = sum(qv.values())
        js = 0.0
        for w in vocab:
            pw, qw = p.get(w, 0) / len(words), qv[w] / z
            m = (pw + qw) / 2
            js += (0.5 * pw * math.log2(pw / m) if pw else 0) + (
                0.5 * qw * math.log2(qw / m) if qw else 0
            )
        row["js_domain"] = js
        surprisals = lm.token_surprisals([content])[0]
        row["lm_mean_surprisal"] = sum(surprisals) / len(surprisals)
        row["lm_top5_surprisal"] = sum(sorted(surprisals, reverse=True)[:5]) / 5
        variants = [
            (w, s, replace_word(content, w, s))
            for _, w, syns in candidates
            for s in syns
        ]
        if variants:
            base = lm.log2_prob([content])[0]
            scores = lm.log2_prob([v for _, _, v in variants])
            best = {}
            for (w, s, _), lp in zip(variants, scores):
                if lp - base > best.get(w, (-1e9, ""))[0]:
                    best[w] = (lp - base, s)
            ctx = sorted(best.items(), key=lambda kv: -kv[1][0])
            row["ctx_syngap_top3"] = sum(g for _, (g, _) in ctx[:3]) / 3
            row["ctx_top_words"] = [
                {"word": w, "likely_original": s, "gap_bits": round(g, 2)}
                for w, (g, s) in ctx[:3]
            ]
        else:
            row["ctx_syngap_top3"], row["ctx_top_words"] = 0.0, []
        rows.append(row)
        print(f"{len(rows)} chunks scored", end="\r", flush=True)

    scores = [
        "syngap_top3_domain",
        "syngap_top3_dirichlet",
        "js_domain",
        "lm_mean_surprisal",
        "lm_top5_surprisal",
        "ctx_syngap_top3",
    ]
    results = {}
    for split in ("development", "held_out", "all"):
        subset = [r for r in rows if split == "all" or r["split"] == split]
        labels = [r["label"] for r in subset]
        results[split] = {
            "chunks": len(subset),
            "positives": sum(labels),
            **{s: {"auroc": auroc([r[s] for r in subset], labels)} for s in scores},
        }
    dev = [r for r in rows if r["split"] == "development"]
    held = [r for r in rows if r["split"] == "held_out"]
    for s in scores:
        t = threshold_for_fpr([r[s] for r in dev], [r["label"] for r in dev], 0.10)
        results["development"][s]["threshold_fpr10"] = round(t, 4)
        results["held_out"][s]["tpr_fpr_at_dev_threshold"] = tpr_at_fpr(
            [r[s] for r in held], [r["label"] for r in held], t
        )
    payload = {
        "corpus": corpus,
        "parameters": {
            "mu": MU,
            "lambda": LAMBDA,
            "floor": FLOOR,
            "lm": LM_NAME,
            "candidate_words": CANDIDATE_WORDS,
            "candidate_synonyms": CANDIDATE_SYNONYMS,
        },
        "results": results,
        "rows": rows,
    }
    Path(out).open("x").write(json.dumps(payload, indent=1))
    print()
    for split in ("development", "held_out", "all"):
        print(
            f"[{split}] chunks={results[split]['chunks']} positives={results[split]['positives']}  "
            + "  ".join(f"{s}={results[split][s]['auroc']}" for s in scores)
        )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "poisoned")
