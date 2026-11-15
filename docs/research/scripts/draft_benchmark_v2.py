"""Draft the benchmark v2 questions for the attack types added in knowledge base v2.

Same question templates, reference-fact rules and record fields as benchmark v1
(build_benchmark_v1.py). For every added attack type:
  attack_description   reference = the section text, verbatim
  prerequisites        reference = the section text, verbatim (skipped when shorter than 60
                       characters: too thin to separate correct from partial, as in v1)
and, going through the attack types in alphabetical order and alternating between the two, one
extra question each until TARGET questions exist:
  execution_flow       one fact per CAPEC step ("Step: first sentence")
  consequences         plain-language impact facts derived from the CAPEC consequence list
This is a draft for human review. Nothing is frozen and no split is drawn here.

Output: docs/research/benchmark-review/draft-v2/questions_v2_draft.json and review-sheet.csv.
Offline. Usage:  python docs/research/scripts/draft_benchmark_v2.py
"""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_benchmark_v1 as v1

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "backend/data/kb_v2/knowledge_base"
OUT = ROOT / "docs/research/benchmark-review/draft-v2"
TARGET = 106
MIN_PREREQUISITES = 60
TEMPLATES = {
    "attack_description": "How does {name} work, according to the knowledge base?",
    "prerequisites": "What conditions are required for {name} in the knowledge base?",
    "execution_flow": "What main stages does the knowledge base describe for {name}?",
    "consequences": "What consequences does the knowledge base list for {name}?",
}
HEADINGS = {
    "attack_description": "Attack description",
    "prerequisites": "Prerequisites",
    "execution_flow": "Execution flow",
    "consequences": "Consequences",
}


def section(text, heading):
    match = re.search(
        rf"^## {re.escape(heading)}\n\n(.*?)(?=\n## |\Z)", text, re.DOTALL | re.MULTILINE
    )
    if not match:
        return None
    body = match.group(1).strip()
    start = match.start(1)
    return body, start, start + len(body)


def facts(category, body):
    if category == "execution_flow":
        return v1.step_facts(body), "derived_from_structured_source"
    if category == "consequences":
        return (
            v1.consequence_facts(re.sub(r" \([^)]*\)", "", body)),
            "derived_from_structured_source",
        )
    text = " ".join(
        line.lstrip("- ").strip() for line in body.splitlines() if line.strip()
    )
    return [v1.strip_markup(text)], "verbatim_source_text"


def main():
    if OUT.exists():
        raise FileExistsError(f"{OUT} already exists; outputs are create-only")
    mapping = yaml.safe_load(
        (ROOT / "backend/data/kb_v2/source_mapping_v2.yaml").read_text()
    )["attacks"]
    v1_keys = set(
        yaml.safe_load(
            (ROOT / "backend/app/kb_builder/source_mapping.yaml").read_text()
        )["attacks"]
    )
    new = sorted(k for k in mapping if k not in v1_keys)
    questions, extras = [], []

    def make(key, category):
        spec = mapping[key]
        relative = spec["output_path"].split("knowledge_base/")[1]
        text = (KB / relative).read_text(encoding="utf-8")
        found = section(text, HEADINGS[category])
        if not found:
            return None
        body, start, end = found
        reference, provenance = facts(category, body)
        if not reference or not all(reference):
            return None
        if category == "prerequisites" and len(body) < MIN_PREREQUISITES:
            return None
        if category == "execution_flow" and len(reference) < 2:
            return None
        return {
            "id": f"v2_{key}_{category}_01",
            "question": TEMPLATES[category].format(name=spec["display_name"]),
            "expected_attack_type": key,
            "expected_sections": [category],
            "reference_facts": reference,
            "question_category": category,
            "source_document": relative,
            "source_evidence": {
                "corpus_relative_path": relative,
                "file_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "heading": HEADINGS[category],
                "start_char": start,
                "end_char": end,
                "exact_excerpt": body,
            },
            "reference_fact_provenance": provenance,
            "benchmark_version": "v2-draft",
        }

    for key in new:
        for category in ("attack_description", "prerequisites"):
            item = make(key, category)
            if item:
                questions.append(item)
    turn = 0
    for key in new:
        if len(questions) + len(extras) >= TARGET:
            break
        order = ("execution_flow", "consequences")
        for category in (order[turn % 2], order[(turn + 1) % 2]):
            item = make(key, category)
            if item:
                extras.append(item)
                turn += 1
                break
    questions += extras
    questions.sort(key=lambda q: q["id"])
    OUT.mkdir(parents=True)
    (OUT / "questions_v2_draft.json").write_text(
        json.dumps(questions, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (OUT / "review-sheet.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "attack_type",
                "category",
                "question",
                "reference_facts",
                "source_excerpt",
                "review_decision (keep / edit / drop)",
                "review_notes",
            ]
        )
        for q in questions:
            writer.writerow(
                [
                    q["id"],
                    q["expected_attack_type"],
                    q["question_category"],
                    q["question"],
                    " | ".join(q["reference_facts"]),
                    q["source_evidence"]["exact_excerpt"][:1500],
                    "",
                    "",
                ]
            )
    from collections import Counter

    print(len(questions), Counter(q["question_category"] for q in questions))


if __name__ == "__main__":
    main()
