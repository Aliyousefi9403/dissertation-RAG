"""Tests for the adaptive (detector-aware) PWWS attack (app/attack/pwws_adaptive_kb.py)."""

import hashlib
from pathlib import Path

import pytest

pytest.importorskip("textattack", exc_type=ImportError)  # also skips when textattack cannot load with the installed transformers
from textattack.shared import AttackedText  # noqa: E402

from app.attack import pwws_adaptive_kb as adaptive  # noqa: E402
from app.defence import entropy_filter as ef  # noqa: E402

try:
    ef._wordnet()
except ef.DetectorUnavailable:  # pragma: no cover
    pytest.skip("WordNet data not installed", allow_module_level=True)


@pytest.fixture
def reference(tmp_path):
    (tmp_path / "ddos").mkdir()
    for name in ("udp", "icmp", "tcp"):
        (tmp_path / f"ddos/{name}.md").write_text(
            f"An adversary floods the server with {name} traffic to deny service to users of the server.", encoding="utf-8")
    (tmp_path / "ddos/http_flood.md").write_text("An adversary may deny users access to a server.", encoding="utf-8")
    return ef.DomainReference(tmp_path)


def swap(text, index, word):
    original = AttackedText(text)
    transformed = original.replace_word_at_index(index, word)
    transformed.attack_attrs["newly_modified_indices"] = {index}
    return original, transformed


def test_constraint_rejects_a_swap_to_a_rarer_word(reference):
    constraint = adaptive.domain_frequency_constraint(reference)
    constraint.document = "ddos/http_flood.md"
    original, transformed = swap("An adversary may deny users access to a server", 8, "waiter")
    assert reference.probability("waiter", constraint.document) < reference.probability("server", constraint.document)
    assert not constraint._check_constraint(transformed, original)


def test_constraint_allows_a_swap_to_an_equally_or_more_common_word(reference):
    constraint = adaptive.domain_frequency_constraint(reference)
    constraint.document = "ddos/http_flood.md"
    original, transformed = swap("An adversary may abnegate users access to a server", 3, "deny")
    assert constraint._check_constraint(transformed, original)
    untouched = AttackedText("An adversary may deny users access to a server")
    assert constraint._check_constraint(untouched, untouched)


class StubLM:
    def __init__(self, scores):
        self.scores = scores

    def log2_prob(self, texts):
        return [self.scores.get(t, -100.0) for t in texts]


def test_second_order_constraint_also_requires_the_language_model_not_to_object(reference):
    original, transformed = swap("An adversary may abnegate users access to a server", 3, "deny")
    allowed = adaptive.domain_frequency_constraint(reference, StubLM({original.text: -50.0, transformed.text: -40.0}))
    allowed.document = "ddos/http_flood.md"
    assert allowed._check_constraint(transformed, original)
    vetoed = adaptive.domain_frequency_constraint(reference, StubLM({original.text: -50.0, transformed.text: -60.0}))
    vetoed.document = "ddos/http_flood.md"
    assert not vetoed._check_constraint(transformed, original)


def test_constraint_compares_against_the_original_text(reference):
    assert adaptive.domain_frequency_constraint(reference).compare_against_original


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode() + p.read_bytes())
    return h.hexdigest()


def test_outputs_are_create_only_and_never_touch_existing_corpora(tmp_path, monkeypatch):
    clean = tmp_path / "clean"
    (clean / "ddos").mkdir(parents=True)
    (clean / "ddos/http_flood.md").write_text("text", encoding="utf-8")
    monkeypatch.setattr(adaptive, "CLEAN_KB", clean)
    before = digest(clean)
    kb, manifest = adaptive.prepare_output(tmp_path / "adaptive")
    assert (kb / "ddos/http_flood.md").read_text() == "text"
    assert not manifest.exists()
    with pytest.raises(FileExistsError):
        adaptive.prepare_output(tmp_path / "adaptive")
    assert digest(clean) == before


def test_variants_write_only_to_new_folders():
    assert {p.name for p in adaptive.VARIANTS.values()} == {"poisoned_adaptive", "poisoned_pwws_rerun", "poisoned_adaptive_lm", "poisoned_textfooler"}
    assert all(p.name != "poisoned" for p in adaptive.VARIANTS.values())


def test_batched_check_matches_the_one_at_a_time_rule(reference):
    base = AttackedText("An adversary may abnegate users access to a server")
    candidates = [base.replace_word_at_index(3, w) for w in ("deny", "refuse", "waiter")]
    for t in candidates:
        t.attack_attrs["newly_modified_indices"] = {3}
    lm = StubLM({base.text: -50.0, candidates[0].text: -40.0, candidates[1].text: -55.0, candidates[2].text: -10.0})
    constraint = adaptive.domain_frequency_constraint(reference, lm)
    constraint.document = "ddos/http_flood.md"
    one_by_one = [t for t in candidates if constraint._check_constraint(t, base)]
    assert constraint._check_constraint_many(candidates, base) == one_by_one


def test_resume_keeps_finished_parts_and_refuses_after_the_manifest(tmp_path, monkeypatch):
    clean = tmp_path / "clean"
    (clean / "ddos").mkdir(parents=True)
    (clean / "ddos/http_flood.md").write_text("text", encoding="utf-8")
    monkeypatch.setattr(adaptive, "CLEAN_KB", clean)
    out = tmp_path / "adaptive"
    kb, manifest = adaptive.prepare_output(out)
    part = adaptive.part_path(out, "ddos/http_flood.md")
    adaptive.write_part(part, [{"file": "ddos/http_flood.md", "success": False}])
    with pytest.raises(FileExistsError):
        adaptive.prepare_output(out)
    adaptive.prepare_output(out, resume=True)
    assert part.exists() and not part.with_suffix(".tmp").exists()
    manifest.write_text("", encoding="utf-8")
    with pytest.raises(FileExistsError):
        adaptive.prepare_output(out, resume=True)
