"""PWWS poisoning of knowledge base v2: the independent test corpus for the detectors.

Same attack, skip rules and create-only checkpoints as the v1 corpora (app.attack.pwws_adaptive_kb,
variant "control" = plain PWWS), with the paths redirected to knowledge base v2 and its 60-class
surrogate (models/bert_surrogate_v2/final). Only the 46 attack types added in v2 are attacked: the
14 v1 documents are copied unchanged, so detectors tuned on v1 are tested on documents they have
never seen.

Output: backend/data/kb_v2/poisoned_pwws/{knowledge_base, parts, pwws_attack_manifest.jsonl, run_log}.
Usage (from backend/, attack environment; run several workers with --resume for speed):
  PYTHONPATH=. python ../docs/research/scripts/attack_kb_v2.py [--resume]
"""

import sys
from pathlib import Path

import yaml
from app.attack import pwws_adaptive_kb as adaptive
from app.attack import pwws_poison_kb as base

V2 = base.PROJECT_ROOT / "data/kb_v2"
base.CLEAN_KB = adaptive.CLEAN_KB = V2 / "knowledge_base"
base.MODEL_DIR = base.PROJECT_ROOT / "models/bert_surrogate_v2/final"
base.LABEL_MAP_FILE = V2 / "bert_dataset/label_map.json"
adaptive.VARIANTS["kb_v2_pwws"] = V2 / "poisoned_pwws"

V1_KEYS = set(
    yaml.safe_load(
        (base.PROJECT_ROOT / "app/kb_builder/source_mapping.yaml").read_text()
    )["attacks"]
)
_poison_file = adaptive.poison_file


def poison_new_only(path, kb, attack, label_map, constraint=None):
    """v1 documents stay clean; only the added attack types are attacked."""
    if Path(path).stem in V1_KEYS:
        return []
    return _poison_file(path, kb, attack, label_map, constraint)


adaptive.poison_file = poison_new_only

if __name__ == "__main__":
    adaptive.main("kb_v2_pwws", resume="--resume" in sys.argv)
