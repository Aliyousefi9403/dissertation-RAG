import pytest
from app.defence import ctl

# 0 -> 1 -> 2 (loops), 0 -> 3 (loops). Labels: p at 1, q at 2, r at 3.
EDGES = {0: [1, 3], 1: [2], 2: [2], 3: [3]}
LABELS = {
    "p": lambda s: s == 1,
    "q": lambda s: s == 2,
    "r": lambda s: s == 3,
    "start": lambda s: s == 0,
}


def model():
    return ctl.Model([0], lambda s: EDGES[s], LABELS)


def atom(name):
    return ("atom", name)


def test_exploration_and_basic_temporal_operators():
    m = model()
    assert len(m.states) == 4
    assert m.holds(("EX", atom("p")))
    assert not m.holds(("AX", atom("p")))
    assert m.holds(("EF", atom("q")))
    assert not m.holds(("AF", atom("q")))  # the branch to 3 never reaches q
    assert m.holds(("AF", ("or", atom("q"), atom("r"))))
    assert m.holds(("AG", ("implies", atom("p"), ("AX", atom("q")))))
    assert m.holds(("EG", ("not", atom("q"))))
    assert not m.holds(("AG", ("not", atom("q"))))


def test_until():
    m = model()
    assert m.holds(("EU", ("or", atom("start"), atom("p")), atom("q")))
    assert not m.holds(("AU", ("or", atom("start"), atom("p")), atom("q")))
    assert m.holds(("AU", atom("start"), ("or", atom("p"), atom("r"))))


def test_counterexample_is_a_shortest_path_to_the_violation():
    m = model()
    assert m.counterexample(("AG", ("not", atom("q")))) == [0, 1, 2]
    path = m.counterexample(("AG", ("implies", atom("p"), ("AG", atom("p")))))
    assert path == [0, 1, 2]
    assert m.path_to(m.check(atom("r"))) == [0, 3]


def test_a_state_without_successor_is_rejected():
    with pytest.raises(ValueError):
        ctl.Model([0], lambda s: [] if s else [1], {})


def test_smv_export_lists_every_state_and_label():
    m = model()
    text = m.to_smv({"P": ctl.smv(("AG", ("implies", atom("p"), ("AX", atom("q")))))})
    assert "s : {s0, s1, s2, s3};" in text
    assert f"q := s in {{s{m.index[2]}}};" in text  # names follow discovery order
    assert "CTLSPEC AG ((p -> AX (q)))" in text
    assert ctl.smv(("EU", atom("p"), atom("q"))) == "E [ p U q ]"
