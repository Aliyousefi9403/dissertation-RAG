import pytest
from app.defence import ltl_monitor as ltl


def run(formula, trace, **kwargs):
    monitor = ltl.Monitor(formula, **kwargs)
    return [monitor.step(event) for event in trace]


def test_always_is_violated_at_the_first_bad_event_and_stays_violated():
    assert run("G !bad", [set(), {"ok"}, {"bad"}, set()]) == [
        "open",
        "open",
        "violated",
        "violated",
    ]


def test_eventually_and_until_are_satisfied_when_the_goal_arrives():
    assert run("F done", [set(), {"done"}, set()]) == ["open", "satisfied", "satisfied"]
    assert run("a U b", [{"a"}, {"a"}, {"b"}]) == ["open", "open", "satisfied"]
    assert run("a U b", [{"a"}, set()]) == ["open", "violated"]


def test_next_looks_one_event_ahead():
    assert run("X a", [set(), {"a"}]) == ["open", "satisfied"]
    assert run("X a", [{"a"}, set()]) == ["open", "violated"]


def test_implication_and_precedence():
    assert ltl.parse("a -> b | c & d") == ltl.parse("(!a) | (b | (c & d))")
    assert ltl.parse("!a & b") == ltl.parse("(!a) & b")
    with pytest.raises(ValueError):
        ltl.parse("G (a ->")
    with pytest.raises(ValueError):
        ltl.parse("a b")


def test_phi1_and_phi2_judge_each_draft_and_rearm_after_a_violation():
    trace = [
        {"draft"},
        {"draft", "rare_copied"},
        {"draft"},
        {"draft", "refusal"},
        {"draft", "refusal", "covered"},
    ]
    assert run(ltl.PHI1, trace, reset=True) == [
        "open",
        "violated",
        "open",
        "open",
        "open",
    ]
    assert run(ltl.PHI2, trace, reset=True) == [
        "open",
        "open",
        "open",
        "open",
        "violated",
    ]


def test_phi3_flags_a_quarantined_passage_that_returns_to_the_context():
    monitor = ltl.ParametricMonitor(ltl.PHI3)
    assert monitor.step({"in_context_a", "in_context_b"}) == []
    assert monitor.step({"quarantined_a"}) == []
    assert monitor.step({"in_context_b", "in_context_c"}) == []
    assert monitor.step({"in_context_a", "in_context_c"}) == ["a"]
    assert monitor.step({"quarantined_c"}) == ["a"]  # a violation is permanent
    assert monitor.step({"in_context_b"}) == ["a"]


def test_a_passage_first_seen_late_is_not_blamed_for_the_past():
    monitor = ltl.ParametricMonitor(ltl.PHI3)
    for _ in range(5):
        assert monitor.step({"in_context_x"}) == []
    assert monitor.step({"in_context_new"}) == []
    assert monitor.step({"quarantined_new"}) == []
    assert monitor.step({"in_context_new"}) == ["new"]


def test_parametric_instances_start_from_the_blank_history():
    # "p must be seen in the context at the very first event" cannot hold for a late value.
    monitor = ltl.ParametricMonitor("in_context_{p}")
    assert monitor.step({"in_context_a"}) == []
    assert monitor.step({"in_context_b"}) == ["b"]
