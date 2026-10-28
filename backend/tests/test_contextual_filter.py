"""Tests for the contextual synonym-gap retrieval filter (contextual-filter-v1)."""

import json
from pathlib import Path

import pytest
from app.defence import contextual_filter as cf
from app.defence import entropy_filter as ef
from langchain_core.documents import Document

pytest.importorskip("wordfreq")
try:
    ef._wordnet()
except ef.DetectorUnavailable:  # pragma: no cover - environment without WordNet data
    pytest.skip("WordNet data not installed", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
CLEAN = "An adversary may deny legitimate users access to a server by flooding the web application with requests."
PWWS = "An adversary may abnegate legitimate users access to a waiter by flooding the entanglement coating with requests."


class StubLM:
    """Stand-in language model: shorter, more common words are 'more probable'."""

    def __init__(self):
        self.calls = 0

    def log2_prob(self, texts):
        self.calls += 1
        return [-sum(len(w) ** 1.5 for w in ef.tokens(t)) for t in texts]


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "ddos").mkdir()
    (tmp_path / "ddos/http_flood.md").write_text(CLEAN, encoding="utf-8")
    for name in ("udp", "icmp", "tcp"):
        (tmp_path / f"ddos/{name}.md").write_text(
            f"An adversary floods the server with {name} traffic to deny service to legitimate users "
            "of the web application and its server.",
            encoding="utf-8",
        )
    ef.reference_for.cache_clear()
    return tmp_path


def test_candidates_are_ranked_deterministically(corpus):
    reference = ef.DomainReference(corpus)
    first = cf.candidates(PWWS, "ddos/http_flood.md", reference)
    assert first == cf.candidates(PWWS, "ddos/http_flood.md", reference)
    assert len(first) <= cf.CANDIDATE_WORDS and all(
        len(s) <= cf.CANDIDATE_SYNONYMS for _, s in first
    )
    assert "abnegate" in [w for w, _ in first]


def test_replace_word_keeps_case_and_word_boundaries():
    assert (
        cf.replace_word("Abnegate users; abnegated stays.", "abnegate", "deny")
        == "Deny users; abnegated stays."
    )


def test_score_names_likely_originals_and_flags_substituted_text(corpus):
    reference = ef.DomainReference(corpus)
    poisoned = cf.score_text(PWWS, "ddos/http_flood.md", reference, StubLM())
    original = cf.score_text(CLEAN, "ddos/http_flood.md", reference, StubLM())
    assert poisoned["score_bits"] > original["score_bits"]
    assert poisoned["threshold_bits"] == cf.THRESHOLD_BITS
    assert {w["word"] for w in poisoned["top_words"]} & {
        "abnegate",
        "entanglement",
        "waiter",
        "coating",
    }


def test_filter_drops_flagged_backfills_and_annotates_for_the_interface(
    corpus, monkeypatch
):
    monkeypatch.setattr(cf, "THRESHOLD_BITS", 50.0)
    reference = ef.DomainReference(corpus)
    pwws_score = cf.score_text(PWWS, "ddos/http_flood.md", reference, StubLM())[
        "score_bits"
    ]
    clean_score = cf.score_text(CLEAN, "ddos/udp.md", reference, StubLM())["score_bits"]
    assert pwws_score > clean_score
    monkeypatch.setattr(cf, "THRESHOLD_BITS", (pwws_score + clean_score) / 2)
    docs = [
        (
            Document(
                page_content=PWWS,
                metadata={
                    "source": str(corpus / "ddos/http_flood.md"),
                    "start_index": 0,
                },
            ),
            0.9,
        )
    ]
    docs += [
        (
            Document(
                page_content=CLEAN,
                metadata={"source": str(corpus / f"ddos/{n}.md"), "start_index": i},
            ),
            0.8 - i / 10,
        )
        for i, n in enumerate(("udp", "icmp", "tcp", "udp"))
    ]
    kept, decisions = cf.filter_results(docs, corpus, lm=StubLM())
    assert [d["kept"] for d in decisions] == [False, True, True, True, False]
    assert len(kept) == 3
    verdict = kept[0][0].metadata["entropy_filter"]
    assert (
        verdict["policy_version"] == cf.POLICY_VERSION
        and verdict["candidate_rank"] == 2
        and not verdict["flagged"]
    )


def test_scores_are_cached_per_passage_and_never_for_an_explicit_model(
    corpus, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        cf,
        "score_text",
        lambda text, doc, ref, lm=None: (
            calls.append(doc)
            or {
                "score_bits": 0.0,
                "threshold_bits": cf.THRESHOLD_BITS,
                "flagged": False,
                "top_words": [],
            }
        ),
    )
    monkeypatch.setattr(cf, "_SCORE_CACHE", {})
    docs = [
        (
            Document(
                page_content=CLEAN,
                metadata={"source": str(corpus / "ddos/udp.md"), "start_index": 0},
            ),
            0.9,
        )
    ]
    cf.filter_results(docs, corpus)
    cf.filter_results(docs, corpus)
    assert calls == ["ddos/udp.md"]
    cf.filter_results(docs, corpus, lm=StubLM())
    assert calls == ["ddos/udp.md", "ddos/udp.md"]


def test_fails_closed_without_a_language_model(corpus, monkeypatch):
    def missing():
        raise ef.DetectorUnavailable("no transformers")

    monkeypatch.setattr(cf, "language_model", missing)
    with pytest.raises(ef.DetectorUnavailable):
        cf.score_text(PWWS, "ddos/http_flood.md", ef.DomainReference(corpus))


def test_contextual_state_routes_to_the_contextual_filter_and_others_are_unchanged():
    assert ef.retrieval_for_state("contextual") is cf.contextual_retrieve
    assert ef.retrieval_for_state("defended") is ef.defended_retrieve
    assert ef.retrieval_for_state("repaired") is ef.repaired_retrieve
    assert (
        ef.retrieval_for_state("clean") is None
        and ef.retrieval_for_state("poisoned") is None
    )


def test_frozen_threshold_matches_recorded_development_choice():
    record = json.loads(
        (
            ROOT.parent / "docs/research/results/entropy-family/family-poisoned.json"
        ).read_text()
    )
    assert (
        record["results"]["development"][cf.SCORE_NAME]["threshold_fpr10"]
        == cf.THRESHOLD_BITS
    )
    assert record["parameters"]["lm"] == cf.LM_NAME
    assert record["parameters"]["candidate_words"] == cf.CANDIDATE_WORDS
    assert record["parameters"]["candidate_synonyms"] == cf.CANDIDATE_SYNONYMS
