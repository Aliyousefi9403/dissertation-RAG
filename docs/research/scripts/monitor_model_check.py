"""CTL design check of the runtime monitor's control loop (Asad's suggestion: CTL alongside LTL).

The monitor's control logic (app.defence.runtime_monitor.monitored_answer) is abstracted into a
finite transition system and model-checked with app.defence.ctl. The language model, the checks
and the blame step are replaced by nondeterministic choices, so every behaviour they could produce
is covered: whether a draft violates phi1 and/or phi2, whether the blame step quarantines anything,
and whether a tracked passage p is retrieved and is among the passages quarantined. Questions
repeat forever and the quarantine memory persists between them. The mode (verify or restore) is
fixed per deployment; whether MITRE covers the attack asked about is chosen per question.

Two designs are checked:
  as_run  the code used for every recorded run (policies v1-v3): after the last round, restore
          regenerates from the passages retrieved for that round, and releases the result as
          "restored" without acting on its re-check;
  strict  restore drops passages quarantined in that round from its context, and withholds the
          restored answer if it violates phi1 (the same rule as for drafts).

Properties (CTL; atoms are explained in LABELS):
  P1 phi3    AG (quarantined -> AG !in_context)       a quarantined passage never re-enters a context
  P2         AG (quarantined -> AG quarantined)        the memory never forgets
  P3         AG AF done                                every question is answered or withheld
  P4         AG (generations <= MAX_ROUNDS + 2)       bounded cost per question
  P5 phi1    AG ((done & !withheld) -> !rare_copied)   no released answer violates phi1
  P6         AG ((new_question & covered) -> AF (done & answered))
             every covered question gets a non-refusing answer (availability)
  E1         EF (done & restored & refusal)            a restored answer can still refuse

For each property and design: holds or not, and a shortest counterexample for AG properties.
Also writes each explored model in NuSMV syntax (explicit states, the same CTLSPECs) so the
verdicts can be reproduced with NuSMV.

Usage: python docs/research/scripts/monitor_model_check.py OUT_DIR
"""

import json
import sys
from itertools import product
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))
from app.defence import ctl
from app.defence.runtime_monitor import MAX_ROUNDS


class S(NamedTuple):
    mode: str  # verify | restore (fixed)
    phase: str  # new | drafted | blamed | final | restored | done
    covered: int  # MITRE covers the attack asked about
    round: int
    generations: int
    quarantined: int  # the tracked passage p is in the quarantine memory
    in_context: int  # p is in the context of the generation made in this step
    rare_copied: int  # the last check found a phi1 violation
    refusal: int  # the last generation declines (a phi2 violation when covered)
    outcome: str  # - | released | released_refusal | restored | withheld


def checks(covered):
    """(rare_copied, refusal) outcomes of a check; a refusal is a violation only when covered."""
    return list(product((0, 1), (0, 1)))


def successors(design):
    def step(s):
        if s.phase == "new":  # retrieve (quarantined passages skipped), draft, check
            for ctx in (0,) if s.quarantined else (0, 1):
                for rare, refusal in checks(s.covered):
                    yield s._replace(
                        phase="drafted",
                        generations=s.generations + 1,
                        in_context=ctx,
                        rare_copied=rare,
                        refusal=refusal,
                    )
        elif s.phase == "drafted":
            violated = s.rare_copied or (s.refusal and s.covered)
            if not violated:
                yield s._replace(phase="done", in_context=0, outcome="released")
                return
            # blame: something new is quarantined or not; p can be blamed only if it was in context
            options = [(0, s.quarantined)] + [(1, s.quarantined)]
            if s.in_context:
                options.append((1, 1))
            for added, q in options:
                last = (not added) or s.round == MAX_ROUNDS
                yield s._replace(
                    phase="final" if last else "blamed",
                    quarantined=q,
                    in_context=0,
                    # remember whether p sat in the last round's context (restore reuses it)
                    outcome="ctx" if s.in_context else "-",
                )
        elif s.phase == "blamed":  # feedback, next round
            yield s._replace(phase="new", round=s.round + 1, outcome="-")
        elif s.phase == "final":
            last_ctx = s.outcome == "ctx"
            if s.mode == "restore" and s.covered and not s.rare_copied:
                ctx = int(last_ctx and not (design == "strict" and s.quarantined))
                for rare, refusal in checks(s.covered):
                    outcome = "withheld" if design == "strict" and rare else "restored"
                    yield s._replace(
                        phase="restored",
                        generations=s.generations + 1,
                        in_context=ctx,
                        rare_copied=rare,
                        refusal=refusal,
                        outcome=outcome,
                    )
            elif s.rare_copied:
                yield s._replace(phase="done", outcome="withheld")
            else:
                yield s._replace(phase="done", outcome="released_refusal")
        elif s.phase == "restored":
            yield s._replace(phase="done", in_context=0)
        elif s.phase == "done":  # the next question; the memory persists
            for covered in (0, 1):
                yield S(s.mode, "new", covered, 0, 0, s.quarantined, 0, 0, 0, "-")

    return step


