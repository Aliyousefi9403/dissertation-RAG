"""Surrogate classifier for knowledge base v2 (60 attack types): the v1 procedure, new folders.

Steps (same code as v1: app.attack.prepare_dataset, augment_dataset, finetune_bert; same prompts,
seeds and hyperparameters), with every path redirected so nothing under data/processed or
models/bert_surrogate is touched:
  prepare   sections of data/kb_v2/knowledge_base -> data/kb_v2/bert_dataset/
  augment   4 paraphrases per sample (gpt-4o-mini, as v1); calls run 8 at a time, order kept
  finetune  distilbert-base-uncased -> models/bert_surrogate_v2/final

Usage (from backend/):  PYTHONPATH=. python ../docs/research/scripts/surrogate_v2.py prepare|augment|finetune
"""

import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "backend"
DATASET = ROOT / "data/kb_v2/bert_dataset"
MODEL = ROOT / "models/bert_surrogate_v2"


def prepare():
    from app.attack import prepare_dataset as pd

    if DATASET.exists():
        raise FileExistsError(f"{DATASET} already exists; outputs are create-only")
    pd.KB_DIR, pd.OUTPUT_DIR = ROOT / "data/kb_v2/knowledge_base", DATASET
    pd.build_dataset()


def augment():
    from app.attack import augment_dataset as ad
    from openai import OpenAI

    done = DATASET / "augmented.json"
    if done.exists():
        raise FileExistsError("the dataset is already augmented")
    client = OpenAI(api_key=os.environ["LLM_API_KEY"])
    samples = ad.load_jsonl(DATASET / "train.jsonl") + ad.load_jsonl(
        DATASET / "val.jsonl"
    )
    jobs = [s for s in samples for _ in range(ad.PARAPHRASES_PER_SAMPLE)]
    with ThreadPoolExecutor(8) as pool:
        texts = list(pool.map(lambda s: ad.paraphrase_once(client, s["text"]), jobs))
    expanded, failed = [], 0
    for i, sample in enumerate(samples):
        expanded.append(sample)
        for text in texts[
            i * ad.PARAPHRASES_PER_SAMPLE : (i + 1) * ad.PARAPHRASES_PER_SAMPLE
        ]:
            if text and len(text) >= 50:
                expanded.append(
                    {
                        **{
                            k: sample[k] for k in ("label", "label_name", "source_file")
                        },
                        "text": text,
                        "augmented": True,
                    }
                )
            else:
                failed += 1
    random.Random(ad.RANDOM_SEED).shuffle(expanded)
    split = int(len(expanded) * (1 - ad.VAL_SPLIT))
    for name, part in (("train", expanded[:split]), ("val", expanded[split:])):
        with (DATASET / f"{name}.jsonl").open("w") as handle:
            handle.writelines(json.dumps(s) + "\n" for s in part)
    done.write_text(
        json.dumps(
            {
                "originals": len(samples),
                "paraphrases_requested": len(jobs),
                "paraphrases_failed": failed,
                "total": len(expanded),
                "model": ad.MODEL_NAME,
            },
            indent=1,
        )
        + "\n"
    )
    print(done.read_text())


def finetune():
    from app.attack import finetune_bert as fb

    fb.DATASET_DIR, fb.MODEL_OUTPUT_DIR = DATASET, MODEL
    fb.main()


if __name__ == "__main__":
    {"prepare": prepare, "augment": augment, "finetune": finetune}[sys.argv[1]]()
