# CTL design check of the runtime monitor

`monitor_model_check.py` abstracts the monitor's control loop (`monitored_answer`) into a finite
transition system: the language model, the φ1/φ2 checks and the blame step become nondeterministic
choices, questions repeat forever and the quarantine memory persists. Seven CTL properties are
checked with the explicit-state checker in `backend/app/defence/ctl.py` (tests:
`backend/tests/test_ctl.py`), for two designs and both modes.

| Property | as run, verify | as run, restore | strict, verify | strict, restore |
|---|---|---|---|---|
| P1 φ3: AG (quarantined → AG ¬inContext) | holds | **fails** | holds | holds |
| P2 AG (quarantined → AG quarantined) | holds | holds | holds | holds |
| P3 AG AF done | holds | holds | holds | holds |
| P4 at most MAX_ROUNDS + 2 generations | holds | holds | holds | holds |
| P5 φ1: no released answer copies rare words | holds | **fails** | holds | holds |
| P6 availability: AG (covered → AF answered) | fails | fails | fails | fails |
| E1 EF (restored ∧ refusal) | false | true | false | true |

- **as run** is the code behind every recorded run (policies v1 to v3). In restore mode the fallback
  is generated from the last round's passages (P1 fails: a passage quarantined in that round is in
  its context) and released whatever its re-check says (P5 fails).
- **strict** (`strict_restore=True`) drops passages quarantined in that round and withholds a
  fallback answer that violates φ1.
- Both failures occur in the recorded runs: P1 in 2 / 2 / 1 restore fallbacks of the v1 / v2 / v3
  runs (`runtime-monitor/*-phi3-corrected/`, `runtime-monitor/ltl-replay-v2/`), P5 once in the v1 run.
- P6 failing is expected: the monitor can withhold or refuse, but it cannot guarantee an answer.

`summary.json` holds the verdicts and shortest counterexamples. `monitor-*.smv` are the same models
in explicit-state NuSMV syntax with the same `CTLSPEC`s, so the verdicts can be reproduced with
NuSMV (`NuSMV monitor-as_run-restore.smv`). NuSMV itself was not run here.