LABELS = {
    "new_question": lambda s: s.phase == "new" and s.round == 0,
    "covered": lambda s: bool(s.covered),
    "done": lambda s: s.phase == "done",
    "quarantined": lambda s: bool(s.quarantined),
    "in_context": lambda s: bool(s.in_context),
    "rare_copied": lambda s: bool(s.rare_copied),
    "refusal": lambda s: bool(s.refusal),
    "withheld": lambda s: s.outcome == "withheld",
    "restored": lambda s: s.outcome == "restored",
    "answered": lambda s: s.outcome in ("released", "restored") and not s.refusal,
    "generations_bounded": lambda s: s.generations <= MAX_ROUNDS + 2,
}


def a(name):
    return ("atom", name)


PROPERTIES = {
    "P1_phi3_quarantined_never_in_context": (
        "AG",
        ("implies", a("quarantined"), ("AG", ("not", a("in_context")))),
    ),
    "P2_memory_is_permanent": (
        "AG",
        ("implies", a("quarantined"), ("AG", a("quarantined"))),
    ),
    "P3_every_question_ends": ("AG", ("AF", a("done"))),
    "P4_bounded_generations": ("AG", a("generations_bounded")),
    "P5_phi1_no_released_answer_copies_rare_words": (
        "AG",
        (
            "implies",
            ("and", a("done"), ("not", a("withheld"))),
            ("not", a("rare_copied")),
        ),
    ),
    "P6_availability_covered_questions_get_an_answer": (
        "AG",
        (
            "implies",
            ("and", a("new_question"), a("covered")),
            ("AF", ("and", a("done"), a("answered"))),
        ),
    ),
    "E1_a_restored_answer_can_still_refuse": (
        "EF",
        ("and", a("done"), ("and", a("restored"), a("refusal"))),
    ),
}


def initial(modes):
    return [S(m, "new", c, 0, 0, 0, 0, 0, 0, "-") for m in modes for c in (0, 1)]


def describe(path):
    keep = (
        "phase",
        "covered",
        "round",
        "quarantined",
        "in_context",
        "rare_copied",
        "refusal",
        "outcome",
    )
    return [{k: getattr(s, k) for k in ("mode",) + keep} for s in path]


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)  # create-only
    summary = {"max_rounds": MAX_ROUNDS, "designs": {}}
    for design in ("as_run", "strict"):
        summary["designs"][design] = {}
        for mode in ("verify", "restore"):
            model = ctl.Model(initial([mode]), successors(design), LABELS)
            verdicts = {}
            for name, f in PROPERTIES.items():
                held = model.holds(f)
                entry = {"ctl": ctl.smv(f), "holds": held}
                if not held:
                    cex = model.counterexample(f)
                    if cex:
                        entry["counterexample"] = describe(cex)
                verdicts[name] = entry
            summary["designs"][design][mode] = {
                "states": len(model.states),
                "transitions": sum(len(x) for x in model.succ),
                "properties": verdicts,
            }
            (out / f"monitor-{design}-{mode}.smv").write_text(
                model.to_smv({n: ctl.smv(f) for n, f in PROPERTIES.items()})
            )
            print(
                f"{design:7s} {mode:8s} states={len(model.states):4d}  "
                + "  ".join(
                    f"{n.split('_')[0]}={'ok' if v['holds'] else 'FAIL'}"
                    for n, v in verdicts.items()
                )
            )
    with open(out / "summary.json", "x", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
