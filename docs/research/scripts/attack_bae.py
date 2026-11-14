"""BAE (Garg and Ramakrishnan, 2020) poisoning of the knowledge base: a third attack family.

PWWS and TextFooler pick replacements from fixed synonym sources (WordNet, counter-fitted
embeddings). BAE asks a masked language model (BERT) for words that fit the context, so its
edits are chosen to read naturally: the hardest case for a detector that looks for words a
language model finds less likely than a synonym.

Same surrogate, sections, skip rules and create-only checkpoints as the other corpora
(app.attack.pwws_adaptive_kb); only the attack recipe differs. No constraint from the defender.
Output: backend/data/poisoned_bae/ (knowledge_base, parts, manifest, run_log).

Usage (from backend/, attack environment):
  PYTHONPATH=. python ../docs/research/scripts/attack_bae.py [--resume]
"""

import sys

from app.attack import pwws_adaptive_kb as adaptive

adaptive.VARIANTS["bae"] = adaptive.PROJECT_ROOT / "data" / "poisoned_bae"


def build_attack(wrapper, constraint=None, recipe_name="pwws"):
    from textattack.attack_recipes import BAEGarg2019

    return BAEGarg2019.build(wrapper)


adaptive.build_attack = build_attack

if __name__ == "__main__":
    adaptive.main("bae", resume="--resume" in sys.argv)
