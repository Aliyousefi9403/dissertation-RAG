"""
Adaptive PWWS: the same attack, constrained to evade the entropy-filter defence.

The entropy filter (app/defence/entropy_filter.py) flags words that are much
rarer, under a domain reference q, than a WordNet synonym. An attacker who knows
that can simply refuse such swaps. This script runs the unchanged PWWS recipe
(PWWSRen2019, same surrogate, same sections, same skip rules) with one extra
TextAttack constraint:

    a swap original -> substitute is allowed only if q(substitute) >= q(original)

where q is the defender's own reference (DomainReference, leave-one-document-out,
lambda 0.5 domain / 0.5 English), built from the clean knowledge base the attacker
is poisoning. This is the strongest adaptive attacker for this detector: it knows
the detector's reference exactly.

  --variant adaptive   constrained attack  -> data/poisoned_adaptive/
  --variant control    unconstrained PWWS  -> data/poisoned_pwws_rerun/
                       (matched control when the surrogate had to be retrained)

Create-only: refuses to run if the output folder or manifest exists. The clean
knowledge base and the original poisoned corpus are never touched.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from app.attack import pwws_poison_kb as base
from app.defence.entropy_filter import DomainReference

PROJECT_ROOT = base.PROJECT_ROOT
CLEAN_KB = base.CLEAN_KB
VARIANTS = {
    "adaptive": PROJECT_ROOT / "data" / "poisoned_adaptive",
    "control": PROJECT_ROOT / "data" / "poisoned_pwws_rerun",
}


def domain_frequency_constraint(reference: DomainReference):
    """TextAttack constraint: reject swaps that make a word rarer under q."""
    from textattack.constraints import Constraint

    class DomainFrequencyConstraint(Constraint):
        def __init__(self):
            super().__init__(compare_against_original=True)
            self.document = ""

        def _check_constraint(self, transformed_text, reference_text):
            indices = transformed_text.attack_attrs.get("newly_modified_indices", set())
            for i in indices:
                new, old = transformed_text.words[i].lower(), reference_text.words[i].lower()
                if reference.probability(new, self.document) < reference.probability(old, self.document):
                    return False
            return True

        def extra_repr_keys(self):
            return ["compare_against_original"]

    return DomainFrequencyConstraint()


def build_attack(wrapper, constraint=None):
    from textattack import Attack
    from textattack.attack_recipes import PWWSRen2019

    recipe = PWWSRen2019.build(wrapper)
    if constraint is None:
        return recipe
    return Attack(recipe.goal_function, recipe.pre_transformation_constraints + recipe.constraints + [constraint],
                  recipe.transformation, recipe.search_method)


def prepare_output(out_dir: Path) -> tuple[Path, Path]:
    kb, manifest = out_dir / "knowledge_base", out_dir / "pwws_attack_manifest.jsonl"
    if kb.exists() or manifest.exists():
        raise FileExistsError(f"{out_dir} already exists; outputs are create-only")
    shutil.copytree(CLEAN_KB, kb)
    return kb, manifest


def poison_file(path: Path, kb: Path, attack, label_map: dict, constraint=None) -> list[dict]:
    label_name = path.stem
    if label_name not in label_map:
        return []
    label = label_map[label_name]
    relative = path.relative_to(kb).as_posix()
    if constraint is not None:
        constraint.document = relative
    sections = base.parse_sections(path.read_text(encoding="utf-8"))
    entries = []
    for section in sections:
        heading = section["heading"].replace("##", "").strip().lower()
        if heading in base.SKIP_SECTIONS:
            continue
        text = base.extract_attack_text(section["body"])
        if len(text) < base.MIN_TEXT_LENGTH:
            continue
        entry = {"file": relative, "attack_type": label_name, "section": heading, "label": label}
        try:
            success, adversarial, result_type = base.run_pwws(attack, text, label)
        except Exception as exc:  # recorded, never hidden
            entries.append({**entry, "success": False, "result": "error", "error": str(exc)})
            continue
        if success:
            section["body"] = "\n\n" + adversarial + "\n"
            entries.append({**entry, "success": True, "result": result_type,
                            "original_text": text, "adversarial_text": adversarial})
        else:
            entries.append({**entry, "success": False, "result": result_type})
    path.write_text(base.rebuild_document(sections), encoding="utf-8")
    return entries


def main(variant: str) -> None:
    from textattack.models.wrappers import HuggingFaceModelWrapper
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if not base.MODEL_DIR.exists():
        raise RuntimeError(f"Surrogate not found: {base.MODEL_DIR}")
    kb, manifest = prepare_output(VARIANTS[variant])
    wrapper = HuggingFaceModelWrapper(AutoModelForSequenceClassification.from_pretrained(base.MODEL_DIR),
                                      AutoTokenizer.from_pretrained(base.MODEL_DIR))
    constraint = domain_frequency_constraint(DomainReference(CLEAN_KB)) if variant == "adaptive" else None
    attack = build_attack(wrapper, constraint)
    label_map = json.loads(base.LABEL_MAP_FILE.read_text(encoding="utf-8"))
    entries = []
    for path in sorted(kb.rglob("*.md")):
        if path.parent.name != "devices":
            entries += poison_file(path, kb, attack, label_map, constraint)
            print(f"{path.relative_to(kb)}: {sum(e['success'] for e in entries)} successful so far", flush=True)
    with manifest.open("x", encoding="utf-8") as handle:
        handle.writelines(json.dumps(e) + "\n" for e in entries)
    print(f"{variant}: {sum(e['success'] for e in entries)}/{len(entries)} sections attacked successfully -> {kb}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    main(parser.parse_args().variant)
