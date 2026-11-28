"""A small explicit-state CTL model checker.

A model is a finite transition system: initial states, a successor function and labelling
predicates. `Model.explore` enumerates the reachable states; `Model.check` returns the set of
states that satisfy a CTL formula, computed with the standard fixpoints (EX, EU, and EG as a
greatest fixpoint), so every state must have a successor (add self-loops to final states).

Formulas are tuples: ("atom", name), ("not", f), ("and", f, g), ("or", f, g), ("implies", f, g),
("EX"|"AX"|"EF"|"AF"|"EG"|"AG", f), ("EU"|"AU", f, g). Atoms name labelling predicates.
`to_smv` writes the explored model as an explicit-state NuSMV module so that the same verdicts can
be reproduced with NuSMV.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable, Iterable


class Model:
    def __init__(
        self,
        initial: Iterable[Hashable],
        successors: Callable[[Hashable], Iterable[Hashable]],
        labels: dict[str, Callable[[Hashable], bool]],
    ):
        self.labels = labels
        self.states: list[Hashable] = []
        self.index: dict[Hashable, int] = {}
        self.succ: list[list[int]] = []
        queue = deque()
        for s in initial:
            if s not in self.index:
                self.index[s] = len(self.states)
                self.states.append(s)
                queue.append(s)
        self.initial = set(range(len(self.states)))
        edges = {}
        while queue:
            s = queue.popleft()
            nxt = []
            for t in successors(s):
                if t not in self.index:
                    self.index[t] = len(self.states)
                    self.states.append(t)
                    queue.append(t)
                nxt.append(self.index[t])
            if not nxt:
                raise ValueError(f"state without a successor: {s}")
            edges[self.index[s]] = sorted(set(nxt))
        self.succ = [edges[i] for i in range(len(self.states))]
        self.pred: list[list[int]] = [[] for _ in self.states]
        for i, out in enumerate(self.succ):
            for j in out:
                self.pred[j].append(i)

    # ---- CTL ----
    def check(self, f: tuple) -> set[int]:
        op = f[0]
        all_states = set(range(len(self.states)))
        if op == "atom":
            label = self.labels[f[1]]
            return {i for i, s in enumerate(self.states) if label(s)}
        if op == "true":
            return all_states
        if op == "not":
            return all_states - self.check(f[1])
        if op == "and":
            return self.check(f[1]) & self.check(f[2])
        if op == "or":
            return self.check(f[1]) | self.check(f[2])
        if op == "implies":
            return (all_states - self.check(f[1])) | self.check(f[2])
        if op == "EX":
            target = self.check(f[1])
            return {i for i in all_states if any(j in target for j in self.succ[i])}
        if op == "AX":
            return self.check(("not", ("EX", ("not", f[1]))))
        if op == "EF":
            return self.check(("EU", ("true",), f[1]))
        if op == "AG":
            return self.check(("not", ("EF", ("not", f[1]))))
        if op == "AF":
            return self.check(("not", ("EG", ("not", f[1]))))
        if op == "EU":
            hold, goal = self.check(f[1]), self.check(f[2])
            result, queue = set(goal), deque(goal)
            while queue:
                j = queue.popleft()
                for i in self.pred[j]:
                    if i not in result and i in hold:
                        result.add(i)
                        queue.append(i)
            return result
        if op == "AU":
            # A[f U g] = not (E[not g U (not f and not g)] or EG not g)
            nf, ng = ("not", f[1]), ("not", f[2])
            return self.check(("not", ("or", ("EU", ng, ("and", nf, ng)), ("EG", ng))))
        if op == "EG":
            result = self.check(f[1])
            changed = True
            while changed:
                keep = {i for i in result if any(j in result for j in self.succ[i])}
                changed = keep != result
                result = keep
            return result
        raise ValueError(f"unknown operator {op}")

    def holds(self, f: tuple) -> bool:
        return self.initial <= self.check(f)

    def path_to(self, targets: set[int], start: set[int] | None = None) -> list | None:
        """Shortest path from `start` (default: the initial states) to a state in `targets`."""
        start = self.initial if start is None else start
        parent = {i: None for i in start}
        queue = deque(start)
        while queue:
            i = queue.popleft()
            if i in targets:
                path = []
                while i is not None:
                    path.append(self.states[i])
                    i = parent[i]
                return path[::-1]
            for j in self.succ[i]:
                if j not in parent:
                    parent[j] = i
                    queue.append(j)
        return None

    def counterexample(self, f: tuple) -> list | None:
        """For AG g: a shortest path to a state violating g (extended for g = a -> AG b)."""
        if f[0] != "AG":
            return None
        body = f[1]
        bad = set(range(len(self.states))) - self.check(body)
        path = self.path_to(bad)
        if path and body[0] == "implies" and body[2][0] == "AG":
            tail = self.path_to(
                set(range(len(self.states))) - self.check(body[2][1]),
                {self.index[path[-1]]},
            )
            if tail:
                path = path + tail[1:]
        return path

    # ---- NuSMV export ----
    def to_smv(self, specs: dict[str, str]) -> str:
        names = [f"s{i}" for i in range(len(self.states))]
        lines = ["MODULE main", "VAR", f"  s : {{{', '.join(names)}}};", "ASSIGN"]
        lines.append(
            f"  init(s) := {{{', '.join(names[i] for i in sorted(self.initial))}}};"
        )
        lines.append("  next(s) := case")
        for i, out in enumerate(self.succ):
            lines.append(
                f"    s = {names[i]} : {{{', '.join(names[j] for j in out)}}};"
            )
        lines.append("  esac;")
        lines.append("DEFINE")
        for label, predicate in self.labels.items():
            members = [names[i] for i, st in enumerate(self.states) if predicate(st)]
            lines.append(
                f"  {label} := "
                + (f"s in {{{', '.join(members)}}}" if members else "FALSE")
                + ";"
            )
        for name, text in specs.items():
            lines.append(f"-- {name}")
            lines.append(f"CTLSPEC {text}")
        return "\n".join(lines) + "\n"


def smv(f: tuple) -> str:
    """A formula in NuSMV CTL syntax."""
    op = f[0]
    if op == "atom":
        return f[1]
    if op == "true":
        return "TRUE"
    if op == "not":
        return f"!({smv(f[1])})"
    if op in ("and", "or", "implies"):
        sym = {"and": "&", "or": "|", "implies": "->"}[op]
        return f"({smv(f[1])} {sym} {smv(f[2])})"
    if op in ("EU", "AU"):
        return f"{op[0]} [ {smv(f[1])} U {smv(f[2])} ]"
    return f"{op} ({smv(f[1])})"
