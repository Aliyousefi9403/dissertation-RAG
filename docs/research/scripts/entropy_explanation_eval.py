"""Do the entropy filter's explanations point at real PWWS substitutions?

For each chunk that contains PWWS-edited text and is flagged by
app.defence.entropy_filter, check whether its top-3 evidence words include a
word PWWS actually substituted, and whether the suggested `likely_original` is
the exact word PWWS replaced. Offline; manifest used only for scoring.

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/entropy_explanation_eval.py OUT.json
"""

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader

from app.config import get_knowledge_base_path
from app.defence import entropy_filter as ef
from app.ingestion.load_documents import add_document_metadata, split_documents

ROOT = Path(__file__).resolve().parents[3]


def main(out):
    root = get_knowledge_base_path("poisoned")
    loader = DirectoryLoader(str(root), glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    chunks = {(Path(c.metadata["source"]).relative_to(root).as_posix(), c.metadata["start_index"]): c.page_content
              for c in split_documents(add_document_metadata(loader.load(), "poisoned"))}
    rows = json.loads((ROOT / "docs/research/results/entropy-detector-20261016/detector-poisoned.json").read_text())["rows"]
    substitutions = {}
    for line in (ROOT / "backend/data/poisoned/pwws_attack_manifest.jsonl").read_text().splitlines():
        entry = json.loads(line)
        if not entry.get("success"):
            continue
        original, adversarial = entry["original_text"].split(), entry["adversarial_text"].split()
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, original, adversarial, autojunk=False).get_opcodes():
            if tag == "replace" and i2 - i1 == j2 - j1:
                for o, a in zip(original[i1:i2], adversarial[j1:j2]):
                    o, a = re.sub(r"[^a-z]", "", o.lower()), re.sub(r"[^a-z]", "", a.lower())
                    if o and a and o != a:
                        substitutions.setdefault(entry["file"], {}).setdefault(a, set()).add(o)
    reference = ef.reference_for(str(root))
    results = []
    for row in rows:
        if not row["label"]:
            continue
        verdict = ef.score_text(chunks[(row["document"], row["start"])], row["document"], reference)
        subs = substitutions.get(row["document"], {})
        hits = [w for w in verdict["top_words"] if w["word"] in subs]
        exact = [w for w in hits if w["likely_original"] in subs[w["word"]]]
        results.append({"document": row["document"], "start": row["start"], "flagged": verdict["flagged"],
                        "score_bits": verdict["score_bits"], "top_words": verdict["top_words"],
                        "evidence_is_substitution": bool(hits), "names_exact_original": bool(exact)})
    flagged = [r for r in results if r["flagged"]]
    summary = {"edited_chunks": len(results), "flagged_edited_chunks": len(flagged),
               "evidence_includes_real_substitution": sum(r["evidence_is_substitution"] for r in flagged),
               "explanation_names_exact_original": sum(r["names_exact_original"] for r in flagged)}
    Path(out).open("x").write(json.dumps({"summary": summary, "chunks": results}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
