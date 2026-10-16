"""
Convert the knowledge base markdown files into a labeled classification dataset
for fine-tuning a BERT surrogate model.

Each attack document is chunked by its markdown sections. Each chunk becomes
one training sample, labeled with the parent document's attack type.

Output:
- data/processed/bert_dataset/train.jsonl
- data/processed/bert_dataset/val.jsonl
- data/processed/bert_dataset/label_map.json
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = PROJECT_ROOT / "data" / "raw" / "knowledge_base"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "bert_dataset"

# Skip the devices folder - those are device specs, not attacks
EXCLUDED_CATEGORIES = {"devices"}

# Reproducible train/val split
RANDOM_SEED = 42
VAL_SPLIT = 0.2

# Minimum characters per chunk to be considered a training sample
MIN_CHUNK_CHARS = 80


def load_attack_files() -> list[tuple[Path, str]]:
    """Find all attack markdown files, excluding device specs."""
    files = []
    for md_path in KB_DIR.rglob("*.md"):
        category = md_path.parent.name
        if category in EXCLUDED_CATEGORIES:
            continue
        # Attack label = filename without extension (e.g. "sql_injection")
        label = md_path.stem
        files.append((md_path, label))
    return sorted(files)


def chunk_markdown(text: str) -> list[str]:
    """
    Split a markdown document by ## section headers.
    Returns non-empty section bodies (excluding the header line itself).
    """
    sections = re.split(r"\n##\s+", text)
    chunks: list[str] = []
    for section in sections:
        # Strip the first line if it's still a heading, and any # H1 lines
        lines = section.strip().split("\n")
        body_lines = [line for line in lines if not line.startswith("#")]
        body = "\n".join(body_lines).strip()
        if len(body) >= MIN_CHUNK_CHARS:
            chunks.append(body)
    return chunks


def build_dataset() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = load_attack_files()
    if not files:
        raise RuntimeError(f"No attack markdown files found in {KB_DIR}")

    # Build label map (attack name -> integer id)
    labels = sorted({label for _, label in files})
    label_map = {label: idx for idx, label in enumerate(labels)}

    samples: list[dict] = []
    for md_path, label in files:
        text = md_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)
        for chunk in chunks:
            samples.append({
                "text": chunk,
                "label": label_map[label],
                "label_name": label,
                "source_file": str(md_path.relative_to(PROJECT_ROOT)),
            })

    # Deterministic shuffle + split
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(samples)
    split_idx = int(len(samples) * (1 - VAL_SPLIT))
    train_samples = samples[:split_idx]
    val_samples = samples[split_idx:]

    # Write outputs
    with (OUTPUT_DIR / "train.jsonl").open("w") as f:
        for sample in train_samples:
            f.write(json.dumps(sample) + "\n")

    with (OUTPUT_DIR / "val.jsonl").open("w") as f:
        for sample in val_samples:
            f.write(json.dumps(sample) + "\n")

    with (OUTPUT_DIR / "label_map.json").open("w") as f:
        json.dump(label_map, f, indent=2)

    # Report
    print(f"\nDataset preparation complete:")
    print(f"  Attack classes:    {len(label_map)}")
    print(f"  Total samples:     {len(samples)}")
    print(f"  Training samples:  {len(train_samples)}")
    print(f"  Validation samples:{len(val_samples)}")
    print(f"\nClasses:")
    for label, idx in label_map.items():
        count = sum(1 for s in samples if s["label"] == idx)
        print(f"  {idx:2d}  {label:30s}  {count} samples")
    print(f"\nOutput written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    build_dataset()