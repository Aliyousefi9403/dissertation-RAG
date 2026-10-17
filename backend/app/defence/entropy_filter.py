"""Relative-entropy / synonym-gap retrieval filter (defence, policy entropy-filter-v1).

Idea (information theory). PWWS rewrites a passage by swapping words for
WordNet synonyms that make a surrogate classifier fail. Those synonyms are
often unusual for the domain ("server" -> "waiter", "implants" -> "engraft").
Against a reference word distribution q, such a passage carries words that are
much less probable than a synonym the author would normally have used. For
each word w with WordNet synonyms S(w):

    gap(w) = max_{s in S(w)} log2 q(s) - log2 q(w)          (bits)

A chunk's score is the mean of its three largest gaps. Chunks scoring above a
threshold are dropped at retrieval time and the next-ranked chunks are used.
The score is a frequency-guided substitution detector (after FGWS, Mozes et al.
2021), measured in bits against a domain reference: the same quantity that
appears inside relative entropy KL(p||q) = sum_w p(w) log2 p(w)/q(w).

Reference distribution q (what a defender has, nothing more):
    q(w) = 0.5 * (count of w in the OTHER documents of the collection / total)
         + 0.5 * general-English frequency (wordfreq), floored at 1e-9
No clean copy, attack manifest or label is used at runtime.

Frozen parameters. The threshold 7.2262 bits was fixed on development-document
chunks of the poisoned collection at a 10% false-positive rate
(docs/research/results/entropy-detector-20261016/detector-poisoned.json) before
any answer-level evaluation. Changing it is a research-methodology change and
needs a new POLICY_VERSION.

Limitations: one attack (PWWS) and one corpus; an adaptive attacker who picks
domain-frequent synonyms can evade it; it reduces exposure to poisoned text
but cannot restore information that only exists in a poisoned passage.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from langchain_core.documents import Document

POLICY_VERSION = "entropy-filter-v1"
SCORE_NAME = "syngap_top3_domain"
THRESHOLD_BITS = 7.2262
CANDIDATE_K = 10
KEEP = 3
LAMBDA = 0.5
FLOOR = 1e-9
TOP_GAPS = 3
SOURCE_STATE_FOR_DEFENDED = "poisoned"

_TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")
STOPWORDS = frozenset({
    "the", "and", "for", "that", "this", "with", "are", "was", "from", "have", "has", "can", "may",
    "its", "not", "but", "they", "their", "which", "into", "such", "these", "than", "will", "use"})


class DetectorUnavailable(RuntimeError):
    """WordNet or wordfreq is missing; the defence fails closed, never silently passes."""


def tokens(text: str) -> list[str]:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\(Citation:[^)]*\)|https?://\S+", " ", text)
    return _TOKEN.findall(text.lower())


@lru_cache(maxsize=1)
def _wordnet():
    try:
        from nltk.corpus import wordnet

        wordnet.synsets("server")
        return wordnet
    except (ImportError, LookupError) as error:
        raise DetectorUnavailable(
            "WordNet data is required: python -m nltk.downloader wordnet"
        ) from error


@lru_cache(maxsize=1)
def _english() -> Callable[[str], float]:
    try:
        from wordfreq import word_frequency
    except ImportError as error:
        raise DetectorUnavailable("wordfreq is required: pip install wordfreq") from error
    return lambda word: word_frequency(word, "en")


@lru_cache(maxsize=50_000)
def synonyms(word: str) -> frozenset[str]:
    return frozenset(
        lemma.name().lower()
        for synset in _wordnet().synsets(word)
        for lemma in synset.lemmas()
        if lemma.name().isalpha() and lemma.name().lower() != word
    )


class DomainReference:
    """Leave-one-document-out unigram counts for one collection root."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.counts = {
            path.relative_to(self.root).as_posix(): Counter(tokens(path.read_text(encoding="utf-8")))
            for path in sorted(self.root.rglob("*.md"))
        }
        self.total = sum(self.counts.values(), Counter())
        self.total_n = sum(self.total.values())
        self.doc_n = {name: sum(c.values()) for name, c in self.counts.items()}

    def probability(self, word: str, document: str) -> float:
        own = self.counts.get(document, Counter())
        rest_total = self.total_n - self.doc_n.get(document, 0)
        rest = (self.total[word] - own[word]) / rest_total if rest_total else 0.0
        return LAMBDA * rest + (1 - LAMBDA) * max(_english()(word), FLOOR)


