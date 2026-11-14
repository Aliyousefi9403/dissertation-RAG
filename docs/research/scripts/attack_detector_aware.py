"""Detector-aware attacker: PWWS edits reworked until the contextual detector no longer flags them.

Threat model: the attacker knows the deployed detector completely (score, language model,
threshold, chunking) and can run it. Starting from each section PWWS poisoned successfully, the
attacker repeats (starting corpus: poisoned_pwws_rerun, the PWWS run made with the current surrogate):
  1. chunk the document as the pipeline does and score the chunks that overlap the section;
  2. if none is flagged and the surrogate is still fooled, stop: the section evades;
  3. otherwise take the flagged chunk's highest-gap word that the attacker introduced and
     (a) swap it for another WordNet synonym of the original word that keeps the surrogate
         fooled (the one the language model finds most likely), or, failing that,
     (b) put the original word back.
The section fails if the surrogate stops being fooled, or if the detector flags words the
attacker did not introduce. Failed sections are returned to the clean text, so the output corpus
contains only edits that pass the detector.

Output (create-only): backend/data/poisoned_evade/{knowledge_base, pwws_attack_manifest.jsonl,
evade_log.jsonl}. The manifest has the same fields as the other corpora, so the detector
evaluation scripts read it unchanged. No API calls.

Usage (from backend/):
  PYTHONPATH=. python ../docs/research/scripts/attack_detector_aware.py
"""

import difflib
import json
import re
import shutil
from pathlib import Path

import torch
from app.defence import contextual_filter as cf
from app.defence.entropy_filter import DomainReference, synonyms
from app.ingestion.load_documents import split_documents
from langchain_core.documents import Document
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3] / "backend"
MODEL_DIR = ROOT / "models/bert_surrogate/final"
SOURCE = ROOT / "data/poisoned_pwws_rerun"  # made with the surrogate that is on disk
OUT = ROOT / "data/poisoned_evade"
MAX_STEPS = 60
ALTERNATIVES = 8
_PIECES = re.compile(r"([A-Za-z]+(?:'[a-z]+)?)")


