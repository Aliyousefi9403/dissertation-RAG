"""Fine-tune a DistilBERT classifier on the KB attack descriptions dataset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "data" / "processed" / "bert_dataset"
MODEL_OUTPUT_DIR = PROJECT_ROOT / "models" / "bert_surrogate"

MODEL_NAME = "distilbert-base-uncased"

# Hyperparameters
NUM_EPOCHS = 30
LEARNING_RATE = 5e-5
BATCH_SIZE = 4
MAX_LENGTH = 256
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def detect_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def compute_metrics(eval_pred) -> dict:
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    accuracy = float((predictions == labels).mean())
    return {"accuracy": accuracy}


def main() -> None:
    # Load labeled data
    train_samples = load_jsonl(DATASET_DIR / "train.jsonl")
    val_samples = load_jsonl(DATASET_DIR / "val.jsonl")
    with (DATASET_DIR / "label_map.json").open("r") as f:
        label_map = json.load(f)

    num_labels = len(label_map)
    id_to_label = {v: k for k, v in label_map.items()}

    print(f"Loaded {len(train_samples)} train / {len(val_samples)} val samples")
    print(f"Classes: {num_labels}")
    print(f"Device: {detect_device()}")

    # Load tokenizer and model
    print(f"\nInitialising {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        id2label=id_to_label,
        label2id=label_map,
    )

    # Convert and tokenize
    def to_hf(samples):
        return Dataset.from_dict({
            "text": [s["text"] for s in samples],
            "label": [s["label"] for s in samples],
        })

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding=False,
            max_length=MAX_LENGTH,
        )

    train_ds = to_hf(train_samples).map(tokenize, batched=True)
    val_ds = to_hf(val_samples).map(tokenize, batched=True)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Training configuration
    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
    output_dir=str(MODEL_OUTPUT_DIR),
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    warmup_ratio=WARMUP_RATIO,
    weight_decay=WEIGHT_DECAY,
    lr_scheduler_type="cosine",
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_accuracy",
    greater_is_better=True,
    save_total_limit=2,
    report_to="none",
)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print(f"\nTraining for {NUM_EPOCHS} epochs...\n")
    trainer.train()

    # Save the final (best) model
    final_dir = MODEL_OUTPUT_DIR / "final"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    with (final_dir / "label_map.json").open("w") as f:
        json.dump(label_map, f, indent=2)

    print("\nFinal evaluation:")
    for k, v in trainer.evaluate().items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    print(f"\nModel saved to: {final_dir}")


if __name__ == "__main__":
    main()