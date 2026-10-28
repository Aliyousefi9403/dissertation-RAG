"""Build the formatting-only control corpus (no word substitutions).

It reproduces exactly what app/attack/pwws_poison_kb.py does to the
document layout:
  * every attacked (non-device) file is split on `##` headings and rebuilt
    with rebuild_document(), adding the same newlines;
  * every section with a successful PWWS entry is replaced by its flattened
    text, "\\n\\n" + text + "\\n";
but the inserted text is the manifest's ORIGINAL text, not the adversarial
text. Control and poisoned therefore differ only in PWWS word substitutions,
and clean and control differ only in layout. This separates the two effects.

Offline, no models. Create-only output: backend/data/control/knowledge_base
(the run fails if the directory exists). After writing, every file is checked:
control must equal the poisoned file once each adversarial section is swapped
back to its original text.

Usage: python docs/research/scripts/build_control_corpus.py
"""

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "backend"
CLEAN = ROOT / "data/raw/knowledge_base"
POISONED = ROOT / "data/poisoned/knowledge_base"
CONTROL = ROOT / "data/control/knowledge_base"
MANIFEST = ROOT / "data/poisoned/pwws_attack_manifest.jsonl"
SKIP_SECTIONS = {"metadata", "source mapping", "provenance"}


# --- verbatim copies of the layout functions in app/attack/pwws_poison_kb.py
def parse_sections(text):
    parts = re.split(r"(^##\s+.+$)", text, flags=re.MULTILINE)
    sections = []
    if parts and parts[0]:
        sections.append({"heading": "", "body": parts[0]})
    for i in range(1, len(parts), 2):
        sections.append(
            {"heading": parts[i], "body": parts[i + 1] if i + 1 < len(parts) else ""}
        )
    return sections


def rebuild_document(sections):
    output = []
    for section in sections:
        if section["heading"]:
            output.append(section["heading"])
        output.append(section["body"])
    return "\n".join(output)


# ============================================================
# -
# ============================================================


def main():
    entries = [
        json.loads(line) for line in MANIFEST.read_text().splitlines() if line.strip()
    ]
    attacked_files = {e["file"] for e in entries}
    successes = {(e["file"], e["section"]): e for e in entries if e.get("success")}
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(CLEAN, CONTROL)  # raises if CONTROL already exists

    report = {"files": {}, "successful_sections": len(successes)}
    for relative in sorted(attacked_files):
        sections = parse_sections((CLEAN / relative).read_text(encoding="utf-8"))
        swapped = 0
        for section in sections:
            heading = section["heading"].replace("##", "").strip().lower()
            entry = successes.get((relative, heading))
            if entry and heading not in SKIP_SECTIONS:
                section["body"] = "\n\n" + entry["original_text"] + "\n"
                swapped += 1
        control_text = rebuild_document(sections)
        (CONTROL / relative).write_text(control_text, encoding="utf-8")

        # Verification: poisoned with adversarial text swapped back == control.
        poisoned_text = (POISONED / relative).read_text(encoding="utf-8")
        for (file, _), entry in successes.items():
            if file == relative:
                assert poisoned_text.count(entry["adversarial_text"]) == 1, (
                    relative,
                    "adversarial text not unique",
                )
                poisoned_text = poisoned_text.replace(
                    entry["adversarial_text"], entry["original_text"]
                )
        assert poisoned_text == control_text, (
            f"{relative}: control differs from poisoned beyond word substitutions"
        )
        report["files"][relative] = {
            "flattened_sections": swapped,
            "sha256": hashlib.sha256(control_text.encode()).hexdigest(),
        }

    for path in sorted(CONTROL.rglob("*.md")):
        relative = path.relative_to(CONTROL).as_posix()
        if relative not in attacked_files:
            assert path.read_bytes() == (CLEAN / relative).read_bytes()
    (CONTROL.parent / "control_build_record.json").open("x").write(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "files_rebuilt": len(report["files"]),
                "sections_flattened": sum(
                    f["flattened_sections"] for f in report["files"].values()
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