class Surrogate:
    def __init__(self):
        self.tok = AutoTokenizer.from_pretrained(MODEL_DIR)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_DIR
        ).eval()

    def predict(self, texts):
        with torch.no_grad():
            enc = self.tok(
                texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            return self.model(**enc).logits.argmax(-1).tolist()


def units(original, adversarial):
    """Split both texts into aligned pieces; return (pieces, edits) where an edit is
    {index, original, current} for each replaced run."""
    a, b = _PIECES.split(original), _PIECES.split(adversarial)
    pieces, edits = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, a, b, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            pieces += a[i1:i2]
        else:
            edits.append(
                {
                    "index": len(pieces),
                    "original": "".join(a[i1:i2]),
                    "attack": "".join(b[j1:j2]),
                    "current": "".join(b[j1:j2]),
                    "state": "attack",
                }
            )
            pieces.append(None)
    return pieces, edits


def render(pieces, edits):
    out = list(pieces)
    for e in edits:
        out[e["index"]] = e["current"]
    return "".join(out)


def keep_case(word, like):
    return word.capitalize() if like[:1].isupper() else word


def section_chunks(path, section_text):
    """The pipeline's chunks of `path` that overlap `section_text`."""
    text = path.read_text(encoding="utf-8")
    start = text.index(section_text)
    end = start + len(section_text)
    chunks = split_documents(
        [Document(page_content=text, metadata={"source": str(path)})]
    )
    return [
        c.page_content
        for c in chunks
        if c.metadata["start_index"] < end
        and start < c.metadata["start_index"] + len(c.page_content)
    ]


def main():
    kb = OUT / "knowledge_base"
    if OUT.exists():
        raise FileExistsError(f"{OUT} already exists; outputs are create-only")
    shutil.copytree(SOURCE / "knowledge_base", kb)
    entries = [
        json.loads(line)
        for line in (SOURCE / "pwws_attack_manifest.jsonl").read_text().splitlines()
        if line.strip()
    ]
    surrogate, lm = Surrogate(), cf.language_model()
    cache = {}

    def verdict(chunk, name):
        key = (name, chunk)
        if key not in cache:
            cache[key] = cf.score_text(chunk, name, DomainReference(kb), lm)
        return cache[key]

    out_entries, log = [], (OUT / "evade_log.jsonl").open("a", encoding="utf-8")
    for entry in entries:
        if not entry.get("success"):
            out_entries.append(entry)
            continue
        path, name, label = kb / entry["file"], entry["file"], entry["label"]
        pieces, edits = units(entry["original_text"], entry["adversarial_text"])
        current = entry["adversarial_text"]
        assert render(pieces, edits) == current
        outcome, steps = None, []
        if surrogate.predict([current])[0] == label:
            outcome = "surrogate_not_fooled_at_start"
        for _ in range(MAX_STEPS):
            if outcome:
                break
            flagged = [
                v
                for v in (verdict(c, name) for c in section_chunks(path, current))
                if v["flagged"]
            ]
            if not flagged:
                outcome = "evades"
                break
            worst = max(flagged, key=lambda v: v["score_bits"])
            gaps = {t["word"]: t["gap_bits"] for t in worst["top_words"]}
            mine = [
                e
                for e in edits
                if e["state"] != "reverted" and e["current"].lower() in gaps
            ]
            if not mine:
                outcome = "flagged_on_words_the_attacker_did_not_introduce"
                break
            edit = max(mine, key=lambda e: gaps[e["current"].lower()])
            step = {"word": edit["current"], "gap_bits": gaps[edit["current"].lower()]}
            chosen = None
            if edit["state"] == "attack" and edit["original"].isalpha():
                reference = DomainReference(kb)
                options = sorted(
                    (
                        s
                        for s in synonyms(edit["original"].lower())
                        if s != edit["current"].lower()
                    ),
                    key=lambda s: -reference.probability(s, name),
                )[:ALTERNATIVES]
                trial_texts = []
                for s in options:
                    edit["current"] = keep_case(s, edit["original"])
                    trial_texts.append(render(pieces, edits))
                edit["current"] = step["word"]
                if options:
                    fooled = [
                        (s, t)
                        for s, t, p in zip(
                            options, trial_texts, surrogate.predict(trial_texts)
                        )
                        if p != label
                    ]
                    if fooled:
                        probs = lm.log2_prob([t for _, t in fooled])
                        chosen = max(zip(probs, fooled))[1][0]
            if chosen:
                edit["current"], edit["state"] = (
                    keep_case(chosen, edit["original"]),
                    "alternative",
                )
                step["action"] = f"alternative:{chosen}"
            else:
                edit["current"], edit["state"] = edit["original"], "reverted"
                step["action"] = "reverted"
            new = render(pieces, edits)
            path.write_text(
                path.read_text(encoding="utf-8").replace(current, new), encoding="utf-8"
            )
            current = new
            steps.append(step)
            if surrogate.predict([current])[0] == label:
                outcome = "surrogate_no_longer_fooled"
        outcome = outcome or "step_limit"
        kept = [e for e in edits if e["state"] != "reverted"]
        success = outcome == "evades" and bool(kept)
        if outcome == "evades" and not kept:
            outcome = "all_edits_removed"
        if not success:  # the attacker gives the section up: back to the clean text
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    current, entry["original_text"]
                ),
                encoding="utf-8",
            )
        record = {
            "file": name,
            "section": entry["section"],
            "outcome": outcome,
            "edits_by_pwws": len(edits),
            "edits_kept": len(kept) if success else 0,
            "edits_as_pwws_chose": sum(e["state"] == "attack" for e in kept)
            if success
            else 0,
            "steps": steps,
        }
        log.write(json.dumps(record) + "\n")
        log.flush()
        out_entries.append(
            {
                **{k: entry[k] for k in ("file", "attack_type", "section", "label")},
                "success": success,
                "result": outcome,
                **(
                    {
                        "original_text": entry["original_text"],
                        "adversarial_text": current,
                    }
                    if success
                    else {}
                ),
            }
        )
        print(
            f"{name} / {entry['section']}: {outcome} ({record['edits_kept']}/{len(edits)} edits kept)",
            flush=True,
        )
    with (OUT / "pwws_attack_manifest.jsonl").open("x", encoding="utf-8") as handle:
        handle.writelines(json.dumps(e) + "\n" for e in out_entries)
    print(
        f"evading sections: {sum(e['success'] for e in out_entries)} of "
        f"{sum(bool(e.get('success')) for e in entries)} that PWWS poisoned"
    )


if __name__ == "__main__":
    main()
