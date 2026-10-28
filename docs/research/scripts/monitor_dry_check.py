"""Offline dry check of the runtime monitor's specifications on recorded answers (no model calls).

Applies phi1 (lexical conformance) and phi2 (evidence availability) of runtime-monitor-v1 to every
answer of the main run (clean and PWWS-poisoned, 132 each) and reports how often each property is
violated per condition and per outcome (correct / partial / incorrect / refusal, labels as in
analyse_defence.py), plus the passages the diagnosis would quarantine. This fixes nothing: the
rare-word cut-off (Zipf 3.5) was set before this check and is not tuned on it.

Usage (from backend/): PYTHONPATH=. python ../docs/research/scripts/monitor_dry_check.py OUT.json
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from langchain_core.documents import Document

from app.defence import runtime_monitor as rm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse_defence import outcome

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e"


def main(out_path):
    onto = rm.trusted_ontology()
    manifest = json.loads((RUN / "manifest.json").read_text())
    questions = {q["id"]: q for q in manifest["benchmark"]["data"]}
    table = defaultdict(Counter)
    examples, quarantine = defaultdict(list), defaultdict(set)
    for unit in manifest["schedule"]:
        q = questions[unit["question_id"]]
        for cond in ("clean", "poisoned"):
            pre = RUN / "observations" / f"{unit['index']:06d}-{cond}"
            rag = json.loads(Path(f"{pre}-rag.json").read_text())
            score = json.loads(Path(f"{pre}-correctness.json").read_text())["capture"].get("raw_score")
            label = outcome(rag.get("answer"), score)
            docs = [Document(page_content=s["content"], metadata={**s["metadata"], "source": s["source"]})
                    for s in rag["capture"].get("sources") or []]
            attack = onto.attack_for(q["question"], docs)
            viol = rm.check(rag.get("answer") or "", q["question"], attack, onto)
            specs = {v.spec for v in viol}
            table[cond]["answers"] += 1
            table[cond][f"label_{label}"] += 1
            for s in specs:
                table[cond][s] += 1
                table[cond][f"{s}|{label}"] += 1
            if viol:
                table[cond]["any_violation"] += 1
                for key in rm.diagnose(viol, docs, onto):
                    quarantine[cond].add(key)
                if len(examples[cond]) < 8 and "phi1_lexical" in specs:
                    examples[cond].append({"question_id": q["id"], "label": label,
                                           "witnesses": [w for v in viol for w in v.witnesses]})
    report = {"policy_version": "runtime-monitor-v1 (check without context)", "rare_zipf": rm.RARE_ZIPF, "run": RUN.name,
              "counts": {c: dict(sorted(t.items())) for c, t in table.items()},
              "passages_diagnosis_would_quarantine": {c: len(k) for c, k in quarantine.items()},
              "phi1_examples": examples}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
