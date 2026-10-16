"""
Generate a PWWS-poisoned knowledge base.

Pipeline:
1. Read the clean KB.
2. Copy it to the poisoned KB.
3. Load the fine-tuned DistilBERT surrogate.
4. Run PWWS against attack-description text.
5. Replace successfully attacked text with adversarial text.
6. Save a JSONL manifest for dissertation evaluation.

Clean KB is never modified.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from textattack.attack_recipes import PWWSRen2019
from textattack.models.wrappers import HuggingFaceModelWrapper
from transformers import AutoModelForSequenceClassification, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLEAN_KB = PROJECT_ROOT / "data" / "raw" / "knowledge_base"
POISONED_KB = PROJECT_ROOT / "data" / "poisoned" / "knowledge_base"

MODEL_DIR = PROJECT_ROOT / "models" / "bert_surrogate" / "final"
LABEL_MAP_FILE = MODEL_DIR / "label_map.json"

MANIFEST_FILE = (
    PROJECT_ROOT / "data" / "poisoned" / "pwws_attack_manifest.jsonl"
)

# Do not attack provenance/source metadata.
SKIP_SECTIONS = {
    "metadata",
    "source mapping",
    "provenance",
}

MIN_TEXT_LENGTH = 80


def load_attack_model():
    print("Loading BERT surrogate...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DIR
    )

    wrapper = HuggingFaceModelWrapper(model, tokenizer)

    attack = PWWSRen2019.build(wrapper)

    with LABEL_MAP_FILE.open("r", encoding="utf-8") as f:
        label_map = json.load(f)

    print(f"Loaded {len(label_map)} attack classes.")

    return attack, label_map


def copy_clean_kb():
    print("\nPreparing poisoned KB...")

    if POISONED_KB.exists():
        shutil.rmtree(POISONED_KB)

    shutil.copytree(CLEAN_KB, POISONED_KB)

    print(f"Clean KB copied to:\n{POISONED_KB}")


def parse_sections(text: str):
    """
    Preserve markdown headings while separating section bodies.
    """

    pattern = r"(^##\s+.+$)"

    parts = re.split(
        pattern,
        text,
        flags=re.MULTILINE,
    )

    sections = []

    # Content before first ## heading.
    if parts and parts[0]:
        sections.append(
            {
                "heading": "",
                "body": parts[0],
            }
        )

    for i in range(1, len(parts), 2):
        heading = parts[i]

        body = parts[i + 1] if i + 1 < len(parts) else ""

        sections.append(
            {
                "heading": heading,
                "body": body,
            }
        )

    return sections


def rebuild_document(sections):
    output = []

    for section in sections:
        if section["heading"]:
            output.append(section["heading"])

        output.append(section["body"])

    return "\n".join(output)


def extract_attack_text(body: str):
    """
    Convert markdown-ish body into cleaner text for PWWS.
    """

    lines = []

    for line in body.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        lines.append(stripped)

    return " ".join(lines)


def run_pwws(attack, text: str, label: int):
    """
    Run one PWWS attack.

    Returns:
        success
        adversarial_text
        result type
    """

    result = attack.attack(text, label)

    result_type = type(result).__name__

    if result_type == "SuccessfulAttackResult":
        adversarial_text = (
            result.perturbed_result.attacked_text.text
        )

        return True, adversarial_text, result_type

    return False, text, result_type


def poison_file(
    path: Path,
    attack,
    label_map: dict,
):
    label_name = path.stem

    if label_name not in label_map:
        print(f"SKIP {path.name}: no BERT label.")
        return []

    label = label_map[label_name]

    text = path.read_text(encoding="utf-8")

    sections = parse_sections(text)

    manifest_entries = []

    print(f"\nAttacking: {path.name}")

    for section_index, section in enumerate(sections):

        heading = (
            section["heading"]
            .replace("##", "")
            .strip()
            .lower()
        )

        if heading in SKIP_SECTIONS:
            continue

        attack_text = extract_attack_text(section["body"])

        if len(attack_text) < MIN_TEXT_LENGTH:
            continue

        print(
            f"  [{section_index}] "
            f"{heading or 'document intro'} "
            f"({len(attack_text)} chars)"
        )

        try:
            success, adversarial_text, result_type = run_pwws(
                attack,
                attack_text,
                label,
            )

        except Exception as exc:
            print(f"      ERROR: {exc}")

            manifest_entries.append(
                {
                    "file": str(path.relative_to(POISONED_KB)),
                    "attack_type": label_name,
                    "section": heading,
                    "success": False,
                    "result": "error",
                    "error": str(exc),
                }
            )

            continue

        if success:
            print("      ✓ PWWS SUCCESS")

            original = attack_text

            # Replace section body with adversarial output.
            section["body"] = "\n\n" + adversarial_text + "\n"

            manifest_entries.append(
                {
                    "file": str(path.relative_to(POISONED_KB)),
                    "attack_type": label_name,
                    "section": heading,
                    "label": label,
                    "success": True,
                    "result": result_type,
                    "original_text": original,
                    "adversarial_text": adversarial_text,
                }
            )

        else:
            print(f"      ✗ {result_type}")

            manifest_entries.append(
                {
                    "file": str(path.relative_to(POISONED_KB)),
                    "attack_type": label_name,
                    "section": heading,
                    "label": label,
                    "success": False,
                    "result": result_type,
                }
            )

    path.write_text(
        rebuild_document(sections),
        encoding="utf-8",
    )

    return manifest_entries


def main():

    if not CLEAN_KB.exists():
        raise RuntimeError(
            f"Clean KB does not exist: {CLEAN_KB}"
        )

    if not MODEL_DIR.exists():
        raise RuntimeError(
            "Fine-tuned BERT model not found.\n"
            f"Expected: {MODEL_DIR}\n"
            "Run finetune_bert.py first."
        )

    copy_clean_kb()

    attack, label_map = load_attack_model()

    MANIFEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_entries = []

    files = sorted(POISONED_KB.rglob("*.md"))

    print(f"\nFound {len(files)} Markdown files.")

    for path in files:

        # Device documents are not attack classes.
        if path.parent.name == "devices":
            continue

        entries = poison_file(
            path,
            attack,
            label_map,
        )

        all_entries.extend(entries)

    with MANIFEST_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        for entry in all_entries:
            f.write(json.dumps(entry) + "\n")

    successes = sum(
        entry.get("success", False)
        for entry in all_entries
    )

    print("\n" + "=" * 60)
    print("PWWS POISONING COMPLETE")
    print("=" * 60)

    print(f"Sections attacked: {len(all_entries)}")
    print(f"Successful attacks: {successes}")

    if all_entries:
        print(
            "Attack success rate: "
            f"{successes / len(all_entries):.1%}"
        )

    print(f"\nPoisoned KB:\n{POISONED_KB}")
    print(f"\nAttack manifest:\n{MANIFEST_FILE}")


if __name__ == "__main__":
    main()