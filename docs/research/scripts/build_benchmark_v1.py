"""Build the frozen benchmark v1 from the reviewed 45-question draft.

Deterministic and offline. Reads the draft and the clean corpus only, and
writes create-only outputs:

  backend/data/evaluation/questions_v1.json          frozen benchmark (pipeline format)
  backend/data/evaluation/benchmark_v1_record.json   decisions, split, provenance

Usage:
  python docs/research/scripts/build_benchmark_v1.py DRAFT.json

Decisions (approved by the author, 16 Oct 2026; see docs/research/pdd-review.md):
  * Fix the unmatchable section slug att_ck_adversary_context -> attck_adversary_context.
  * Execution-flow references -> one atomic fact per CAPEC step ("Step: first sentence"),
    extracted verbatim from the source HTML.
  * CAPEC consequence dictionaries -> plain-language impact facts (derived, flagged).
  * Long ATT&CK prose reference -> 4 verbatim key sentences (citations/links stripped).
  * Drop expanded_dns_spoofing_prerequisites_01 (reference "On/In Path Device" too thin).
  * Keep clean-retrieval-miss items; they are reported as a separate stratum, not reworded
    (rewording questions until retrieval succeeds would bias the benchmark).
  * Held-out split by source document, chosen before any v1 run: one document per category
    among documents NOT used by the 12-question pilot (malware has none), seeded draw.
"""

import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "backend/data/raw/knowledge_base"
OUT_Q = ROOT / "backend/data/evaluation/questions_v1.json"
OUT_R = ROOT / "backend/data/evaluation/benchmark_v1_record.json"
PILOT = ROOT / "backend/data/evaluation/questions.json"
SEED = 20261016

IMPACT_TEXT = {
    "Gain Privileges": "gain privileges",
    "Read Data": "read data",
    "Modify Data": "modify data",
    "Execute Unauthorized Commands (Run Arbitrary Code)": "execute unauthorized commands (run arbitrary code)",
    "Hide Activities": "hide their activities",
    "Bypass Protection Mechanism": "bypass protection mechanisms",
}
VULN_SENTENCES = [
    "Adversaries may scan victims for vulnerabilities that can be used during targeting.",
    "Vulnerability scans typically check if the configuration of a target host/application (ex: software and version) potentially aligns with the target of a specific exploit the adversary may seek to use.",
    "Vulnerability scans typically harvest running software and version numbers via server banners, listening ports, or other network artifacts.",
    "Information from these scans may reveal opportunities for other forms of reconnaissance",
]
DROP = {"expanded_dns_spoofing_prerequisites_01": "Reference 'On/In Path Device' is too thin to separate correct from partial answers."}


def strip_markup(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\(Citation:[^)]*\)", "", text)
    return " ".join(text.replace("**", "").split())


def first_sentence(text):
    text = " ".join(re.sub(r"<[^>]+>", " ", text).split())
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    return match.group(1) if match else text


def step_facts(document):
    return [f"{name.strip()}: {first_sentence(desc)}"
            for name, desc in re.findall(r"<b>(.*?):\s*</b>(.*?)</p>", document, re.S)]


def consequence_facts(reference):
    impacts = []
    for _, values in re.findall(r"(\w+): \[([^\]]*)\]", reference):
        for value in re.findall(r"'([^']+)'", values):
            if value in IMPACT_TEXT and IMPACT_TEXT[value] not in impacts:
                impacts.append(IMPACT_TEXT[value])
    return [f"A successful attack can allow the adversary to {impact}." for impact in impacts]


def main(draft_path):
    draft = json.loads(Path(draft_path).read_text())
    pilot_docs = set()
    for item in json.loads(PILOT.read_text()):
        pilot_docs |= {p.relative_to(CORPUS).as_posix() for p in CORPUS.rglob(f"{item['expected_attack_type']}.md")}
    docs = sorted({q["source_evidence"]["corpus_relative_path"] for q in draft})
    rng = random.Random(SEED)
    held_out = []
    for category in sorted({d.split("/")[0] for d in docs}):
        candidates = [d for d in docs if d.startswith(category + "/") and d not in pilot_docs]
        if candidates:
            held_out.append(rng.choice(candidates))

    questions, decisions = [], []
    for q in draft:
        text = (CORPUS / q["source_evidence"]["corpus_relative_path"]).read_text(encoding="utf-8")
        record = {"id": q["id"], "changes": []}
        if q["id"] in DROP:
            decisions.append({**record, "decision": "dropped", "reason": DROP[q["id"]]})
            continue
        item = {k: q[k] for k in ("id", "question", "expected_attack_type", "expected_sections", "reference_facts")}
        if item["expected_sections"] == ["att_ck_adversary_context"]:
            item["expected_sections"] = ["attck_adversary_context"]
            record["changes"].append("section slug fixed to normalize_heading() output")
        category = q["question_category"]
        reference = q["reference_facts"][0]
        if category == "execution_flow":
            item["reference_facts"] = step_facts(text)
            record["changes"].append(f"reference split into {len(item['reference_facts'])} verbatim step facts")
        elif category == "consequences":
            item["reference_facts"] = consequence_facts(reference)
            record["changes"].append("CAPEC consequence dictionary rewritten as plain impact facts (derived)")
        elif q["id"].startswith("expanded_vulnerability_scanning"):
            plain = strip_markup(text)
            assert all(s in plain for s in VULN_SENTENCES), "vulnerability sentences must be verbatim"
            item["reference_facts"] = VULN_SENTENCES
            record["changes"].append("reference reduced to 4 verbatim key sentences")
        assert item["reference_facts"] and all(isinstance(f, str) and f for f in item["reference_facts"])
        item.update(
            question_category=category,
            source_document=q["source_evidence"]["corpus_relative_path"],
            source_evidence=q["source_evidence"],
            split="held_out" if q["source_evidence"]["corpus_relative_path"] in held_out else "development",
            reference_fact_provenance="derived_from_structured_source" if category == "consequences" else "verbatim_source_text",
            benchmark_version="v1",
        )
        questions.append(item)
        decisions.append({**record, "decision": "revised" if record["changes"] else "accepted"})

    payload = json.dumps(questions, indent=2, ensure_ascii=False) + "\n"
    with OUT_Q.open("x", encoding="utf-8") as handle:
        handle.write(payload)
    record = {
        "benchmark_version": "v1",
        "frozen_on": "2026-10-16",
        "draft_sha256": hashlib.sha256(Path(draft_path).read_bytes()).hexdigest(),
        "questions_v1_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "question_count": len(questions),
        "dropped": [d for d in decisions if d["decision"] == "dropped"],
        "split_rule": "Held-out = one source document per category among documents not used by the 12-question pilot, random.Random(20261016).choice over sorted candidates; malware has no eligible document.",
        "pilot_documents": sorted(pilot_docs),
        "held_out_documents": held_out,
        "split_counts": {s: sum(q["split"] == s for q in questions) for s in ("development", "held_out")},
        "decisions": decisions,
        "known_limitations": [
            "Development questions share documents and sections with the 12-question pilot.",
            "Consequence facts are derived from CAPEC's structured field, not verbatim prose.",
            "13 questions miss the target section in clean top-3 retrieval (pre-check 2026-10-16); kept and reported as a stratum.",
            "Four flood prerequisite references differ only by protocol name.",
            "Questions were drafted from templates and reviewed by the author; no second annotator.",
        ],
    }
    with OUT_R.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("question_count", "held_out_documents", "split_counts", "questions_v1_sha256")}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
