"""Offline, read-only re-analysis of one saved pilot run.

Usage: python docs/research/scripts/reanalyse_pilot.py RUN_DIR EXPOSURE_REPORT.json [ROWS_OUT.json]

Per-question table, repetition determinism, the edited-text ASR variant and a
question-level (cluster) bootstrap. No model calls, no corpus reads and no
writes except the optional create-only rows file. Seed 20261016, B=10000.
"""

import collections
import json
import random
import statistics as st
import sys
from pathlib import Path

run = Path(sys.argv[1])
expo = json.load(open(sys.argv[2]))
obs = run / "observations"
m = json.load(open(run / "manifest.json"))
ex = {
    o["index"]: o["edited_text_exposure"]["edited_text_hit_at_3"]
    for r in expo["runs"]
    if r.get("run_id") == m["run_id"]
    for o in r["observations"]
}
rows = []
for u in m["schedule"]:
    i = u["index"]
    g = lambda c, s: json.load(open(obs / f"{i:06d}-{c}-{s}.json"))
    pair = json.load(open(obs / f"{i:06d}-pair.json"))
    r = {"i": i, "q": u["question_id"], "rep": u["repetition"]}
    for c in ("clean", "poisoned"):
        r[c + "_corr"] = g(c, "correctness")["capture"]["raw_score"]
        r[c + "_faith"] = g(c, "faithfulness")["capture"]["raw_score"]
        v = g(c, "retrieval")["value"]
        r[c + "_hit"] = v["hit_at_3"]
        r[c + "_rr"] = v["reciprocal_rank"]
        r[c + "_ans"] = g(c, "rag")["answer"]
        r[c + "_ids"] = [
            (
                s["metadata"].get("source", "").split("knowledge_base/")[-1],
                s["metadata"].get("start_index"),
            )
            for s in g(c, "rag")["capture"]["sources"]
        ]
    r["section_hit"] = pair["attack_inputs"]["poison_hit_at_3"]
    r["edited_hit"] = ex[i]
    r["asr"] = pair["attack_success"]["rag_attack_success"]
    r["drop"] = r["clean_corr"] - r["poisoned_corr"]
    r["asr_edited"] = r["edited_hit"] == 1 and r["drop"] >= 0.25
    r["jacc"] = pair["document_overlap"]["jaccard"]
    rows.append(r)

print(
    f"{'question':36} rep  cHit pHit secHit edHit  cCorr pCorr  cFai pFai  ASR ASRed jac"
)
for r in rows:
    print(
        f"{r['q']:36} {r['rep']}   {r['clean_hit']}    {r['poisoned_hit']}    {r['section_hit']}      {r['edited_hit']}     {r['clean_corr']:.2f}  {r['poisoned_corr']:.2f}   {r['clean_faith']:.2f} {r['poisoned_faith']:.2f}  {int(r['asr'])}   {int(r['asr_edited'])}    {r['jacc']}"
    )

# determinism across repetitions (temperature 0)
by_q = collections.defaultdict(list)
for r in rows:
    by_q[r["q"]].append(r)
same = {
    c: sum(len({x[c + "_ans"] for x in v}) == 1 for v in by_q.values())
    for c in ("clean", "poisoned")
}
same_ret = {
    c: sum(len({json.dumps(x[c + "_ids"]) for x in v}) == 1 for v in by_q.values())
    for c in ("clean", "poisoned")
}
score_var = {
    c: sum(
        len({(x[c + "_corr"], x[c + "_faith"]) for x in v}) > 1 for v in by_q.values()
    )
    for c in ("clean", "poisoned")
}
print(
    "\nquestions with identical answers across 3 reps:",
    same,
    "identical retrieval:",
    same_ret,
    "questions whose judge scores vary across reps:",
    score_var,
)


def mean(k, f=lambda r: True):
    v = [r[k] for r in rows if f(r)]
    return round(sum(v) / len(v), 4), len(v)


print(
    "ASR (section exposure):",
    mean("asr"),
    " ASR (edited-text exposure):",
    mean("asr_edited"),
)
print(
    "edited exposure rate:",
    mean("edited_hit"),
    " section exposure:",
    mean("section_hit"),
)
print(
    "mean correctness drop | edited_hit=1:",
    mean("drop", lambda r: r["edited_hit"] == 1),
    " | edited_hit=0:",
    mean("drop", lambda r: r["edited_hit"] == 0),
)
print(
    "mean correctness drop | poisoned_hit=0:",
    mean("drop", lambda r: r["poisoned_hit"] == 0),
    " | poisoned_hit=1:",
    mean("drop", lambda r: r["poisoned_hit"] == 1),
)

# question-level (cluster) analysis: average reps per question, then bootstrap over questions
q = {
    k: {
        m: st.mean(x[m] for x in v)
        for m in (
            "clean_corr",
            "poisoned_corr",
            "clean_faith",
            "poisoned_faith",
            "clean_hit",
            "poisoned_hit",
            "edited_hit",
            "asr",
            "asr_edited",
        )
    }
    for k, v in by_q.items()
}
random.seed(20261016)


def boot(fn, B=10000):
    keys = list(q)
    vals = []
    for _ in range(B):
        s = [q[random.choice(keys)] for _ in keys]
        vals.append(fn(s))
    vals.sort()
    return round(vals[int(0.025 * B)], 4), round(vals[int(0.975 * B)], 4)


for name, fn in {
    "correctness delta": lambda s: st.mean(
        x["poisoned_corr"] - x["clean_corr"] for x in s
    ),
    "faithfulness delta": lambda s: st.mean(
        x["poisoned_faith"] - x["clean_faith"] for x in s
    ),
    "Hit@3 delta": lambda s: st.mean(x["poisoned_hit"] - x["clean_hit"] for x in s),
    "ASR (section)": lambda s: st.mean(x["asr"] for x in s),
    "ASR (edited)": lambda s: st.mean(x["asr_edited"] for x in s),
}.items():
    point = fn(list(q.values()))
    print(
        f"{name:20} point={point:.4f}  95% cluster-bootstrap CI over 12 questions={boot(fn)}"
    )
d = [v["poisoned_corr"] - v["clean_corr"] for v in q.values()]
print(
    "per-question correctness deltas:",
    [round(x, 3) for x in d],
    " negative:",
    sum(x < 0 for x in d),
    "zero:",
    sum(x == 0 for x in d),
    "positive:",
    sum(x > 0 for x in d),
)
if len(sys.argv) > 3:
    json.dump(rows, open(sys.argv[3], "x"), indent=1, default=str)  # create-only
