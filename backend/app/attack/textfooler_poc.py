"""Adversarial attack proof-of-concept."""

from textattack import Attacker, AttackArgs
from textattack.attack_recipes import TextFoolerJin2019
from textattack.datasets import Dataset
from textattack.models.wrappers import HuggingFaceModelWrapper
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


TARGET_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"


def run_poc() -> None:
    tokenizer = AutoTokenizer.from_pretrained(TARGET_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(TARGET_MODEL)
    model_wrapper = HuggingFaceModelWrapper(model, tokenizer)

    attack = TextFoolerJin2019.build(model_wrapper)

    # Labels: 0 = negative, 1 = positive.
    test_samples = [
        (
            "The performance was absolutely wonderful and the acting "
            "was superb, easily the best film I have seen this year.",
            1,
        ),
        (
            "This was a terrible waste of time, badly acted and boring "
            "from start to finish, I regret every minute.",
            0,
        ),
    ]

    dataset = Dataset(test_samples)

    attack_args = AttackArgs(
        num_examples=len(test_samples),
        disable_stdout=False,
    )

    attacker = Attacker(attack, dataset, attack_args)
    attacker.attack_dataset()


if __name__ == "__main__":
    run_poc()