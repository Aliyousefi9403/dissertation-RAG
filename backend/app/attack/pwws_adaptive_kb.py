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

  --variant adaptive     constrained attack  -> data/poisoned_adaptive/
  --variant adaptive_lm  second-order attack -> data/poisoned_adaptive_lm/
                         adds a second rule aimed at the contextual detector
                         (app/defence/contextual_filter.py): the swapped passage must be at
                         least as probable as the original under the same language model
  --variant adaptive_lm_budget  budgeted second-order attack -> data/poisoned_adaptive_lm_budget/
                         as adaptive_lm, but the passage may become up to LM_BUDGET_BITS less
                         probable (the strict rule of adaptive_lm allowed almost no swaps);
                         --budget-bits B writes to data/poisoned_adaptive_lm_budget_B/ instead
  --variant control    unconstrained PWWS  -> data/poisoned_pwws_rerun/
                       (matched control when the surrogate had to be retrained)
  --variant textfooler   TextFooler (Jin et al. 2020) instead of PWWS -> data/poisoned_textfooler/
                         a second word-substitution attack, to test whether the detectors
                         generalise beyond PWWS (substitutes come from counter-fitted word
                         embeddings, not WordNet)

Create-only: refuses to run if the output folder or manifest exists. The clean
knowledge base and the original poisoned corpus are never touched. Each finished
file is checkpointed in <out>/parts/; `--resume` continues an interrupted run,
restoring every unfinished file from the clean copy before attacking it, and
appends start/resume events to <out>/run_log.jsonl. Several `--resume` workers may run
at once: each claims a file with <out>/parts/<file>.lock (holding its pid and the boot id;
a lock from another boot, or whose process has gone, is stale), and whichever worker finds every file done writes the
manifest, in file order, from the parts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from app.attack import pwws_poison_kb as base
from app.defence.entropy_filter import DomainReference

PROJECT_ROOT = base.PROJECT_ROOT
CLEAN_KB = base.CLEAN_KB
VARIANTS = {
    "adaptive": PROJECT_ROOT / "data" / "poisoned_adaptive",
    "control": PROJECT_ROOT / "data" / "poisoned_pwws_rerun",
    "adaptive_lm": PROJECT_ROOT / "data" / "poisoned_adaptive_lm",
    "textfooler": PROJECT_ROOT / "data" / "poisoned_textfooler",
    "adaptive_lm_budget": PROJECT_ROOT / "data" / "poisoned_adaptive_lm_budget",
}
# Budget for adaptive_lm_budget: the contextual filter's threshold (contextual_filter.THRESHOLD_BITS),
# a natural scale for "how much less likely the language model may find the passage".
LM_BUDGET_BITS = 4.4611


def domain_frequency_constraint(
    reference: DomainReference, lm=None, budget_bits: float = 0.0
):
    """TextAttack constraint: reject swaps that make a word rarer under q.

    With `lm` (an object with log2_prob(texts) -> list[float]), also reject any
    transformed text that is more than `budget_bits` less probable than the original
    under that model (budget 0: at least as probable).
    """
    from textattack.constraints import Constraint

    class DomainFrequencyConstraint(Constraint):
        def __init__(self):
            super().__init__(compare_against_original=True)
            self.document = ""
            self._base = {}

        def _frequency_ok(self, transformed_text, reference_text):
            for i in transformed_text.attack_attrs.get("newly_modified_indices", set()):
                new, old = (
                    transformed_text.words[i].lower(),
                    reference_text.words[i].lower(),
                )
                if reference.probability(new, self.document) < reference.probability(
                    old, self.document
                ):
                    return False
            return True

        def _base_log2(self, reference_text):
            original = reference_text.text
            if original not in self._base:
                self._base = {original: lm.log2_prob([original])[0]}
            return self._base[original]

        def _check_constraint(self, transformed_text, reference_text):
            if not self._frequency_ok(transformed_text, reference_text):
                return False
            if lm is None or not transformed_text.attack_attrs.get(
                "newly_modified_indices"
            ):
                return True
            return (
                lm.log2_prob([transformed_text.text])[0]
                >= self._base_log2(reference_text) - budget_bits
            )

        def _check_constraint_many(self, transformed_texts, reference_text):
            # Same rule as _check_constraint; the language model scores all survivors in one batch.
            survivors = [
                t for t in transformed_texts if self._frequency_ok(t, reference_text)
            ]
            if lm is None:
                return survivors
            scored = [
                t for t in survivors if t.attack_attrs.get("newly_modified_indices")
            ]
            if not scored:
                return survivors
            base = self._base_log2(reference_text) - budget_bits
            keep = {
                id(t)
                for t, lp in zip(scored, lm.log2_prob([t.text for t in scored]))
                if lp >= base
            }
            return [
                t
                for t in survivors
                if id(t) in keep or not t.attack_attrs.get("newly_modified_indices")
            ]

        def extra_repr_keys(self):
            return ["compare_against_original"]

    return DomainFrequencyConstraint()


