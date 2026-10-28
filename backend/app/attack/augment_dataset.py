"""Expand the KB-attack training dataset by paraphrasing each chunk with gpt-4o-mini."""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "data" / "processed" / "bert_dataset"

MODEL_NAME = "gpt-4o-mini"
PARAPHRASES_PER_SAMPLE = 4
RANDOM_SEED = 42
VAL_SPLIT = 0.2

PARAPHRASE_PROMPT = """You are helping build a cybersecurity classification dataset.

Rewrite the following technical description of a cybersecurity attack. Keep every technical fact identical. Preserve terminology, mechanisms, examples, and mitigations. Only vary the sentence structure, phrasing, and word choice.

Do not add new information. Do not remove information. Do not add commentary. Return only the rewritten description as plain text.

Original:
{text}

Rewritten:"""


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def paraphrase_once(client: OpenAI, text: str) -> str | None:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": PARAPHRASE_PROMPT.format(text=text)}],
            temperature=0.8,
            max_tokens=800,
        )
        result = response.choices[0].message.content
        return result.strip() if result else None
    except Exception as e:
        print(f"  API error: {e}")
        return None


def main() -> None:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY missing from .env")

    client = OpenAI(api_key=api_key)

    # Load current train+val samples
    train_samples = load_jsonl(DATASET_DIR / "train.jsonl")
    val_samples = load_jsonl(DATASET_DIR / "val.jsonl")
    all_samples = train_samples + val_samples

    print(f"Loaded {len(all_samples)} original samples")
    print(f"Generating {PARAPHRASES_PER_SAMPLE} paraphrases each")
    print(f"Target expanded size: {len(all_samples) * (PARAPHRASES_PER_SAMPLE + 1)}\n")

    expanded: list[dict] = []
    for i, sample in enumerate(all_samples, 1):
        # Keep the original
        expanded.append(sample)

        # Generate paraphrases
        print(f"[{i:3d}/{len(all_samples)}] {sample['label_name']}... ", end="", flush=True)
        successes = 0
        for _ in range(PARAPHRASES_PER_SAMPLE):
            paraphrased = paraphrase_once(client, sample["text"])
            if paraphrased and len(paraphrased) >= 50:
                expanded.append({
                    "text": paraphrased,
                    "label": sample["label"],
                    "label_name": sample["label_name"],
                    "source_file": sample["source_file"],
                    "augmented": True,
                })
                successes += 1
        print(f"+{successes}")

    # Re-shuffle and split
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(expanded)
    split_idx = int(len(expanded) * (1 - VAL_SPLIT))
    new_train = expanded[:split_idx]
    new_val = expanded[split_idx:]

    # Write
    with (DATASET_DIR / "train.jsonl").open("w") as f:
        for s in new_train:
            f.write(json.dumps(s) + "\n")

    with (DATASET_DIR / "val.jsonl").open("w") as f:
        for s in new_val:
            f.write(json.dumps(s) + "\n")

    print(f"\nAugmentation complete:")
    print(f"  Total samples: {len(expanded)}")
    print(f"  Training:      {len(new_train)}")
    print(f"  Validation:    {len(new_val)}")
    print(f"  Ratio: {len(expanded)/len(all_samples):.1f}x original")


if __name__ == "__main__":
    main()