@lru_cache(maxsize=8)
def reference_for(root: str) -> DomainReference:
    return DomainReference(Path(root))


def score_text(text: str, document: str, reference: DomainReference) -> dict[str, Any]:
    """Synonym-gap score in bits plus the words that drive it (for audit and display)."""
    q = lambda w: reference.probability(w, document)  # noqa: E731
    gaps = []
    for word in set(tokens(text)):
        if len(word) <= 2 or word in STOPWORDS:
            continue
        candidates = synonyms(word)
        if not candidates:
            continue
        best = max(candidates, key=q)
        gaps.append((math.log2(q(best)) - math.log2(q(word)), word, best))
    gaps.sort(reverse=True)
    top = gaps[:TOP_GAPS]
    score = sum(g for g, _, _ in top) / TOP_GAPS if top else 0.0
    return {
        "score_bits": round(score, 4),
        "threshold_bits": THRESHOLD_BITS,
        "flagged": score > THRESHOLD_BITS,
        "top_words": [{"word": w, "likely_original": s, "gap_bits": round(g, 2)} for g, w, s in top],
    }


def _relative_document(source: str, root: Path) -> str:
    try:
        return Path(source).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return "/".join(Path(source).parts[-2:])


def filter_results(
    results: list[tuple[Document, float]],
    root: Path,
    *,
    keep: int = KEEP,
) -> tuple[list[tuple[Document, float]], list[dict[str, Any]]]:
    """Drop flagged chunks from ranked results; return (kept top-`keep`, decisions)."""
    reference = reference_for(str(root))
    kept, decisions = [], []
    for rank, (document, similarity) in enumerate(results, start=1):
        name = _relative_document(document.metadata.get("source", ""), root)
        verdict = score_text(document.page_content, name, reference)
        decisions.append({"rank": rank, "document": name, "start_index": document.metadata.get("start_index"),
                          "similarity": round(float(similarity), 4), **verdict,
                          "kept": not verdict["flagged"] and len(kept) < keep})
        if not verdict["flagged"] and len(kept) < keep:
            annotated = Document(page_content=document.page_content,
                                 metadata={**document.metadata, "entropy_filter": {
                                     "policy_version": POLICY_VERSION, "candidate_rank": rank, **verdict}})
            kept.append((annotated, similarity))
    return kept, decisions


def make_filtered_retrieval(source_state: str, *, k: int = CANDIDATE_K, keep: int = KEEP, capture: dict | None = None):
    """Retrieval function compatible with rag_chain.answer_question(retrieval_fn=...).

    Searches `source_state`'s collection for `k` candidates, filters, keeps `keep`.
    """
    from app.config import get_knowledge_base_path
    from app.retrieval.search import search_knowledge_base

    root = get_knowledge_base_path(source_state)

    def retrieve(question: str, system_state: str = "defended"):
        candidates = search_knowledge_base(query=question, k=k, system_state=source_state)
        kept, decisions = filter_results(candidates, root, keep=keep)
        if capture is not None:
            capture["entropy_filter"] = {"policy_version": POLICY_VERSION, "source_state": source_state,
                                         "candidate_k": k, "keep": keep, "threshold_bits": THRESHOLD_BITS,
                                         "decisions": decisions}
        return kept

    return retrieve


def defended_retrieve(question: str, system_state: str = "defended"):
    """The `defended` system state: the PWWS-poisoned collection behind the entropy filter."""
    return make_filtered_retrieval(SOURCE_STATE_FOR_DEFENDED)(question, system_state)


def retrieval_for_state(system_state: str):
    """Retrieval override for /chat: only `defended` is filtered; others use the default."""
    return defended_retrieve if system_state == "defended" else None