class SmallBatches:
    """Scores texts a few at a time: whole sections x 16 at once exhausted memory (full-vocabulary logits)."""

    def __init__(self, lm, size: int = 4):
        self.lm, self.size = lm, size

    def log2_prob(self, texts: list[str]) -> list[float]:
        return [
            p
            for i in range(0, len(texts), self.size)
            for p in self.lm.log2_prob(texts[i : i + self.size])
        ]


def build_attack(wrapper, constraint=None, recipe_name="pwws"):
    from textattack import Attack
    from textattack.attack_recipes import PWWSRen2019, TextFoolerJin2019

    recipe = (TextFoolerJin2019 if recipe_name == "textfooler" else PWWSRen2019).build(
        wrapper
    )
    if constraint is None:
        return recipe
    return Attack(
        recipe.goal_function,
        recipe.pre_transformation_constraints + recipe.constraints + [constraint],
        recipe.transformation,
        recipe.search_method,
    )


def prepare_output(out_dir: Path, resume: bool = False) -> tuple[Path, Path]:
    kb, manifest = out_dir / "knowledge_base", out_dir / "pwws_attack_manifest.jsonl"
    if manifest.exists():
        raise FileExistsError(f"{manifest} already exists; outputs are create-only")
    if kb.exists() and not resume:
        raise FileExistsError(
            f"{out_dir} already exists; outputs are create-only (use --resume to continue)"
        )
    if not kb.exists():
        shutil.copytree(CLEAN_KB, kb)
    (out_dir / "parts").mkdir(exist_ok=True)
    return kb, manifest


def part_path(out_dir: Path, relative: str) -> Path:
    return out_dir / "parts" / (relative.replace("/", "__") + ".json")


def write_part(part: Path, entries: list[dict]) -> None:
    tmp = part.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries), encoding="utf-8")
    os.replace(tmp, part)  # atomic: a part exists only once its file is fully attacked


CODE_SHA256 = hashlib.sha256(
    Path(__file__).read_bytes()
).hexdigest()  # the code this process runs


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "unknown"


def claim(part: Path) -> bool:
    """Take the file for this worker unless a live process of this boot holds it."""
    lock = part.with_suffix(".lock")
    me = f"{os.getpid()} {boot_id()}"
    try:
        pid, _, boot = lock.read_text().strip().partition(" ")
        if boot != boot_id():
            raise ProcessLookupError  # left by a previous boot: pids may have been reused
        os.kill(int(pid), 0)
        return f"{pid} {boot}" == me
    except (FileNotFoundError, ValueError, ProcessLookupError):
        lock.unlink(missing_ok=True)  # stale or absent
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, me.encode())
    os.close(fd)
    return True


def collect(out_dir: Path, kb: Path):
    """All entries in file order, or None while some file is unfinished."""
    entries = []
    for path in sorted(kb.rglob("*.md")):
        if path.parent.name == "devices":
            continue
        part = part_path(out_dir, path.relative_to(kb).as_posix())
        if not part.exists():
            return None
        entries += json.loads(part.read_text(encoding="utf-8"))
    return entries


def log_event(out_dir: Path, event: str, **fields) -> None:
    with (out_dir / "run_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "event": event,
                    "at": datetime.now(UTC).isoformat(),
                    "code_sha256": CODE_SHA256,
                    **fields,
                }
            )
            + "\n"
        )


