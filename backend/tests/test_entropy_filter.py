"""Tests for the relative-entropy / synonym-gap retrieval filter (entropy-filter-v1)."""

import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

from app.defence import entropy_filter as ef

pytest.importorskip("wordfreq")
try:
    ef._wordnet()
except ef.DetectorUnavailable:  # pragma: no cover - environment without WordNet data
    pytest.skip("WordNet data not installed", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
CLEAN = "An adversary may deny legitimate users access to a server by flooding the web application with requests."
PWWS = "An adversary may abnegate legitimate users access to a waiter by flooding the entanglement coating with requests."


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "ddos").mkdir()
    (tmp_path / "ddos/http_flood.md").write_text(CLEAN, encoding="utf-8")
    for name in ("udp", "icmp", "tcp"):
        (tmp_path / f"ddos/{name}.md").write_text(
            f"An adversary floods the server with {name} traffic to deny service to legitimate users "
            "of the web application and its server.", encoding="utf-8")
    ef.reference_for.cache_clear()
    return tmp_path


def test_substituted_text_scores_higher_than_original(corpus):
    reference = ef.DomainReference(corpus)
    original = ef.score_text(CLEAN, "ddos/http_flood.md", reference)
    poisoned = ef.score_text(PWWS, "ddos/http_flood.md", reference)
    assert poisoned["score_bits"] > original["score_bits"]
    assert poisoned["flagged"] and not original["flagged"]
    recovered = {w["word"]: w["likely_original"] for w in poisoned["top_words"]}
    assert recovered.get("waiter") == "server" or recovered.get("abnegate") == "deny"


def test_reference_is_leave_one_document_out(corpus):
    reference = ef.DomainReference(corpus)
    # "flooding" only occurs in http_flood.md, so it gets no domain mass when scoring that document.
    with_self = reference.probability("flooding", "ddos/udp.md")
    without_self = reference.probability("flooding", "ddos/http_flood.md")
    assert with_self > without_self


def test_filter_drops_flagged_and_backfills(corpus):
    docs = [(Document(page_content=PWWS, metadata={"source": str(corpus / "ddos/http_flood.md"), "start_index": 0}), 0.9)]
    docs += [(Document(page_content=CLEAN, metadata={"source": str(corpus / f"ddos/{n}.md"), "start_index": i}), 0.8 - i / 10)
             for i, n in enumerate(("udp", "icmp", "tcp", "udp"))]
    kept, decisions = ef.filter_results(docs, corpus)
    assert len(kept) == 3
    assert all(not d.metadata["entropy_filter"]["flagged"] for d, _ in kept)
    assert decisions[0]["flagged"] and not decisions[0]["kept"]
    assert [d["kept"] for d in decisions] == [False, True, True, True, False]
    assert kept[0][0].metadata["entropy_filter"]["candidate_rank"] == 2


def test_fails_closed_without_wordnet(monkeypatch, corpus):
    def missing():
        raise ef.DetectorUnavailable("no wordnet")

    monkeypatch.setattr(ef, "_wordnet", missing)
    ef.synonyms.cache_clear()
    with pytest.raises(ef.DetectorUnavailable):
        ef.score_text(PWWS, "ddos/http_flood.md", ef.DomainReference(corpus))
    ef.synonyms.cache_clear()


def test_only_defended_state_is_filtered():
    assert ef.retrieval_for_state("clean") is None
    assert ef.retrieval_for_state("poisoned") is None
    assert ef.retrieval_for_state("defended") is ef.defended_retrieve


def test_frozen_threshold_matches_recorded_development_choice():
    record = json.loads((ROOT.parent / "docs/research/results/entropy-detector-20261016/detector-poisoned.json").read_text())
    assert record["results"]["development"][ef.SCORE_NAME]["threshold_fpr10"] == ef.THRESHOLD_BITS


def test_reproduces_recorded_detector_scores():
    from langchain_community.document_loaders import DirectoryLoader, TextLoader

    from app.config import get_knowledge_base_path
    from app.ingestion.load_documents import add_document_metadata, split_documents

    root = get_knowledge_base_path("poisoned")
    loader = DirectoryLoader(str(root), glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    chunks = {(Path(c.metadata["source"]).relative_to(root).as_posix(), c.metadata["start_index"]): c.page_content
              for c in split_documents(add_document_metadata(loader.load(), "poisoned"))}
    rows = json.loads((ROOT.parent / "docs/research/results/entropy-detector-20261016/detector-poisoned.json").read_text())["rows"]
    ef.reference_for.cache_clear()
    reference = ef.reference_for(str(root))
    for row in rows[::10]:
        score = ef.score_text(chunks[(row["document"], row["start"])], row["document"], reference)["score_bits"]
        assert score == pytest.approx(row["syngap_top3_domain"], abs=1e-3)
