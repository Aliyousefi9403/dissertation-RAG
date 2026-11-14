"""Knowledge base v2: the 14 attack types of v1 plus further CAPEC attack patterns, built by the
same builder from the same pinned MITRE files. Nothing under data/raw is touched.

Selection rule for the added attack types (fixed before any experiment on v2):
  CAPEC attack patterns that are not deprecated, have an execution flow, prerequisites,
  consequences and mitigations, a description of more than 150 characters, and a mapping to an
  Enterprise ATT&CK technique that is still active; patterns already used in v1 are excluded;
  the list is ordered by CAPEC number and the first TARGET_NEW are taken.

Output: backend/data/kb_v2/source_mapping_v2.yaml and backend/data/kb_v2/knowledge_base/.
The four device documents of v1 are copied unchanged.

Usage (from backend/):  PYTHONPATH=. python ../docs/research/scripts/build_kb_v2.py
"""

import json
import re
import shutil

import yaml
from app.kb_builder import build_knowledge_base as kb

TARGET_NEW = 46
OUT = kb.PROJECT_ROOT / "data/kb_v2"
V1_PREFIX, V2_PREFIX = "data/raw/knowledge_base/", "data/kb_v2/knowledge_base/"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def external_id(obj, source):
    return next(
        (
            r["external_id"]
            for r in obj.get("external_references", [])
            if r.get("source_name") == source and r.get("external_id")
        ),
        None,
    )


def main():
    if OUT.exists():
        raise FileExistsError(f"{OUT} already exists; outputs are create-only")
    v1 = yaml.safe_load(kb.MAPPING_FILE.read_text(encoding="utf-8"))
    used = {
        s.get("id")
        for a in v1["attacks"].values()
        for s in [a["primary_source"], *a.get("supporting_sources", [])]
    }
    attack_data = kb.load_attack_data()
    capec = json.loads(kb.CAPEC_STIX_FILE.read_text(encoding="utf-8"))["objects"]
    candidates = []
    for obj in capec:
        if obj["type"] != "attack-pattern" or obj.get("revoked"):
            continue
        if obj.get("x_capec_status") == "Deprecated":
            continue
        capec_id, technique = external_id(obj, "capec"), external_id(obj, "ATTACK")
        if not capec_id or capec_id in used or not technique:
            continue
        if not all(
            obj.get(f)
            for f in (
                "x_capec_execution_flow",
                "x_capec_prerequisites",
                "x_capec_consequences",
            )
        ):
            continue
        if len(obj.get("description", "")) <= 150:
            continue
        if not any(
            m.get("type") == "relationship"
            and m.get("relationship_type") == "mitigates"
            and m.get("target_ref") == obj["id"]
            for m in capec
        ):
            continue
        technique = technique if technique.startswith("T") else f"T{technique}"
        try:
            kb.get_attack_technique(attack_data, technique)
        except ValueError:
            continue
        candidates.append((int(capec_id.split("-")[1]), capec_id, technique, obj))
    candidates.sort(key=lambda c: c[0])
    attacks = {}
    for key, spec in v1["attacks"].items():
        attacks[key] = {
            **spec,
            "output_path": spec["output_path"].replace(V1_PREFIX, V2_PREFIX),
        }
    names = {a["display_name"].lower() for a in attacks.values()}
    added = []
    for _, capec_id, technique, obj in candidates:
        if len(added) == TARGET_NEW:
            break
        key = slug(obj["name"])
        if key in attacks or obj["name"].lower() in names:
            continue
        category = slug((obj.get("x_capec_domains") or ["other"])[0])
        attacks[key] = {
            "display_name": obj["name"],
            "category": category,
            "output_path": f"{V2_PREFIX}{category}/{key}.md",
            "primary_source": {
                "system": "CAPEC",
                "id": capec_id,
                "role": "attack_mechanism",
                "required": True,
            },
            "supporting_sources": [
                {
                    "system": "MITRE_ATTACK_ENTERPRISE",
                    "id": technique,
                    "role": "adversary_context",
                    "required": True,
                }
            ],
            "extraction": {
                "use_llm": False,
                "preserve_source_text": True,
                "generate_markdown": True,
                "human_review_required": True,
            },
        }
        added.append(key)
    OUT.mkdir(parents=True)
    mapping = OUT / "source_mapping_v2.yaml"
    mapping.write_text(
        yaml.safe_dump({"version": 2, "attacks": attacks}, sort_keys=False),
        encoding="utf-8",
    )
    kb.MAPPING_FILE = mapping
    kb.main()
    shutil.copytree(
        kb.PROJECT_ROOT / V1_PREFIX / "devices", kb.PROJECT_ROOT / V2_PREFIX / "devices"
    )
    print(
        f"candidates: {len(candidates)}; added: {len(added)}; total attack types: {len(attacks)}"
    )


if __name__ == "__main__":
    main()