def poison_file(
    path: Path, kb: Path, attack, label_map: dict, constraint=None
) -> list[dict]:
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
        entry = {
            "file": relative,
            "attack_type": label_name,
            "section": heading,
            "label": label,
        }
        try:
            success, adversarial, result_type = base.run_pwws(attack, text, label)
        except Exception as exc:  # recorded, never hidden
            entries.append(
                {**entry, "success": False, "result": "error", "error": str(exc)}
            )
            continue
        if success:
            section["body"] = "\n\n" + adversarial + "\n"
            entries.append(
                {
                    **entry,
                    "success": True,
                    "result": result_type,
                    "original_text": text,
                    "adversarial_text": adversarial,
                }
            )
        else:
            entries.append({**entry, "success": False, "result": result_type})
    path.write_text(base.rebuild_document(sections), encoding="utf-8")
    return entries


def output_dir(variant: str, budget_bits: float | None = None) -> Path:
    if budget_bits is None or variant != "adaptive_lm_budget":
        return VARIANTS[variant]
    return PROJECT_ROOT / "data" / f"poisoned_adaptive_lm_budget_{budget_bits:g}"


def main(variant: str, resume: bool = False, budget_bits: float | None = None) -> None:
    from textattack.models.wrappers import HuggingFaceModelWrapper
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if not base.MODEL_DIR.exists():
        raise RuntimeError(f"Surrogate not found: {base.MODEL_DIR}")
    if budget_bits is not None and variant != "adaptive_lm_budget":
        raise ValueError("--budget-bits applies only to --variant adaptive_lm_budget")
    out_dir = output_dir(variant, budget_bits)
    kb, manifest = prepare_output(out_dir, resume)
    wrapper = HuggingFaceModelWrapper(
        AutoModelForSequenceClassification.from_pretrained(base.MODEL_DIR),
        AutoTokenizer.from_pretrained(base.MODEL_DIR),
    )
    lm = None
    if variant in ("adaptive_lm", "adaptive_lm_budget"):
        from app.defence.contextual_filter import LanguageModel

        lm = SmallBatches(
            LanguageModel(max_tokens=1024)
        )  # the whole section, so no swap escapes the rule
    budget = (
        (LM_BUDGET_BITS if budget_bits is None else budget_bits)
        if variant == "adaptive_lm_budget"
        else 0.0
    )
    constraint = (
        domain_frequency_constraint(DomainReference(CLEAN_KB), lm, budget)
        if variant.startswith("adaptive")
        else None
    )
    attack = build_attack(
        wrapper, constraint, "textfooler" if variant == "textfooler" else "pwws"
    )
    label_map = json.loads(base.LABEL_MAP_FILE.read_text(encoding="utf-8"))
    done = sorted(p.name for p in (out_dir / "parts").glob("*.json"))
    log_event(
        out_dir,
        "resume" if resume else "start",
        variant=variant,
        budget_bits=budget,
        files_already_done=done,
    )
    for path in sorted(kb.rglob("*.md")):
        if path.parent.name == "devices":
            continue
        relative = path.relative_to(kb).as_posix()
        part = part_path(out_dir, relative)
        if part.exists() or not claim(part):
            continue
        shutil.copyfile(
            CLEAN_KB / relative, path
        )  # an interrupted file restarts from the clean text
        file_entries = poison_file(path, kb, attack, label_map, constraint)
        write_part(part, file_entries)
        part.with_suffix(".lock").unlink(missing_ok=True)
        print(
            f"{relative}: {sum(e['success'] for e in file_entries)} successful in this file",
            flush=True,
        )
    entries = collect(out_dir, kb)
    if entries is None:
        print(
            "other workers still running; the last one writes the manifest", flush=True
        )
        return
    try:
        with manifest.open("x", encoding="utf-8") as handle:
            handle.writelines(json.dumps(e) + "\n" for e in entries)
    except FileExistsError:
        return  # another worker finished at the same moment and wrote it
    log_event(
        out_dir,
        "finish",
        successful=sum(e["success"] for e in entries),
        sections=len(entries),
    )
    print(
        f"{variant}: {sum(e['success'] for e in entries)}/{len(entries)} sections attacked successfully -> {kb}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="continue an interrupted run from its checkpoints",
    )
    parser.add_argument(
        "--budget-bits",
        type=float,
        help=f"LM budget for adaptive_lm_budget (default {LM_BUDGET_BITS})",
    )
    args = parser.parse_args()
    main(args.variant, args.resume, args.budget_bits)
