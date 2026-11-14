"""Monitors generated from linear temporal logic formulas by formula progression.

A formula is parsed once. Each event (a set of atomic propositions that hold now) rewrites the
formula into what must hold for the rest of the trace. If it rewrites to false, the trace so far
cannot be extended to satisfy the formula (a violation); if it rewrites to true, it can no longer
be violated. Otherwise the verdict is still open.

Syntax: atoms (letters, digits, underscore), true, false, ! & | ->, the unary operators G (always),
F (eventually), X (next) and the binary U (until), and parentheses.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

TRUE, FALSE = ("true",), ("false",)
_TOKENS = re.compile(r"\s*(->|[()!&|]|[A-Za-z_][A-Za-z0-9_{}]*)")
PLACEHOLDER = "{p}"


def parse(text: str) -> tuple:
    tokens, pos = [], 0
    while pos < len(text):
        match = _TOKENS.match(text, pos)
        if not match:
            if text[pos:].strip():
                raise ValueError(f"cannot read formula at: {text[pos:]!r}")
            break
        tokens.append(match.group(1))
        pos = match.end()
    tokens.reverse()

    def peek():
        return tokens[-1] if tokens else None

    def implies():
        left = disjunction()
        if peek() == "->":
            tokens.pop()
            return _or(_not(left), implies())
        return left

    def disjunction():
        left = conjunction()
        while peek() == "|":
            tokens.pop()
            left = _or(left, conjunction())
        return left

    def conjunction():
        left = until()
        while peek() == "&":
            tokens.pop()
            left = _and(left, until())
        return left

    def until():
        left = unary()
        if peek() == "U":
            tokens.pop()
            return ("U", left, until())
        return left

    def unary():
        token = tokens.pop() if tokens else None
        if token in ("!", "G", "F", "X"):
            inner = unary()
            return _not(inner) if token == "!" else (token, inner)
        if token == "(":
            inner = implies()
            if not tokens or tokens.pop() != ")":
                raise ValueError("missing )")
            return inner
        if token in ("true", "false"):
            return (token,)
        if token is None or not re.match(r"[A-Za-z_]", token) or token == "U":
            raise ValueError(f"unexpected {token!r}")
        return ("atom", token)

    formula = implies()
    if tokens:
        raise ValueError(f"unexpected {tokens[-1]!r}")
    return formula


def _not(f: tuple) -> tuple:
    if f == TRUE:
        return FALSE
    if f == FALSE:
        return TRUE
    return f[1] if f[0] == "!" else ("!", f)


def _and(a: tuple, b: tuple) -> tuple:
    if FALSE in (a, b):
        return FALSE
    if a == TRUE:
        return b
    if b == TRUE or a == b:
        return a
    return ("&", a, b)


def _or(a: tuple, b: tuple) -> tuple:
    if TRUE in (a, b):
        return TRUE
    if a == FALSE:
        return b
    if b == FALSE or a == b:
        return a
    return ("|", a, b)


def progress(f: tuple, event: frozenset[str] | set[str]) -> tuple:
    """The formula that the rest of the trace must satisfy after `event`."""
    op = f[0]
    if op in ("true", "false"):
        return f
    if op == "atom":
        return TRUE if f[1] in event else FALSE
    if op == "!":
        return _not(progress(f[1], event))
    if op == "&":
        return _and(progress(f[1], event), progress(f[2], event))
    if op == "|":
        return _or(progress(f[1], event), progress(f[2], event))
    if op == "X":
        return f[1]
    if op == "G":
        return _and(progress(f[1], event), f)
    if op == "F":
        return _or(progress(f[1], event), f)
    if op == "U":
        return _or(progress(f[2], event), _and(progress(f[1], event), f))
    raise ValueError(f"unknown operator {op}")


def substitute(f: tuple, value: str) -> tuple:
    if f[0] == "atom":
        return ("atom", f[1].replace(PLACEHOLDER, value))
    return (f[0], *(substitute(g, value) if isinstance(g, tuple) else g for g in f[1:]))


class Monitor:
    """One formula over one trace. `step` returns "violated", "satisfied" or "open".

    With reset=True a violation is reported once and the monitor re-arms, so each later event is
    judged afresh (the reaction to the violation is somebody else's job).
    """

    def __init__(self, formula: str | tuple, *, reset: bool = False):
        self.initial = parse(formula) if isinstance(formula, str) else formula
        self.state, self.reset = self.initial, reset

    def step(self, event: Iterable[str]) -> str:
        self.state = progress(self.state, frozenset(event))
        if self.state == FALSE:
            if self.reset:
                self.state = self.initial
            return "violated"
        return "satisfied" if self.state == TRUE else "open"


class ParametricMonitor:
    """A formula with the placeholder {p} in its atoms, monitored once per value of p.

    An event is a set of (atom_prefix, value) pairs written as atoms, e.g. "in_context_<key>".
    A value seen for the first time starts from the state the formula reaches on a trace in which
    none of its atoms has held so far, so it needs no stored history.
    """

    def __init__(self, formula: str):
        self.template = parse(formula)
        self.blank = self.template  # progressed through events where no {p} atom holds
        self.instances: dict[str, tuple] = {}
        self.prefixes = sorted(
            {a.split(PLACEHOLDER)[0] for a in _atoms(self.template)}, key=len
        )

    def _value(self, atom: str) -> str | None:
        for prefix in reversed(self.prefixes):
            if atom.startswith(prefix):
                return atom[len(prefix) :]
        return None

    def step(self, event: Iterable[str]) -> list[str]:
        """Advance every instance; return the values whose instance is violated by this event."""
        event = frozenset(event)
        for value in {v for v in map(self._value, event) if v is not None}:
            self.instances.setdefault(value, substitute(self.blank, value))
        violated = []
        for value, state in self.instances.items():
            self.instances[value] = progress(state, event)
            if self.instances[value] == FALSE:
                violated.append(value)
        self.blank = progress(self.blank, frozenset())
        return sorted(violated)


def _atoms(f: tuple) -> set[str]:
    if f[0] == "atom":
        return {f[1]}
    return set().union(*(_atoms(g) for g in f[1:] if isinstance(g, tuple)), set())


# The runtime monitor's three properties.
#   draft        a draft answer has just been generated
#   rare_copied  the draft contains a rare word, copied from the retrieved passages, that is
#                absent from the trusted MITRE vocabulary and from the question
#   refusal      the draft declines to answer
#   covered      the trusted MITRE data covers the attack asked about
#   quarantined_p / in_context_p   passage p has just been quarantined / is in the model's context
PHI1 = "G (draft -> !rare_copied)"
PHI2 = "G (draft -> !(refusal & covered))"
PHI3 = "G (quarantined_{p} -> G !in_context_{p})"
