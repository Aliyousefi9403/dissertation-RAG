"""Contextual synonym-gap retrieval filter (defence, policy contextual-filter-v1).

Same idea as entropy_filter.py, the log-ratio between a word and its likely
original, but the reference distribution q is a small causal language model
(distilgpt2) that reads the whole passage instead of a unigram table:

    gap(w -> s) = log2 p_LM(passage with w replaced by s) - log2 p_LM(passage)   (bits)

Candidates: the CANDIDATE_WORDS words with the largest unigram synonym gap
(entropy_filter's leave-one-document-out reference), each tried with its
CANDIDATE_SYNONYMS most probable WordNet synonyms under that reference. A
word's gap is its best synonym's gap; a passage's score is the mean of its
three largest word gaps. Passages above THRESHOLD_BITS are dropped and the
next-ranked passages are used, exactly as in the drop defence.

Frozen parameters. THRESHOLD_BITS was fixed on development-document chunks of
the poisoned collection at a 10% false-positive rate
(docs/research/results/entropy-family/family-poisoned.json) before any
answer-level evaluation. Evaluated offline: AUROC 0.95 on the PWWS corpus,
0.53 on the formatting-only control, 0.92 against the frequency-constrained
adaptive attacker (results section 16).

Fails closed: without transformers/torch or WordNet it raises DetectorUnavailable.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.defence.entropy_filter import (
    CANDIDATE_K, KEEP, STOPWORDS, SOURCE_STATE_FOR_DEFENDED, DetectorUnavailable, DomainReference,
    _relative_document, reference_for, synonyms, tokens,
)

POLICY_VERSION = "contextual-filter-v1"
SCORE_NAME = "ctx_syngap_top3"
THRESHOLD_BITS = 4.4611
LM_NAME = "distilgpt2"
CANDIDATE_WORDS = 10
CANDIDATE_SYNONYMS = 5
TOP_GAPS = 3
MAX_TOKENS = 256
BATCH = 16


class LanguageModel:
    def __init__(self, name: str = LM_NAME, max_tokens: int = MAX_TOKENS):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise DetectorUnavailable("transformers and torch are required for the contextual filter") from error
        self.torch = torch
        self.max_tokens = max_tokens
        self.tok = AutoTokenizer.from_pretrained(name)
        self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(name).eval()

    def log2_prob(self, texts: list[str]) -> list[float]:
        """Total log2 probability of each text (first token excluded)."""
        torch = self.torch
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), BATCH):
                enc = self.tok([self.tok.bos_token + t for t in texts[i:i + BATCH]], return_tensors="pt",
                               padding=True, truncation=True, max_length=self.max_tokens)
                logits = self.model(**enc).logits[:, :-1]
                target = enc.input_ids[:, 1:]
                mask = enc.attention_mask[:, 1:].bool()
                nll = torch.nn.functional.cross_entropy(logits.transpose(1, 2), target, reduction="none") / math.log(2)
                out += [-float(row[m].sum()) for row, m in zip(nll, mask)]
        return out


@lru_cache(maxsize=1)
def language_model() -> LanguageModel:
    return LanguageModel()


def replace_word(text: str, word: str, synonym: str) -> str:
    def keep_case(match: re.Match) -> str:
        return synonym.capitalize() if match.group(0)[0].isupper() else synonym
    return re.sub(rf"\b{re.escape(word)}\b", keep_case, text, flags=re.IGNORECASE)


def candidates(text: str, document: str, reference: DomainReference) -> list[tuple[str, list[str]]]:
    """The words with the largest unigram synonym gap, each with its most probable synonyms."""
    q = lambda w: reference.probability(w, document)  # noqa: E731
    gaps = []
    for word in sorted(set(tokens(text))):
        if len(word) <= 2 or word in STOPWORDS:
            continue
        ranked = sorted(sorted(synonyms(word)), key=q, reverse=True)
        if ranked:
            gaps.append((math.log2(q(ranked[0])) - math.log2(q(word)), word, ranked[:CANDIDATE_SYNONYMS]))
    gaps.sort(key=lambda g: (-g[0], g[1]))
    return [(word, syns) for _, word, syns in gaps[:CANDIDATE_WORDS]]


def score_text(text: str, document: str, reference: DomainReference, lm: LanguageModel | None = None) -> dict[str, Any]:
    """Contextual synonym-gap score in bits plus the words that drive it."""
    variants = [(w, s, replace_word(text, w, s)) for w, syns in candidates(text, document, reference) for s in syns]
    best: dict[str, tuple[float, str]] = {}
    if variants:
        lm = lm or language_model()
        base, *scores = lm.log2_prob([text] + [v for _, _, v in variants])
        for (word, synonym, _), lp in zip(variants, scores):
            if lp - base > best.get(word, (-math.inf, ""))[0]:
                best[word] = (lp - base, synonym)
    top = sorted(best.items(), key=lambda kv: -kv[1][0])[:TOP_GAPS]
    score = sum(g for _, (g, _) in top) / TOP_GAPS if top else 0.0
    return {
        "score_bits": round(score, 4),
        "threshold_bits": THRESHOLD_BITS,
        "flagged": score > THRESHOLD_BITS,
        "top_words": [{"word": w, "likely_original": s, "gap_bits": round(g, 2)} for w, (g, s) in top],
    }


# A passage's score depends only on its text, its document and the collection, so it is cached
# for the life of the process (the same passages recur across questions and repetitions).
_SCORE_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}


def filter_results(results: list[tuple[Document, float]], root: Path, *, keep: int = KEEP,
                   lm: LanguageModel | None = None) -> tuple[list[tuple[Document, float]], list[dict[str, Any]]]:
    """Drop flagged chunks from ranked results; return (kept top-`keep`, decisions)."""
    reference = reference_for(str(root))
    kept, decisions = [], []
    for rank, (document, similarity) in enumerate(results, start=1):
        name = _relative_document(document.metadata.get("source", ""), root)
        if lm is not None:  # an explicitly supplied model (tests) is never cached
            verdict = score_text(document.page_content, name, reference, lm)
        else:
            key = (str(root), name, document.page_content)
            if key not in _SCORE_CACHE:
                _SCORE_CACHE[key] = score_text(document.page_content, name, reference)
            verdict = _SCORE_CACHE[key]
        decisions.append({"rank": rank, "document": name, "start_index": document.metadata.get("start_index"),
                          "similarity": round(float(similarity), 4), **verdict,
                          "kept": not verdict["flagged"] and len(kept) < keep})
        if not verdict["flagged"] and len(kept) < keep:
            # Same metadata key as the drop defence, so the interface reads both the same way.
            annotated = Document(page_content=document.page_content,
                                 metadata={**document.metadata, "entropy_filter": {
                                     "policy_version": POLICY_VERSION, "candidate_rank": rank, **verdict}})
            kept.append((annotated, similarity))
    return kept, decisions


def make_filtered_retrieval(source_state: str, *, k: int = CANDIDATE_K, keep: int = KEEP, capture: dict | None = None):
    """Retrieval function compatible with rag_chain.answer_question(retrieval_fn=...)."""
    from app.config import get_knowledge_base_path
    from app.retrieval.search import search_knowledge_base

    root = get_knowledge_base_path(source_state)

    def retrieve(question: str, system_state: str = "contextual"):
        found = search_knowledge_base(query=question, k=k, system_state=source_state)
        kept, decisions = filter_results(found, root, keep=keep)
        if capture is not None:
            capture["entropy_filter"] = {"policy_version": POLICY_VERSION, "source_state": source_state,
                                         "candidate_k": k, "keep": keep, "threshold_bits": THRESHOLD_BITS,
                                         "lm": LM_NAME, "decisions": decisions}
        return kept

    return retrieve


def contextual_retrieve(question: str, system_state: str = "contextual"):
    """The `contextual` system state: the PWWS-poisoned collection behind the contextual filter."""
    return make_filtered_retrieval(SOURCE_STATE_FOR_DEFENDED)(question, system_state)
