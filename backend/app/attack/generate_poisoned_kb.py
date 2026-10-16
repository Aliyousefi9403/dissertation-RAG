import json
import shutil
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]

KB_ROOT = BACKEND_ROOT / "data" / "raw" / "knowledge_base"
POISONED_ROOT = BACKEND_ROOT / "data" / "poisoned" / "knowledge_base"
MANIFEST = BACKEND_ROOT / "data" / "external" / "enterprise_attack.json"


def copy_clean_kb():
    if POISONED_ROOT.exists():
        shutil.rmtree(POISONED_ROOT)

    shutil.copytree(KB_ROOT, POISONED_ROOT)


def load_manifest():
    with open(MANIFEST, "r") as f:
        return json.load(f)


def count_markdown_files(root: Path) -> int:
    return sum(1 for _ in root.rglob("*.md"))


def main():
    print("Creating poisoned knowledge-base snapshot...")
    print(f"BACKEND_ROOT = {BACKEND_ROOT}")
    print(f"KB_ROOT = {KB_ROOT}")
    print(f"POISONED_ROOT = {POISONED_ROOT}")

    copy_clean_kb()

    clean_count = count_markdown_files(KB_ROOT)
    poisoned_count = count_markdown_files(POISONED_ROOT)

    print(f"Clean markdown files: {clean_count}")
    print(f"Poisoned markdown files: {poisoned_count}")

    if clean_count == 0:
        raise RuntimeError(
            f"No Markdown files found in clean KB: {KB_ROOT}"
    )

    if clean_count != poisoned_count:
        raise RuntimeError(
            "Copy verification failed: clean and poisoned KB file counts differ."
    )

    print(f"Poisoned KB created at: {POISONED_ROOT}")
    print("Snapshot verified.")


if __name__ == "__main__":
    main()