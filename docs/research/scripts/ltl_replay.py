"""Replay the recorded monitor runs through monitors generated from the LTL formulas.

The live runs used hand-written checks for phi1 and phi2 and a set lookup for phi3. Here the three
properties are the formulas in app.defence.ltl_monitor (PHI1, PHI2, PHI3), and the monitors are
generated from them by formula progression. For every recorded draft the atomic propositions are
recomputed from the recorded answer, question, attack and retrieved passages, the generated
monitors are stepped, and their verdicts are compared with the violations the live run recorded.
phi3 is monitored per passage over the whole run trace of each condition.

Offline apart from the passage lookup in Qdrant; no model calls.

Usage (from backend/, Qdrant running):
  PYTHONPATH=. python ../docs/research/scripts/ltl_replay.py OUT_JSON RUN_DIR [RUN_DIR ...]
"""

import json
import sys
from pathlib import Path

from app.config import QDRANT_URL, get_qdrant_collection
from app.defence import ltl_monitor as ltl
from app.defence import runtime_monitor as rm
from langchain_core.documents import Document
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[3]


def passage_texts(state):
    client, out, offset = QdrantClient(url=QDRANT_URL), {}, None
    while True:
        points, offset = client.scroll(
            get_qdrant_collection(state), limit=256, offset=offset, with_payload=True
        )
        for p in points:
            doc = Document(
                page_content=p.payload.get("page_content", ""),
                metadata=p.payload.get("metadata", {}),
            )
            out[rm.passage_key(doc)] = doc.page_content
        if offset is None:
            return out


def propositions(answer, question, attack, context, ontology):
    """The labelling function: which atomic propositions hold for this draft."""
    props = {"draft"}
    seen = set()
    for text in context:
        seen |= set(rm.words(text)) | rm.base_words(text)
    rare = rm.rare_out_of_vocabulary(
        answer, ontology.vocabulary, rm.base_words(question) | set(rm.words(question))
    )
    if any(w in seen or rm.base_form(w) in seen for w in rare):
        props.add("rare_copied")
    if rm.abstains(answer):
        props.add("refusal")
    if ontology.covers(attack):
        props.add("covered")
    return props


def replay(run_dir, ontology, questions, texts):
    run = Path(run_dir)
    manifest = json.loads((run / "manifest.json").read_text())
    result = {
        "policy_version": manifest["monitor"]["policy_version"],
        "conditions": {},
    }
    for condition, spec in manifest["conditions"].items():
        lookup = texts[spec["source_state"]]
        phi1, phi2 = (
            ltl.Monitor(ltl.PHI1, reset=True),
            ltl.Monitor(ltl.PHI2, reset=True),
        )
        phi3 = ltl.ParametricMonitor(ltl.PHI3)
        drafts = agree = phi1_violations = phi2_violations = 0
        disagreements, phi3_violated = [], set()
        for unit in manifest["schedule"]:
            path = run / "observations" / f"{unit['index']:06d}-{condition}-rag.json"
            monitor = json.loads(path.read_text())["capture"].get("monitor")
            if not monitor:  # the one answer lost to a network error has no trace
                continue
            question = questions[unit["question_id"]]
            keys = []
            for step in monitor["rounds"]:
                if "context_keys" in step:
                    keys = step["context_keys"]
                    phi3_violated |= set(phi3.step({f"in_context_{k}" for k in keys}))
                props = propositions(
                    step["answer"],
                    question,
                    monitor["attack"],
                    [lookup[k] for k in keys],
                    ontology,
                )
                generated = {
                    "phi1_lexical": phi1.step(props) == "violated",
                    "phi2_availability": phi2.step(props) == "violated",
                }
                recorded = {v["spec"] for v in step["violations"]}
                drafts += 1
                phi1_violations += generated["phi1_lexical"]
                phi2_violations += generated["phi2_availability"]
                if {s for s, bad in generated.items() if bad} == recorded:
                    agree += 1
                else:
                    disagreements.append(
                        {
                            "index": unit["index"],
                            "round": step["round"],
                            "generated": sorted(s for s, b in generated.items() if b),
                            "recorded": sorted(recorded),
                        }
                    )
                if step.get("quarantined"):
                    phi3_violated |= set(
                        phi3.step({f"quarantined_{k}" for k in step["quarantined"]})
                    )
        result["conditions"][condition] = {
            "drafts_checked": drafts,
            "verdicts_equal_to_recorded": agree,
            "disagreements": disagreements,
            "phi1_violations": phi1_violations,
            "phi2_violations": phi2_violations,
            "phi3_passages_monitored": len(phi3.instances),
            "phi3_violations": len(phi3_violated),
        }
    return result


def main(out, *run_dirs):
    ontology = rm.trusted_ontology()
    questions = {
        q["id"]: q["question"]
        for q in json.loads(
            (ROOT / "backend/data/evaluation/questions_v1.json").read_text()
        )
    }
    texts = {s: passage_texts(s) for s in ("poisoned", "clean", "textfooler")}
    summary = {
        "formulas": {"phi1": ltl.PHI1, "phi2": ltl.PHI2, "phi3": ltl.PHI3},
        "runs": {Path(r).name: replay(r, ontology, questions, texts) for r in run_dirs},
    }
    cells = [c for r in summary["runs"].values() for c in r["conditions"].values()]
    summary["total"] = {
        "drafts_checked": sum(c["drafts_checked"] for c in cells),
        "verdicts_equal_to_recorded": sum(
            c["verdicts_equal_to_recorded"] for c in cells
        ),
        "phi3_violations": sum(c["phi3_violations"] for c in cells),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "runs"}, indent=1))
    for name, run in summary["runs"].items():
        for c, v in run["conditions"].items():
            print(
                name[-8:],
                run["policy_version"],
                c,
                {k: x for k, x in v.items() if k != "disagreements"},
                v["disagreements"][:3],
            )


if __name__ == "__main__":
    main(*sys.argv[1:])
