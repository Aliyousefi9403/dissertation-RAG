"""Offline evaluation of information-theoretic detectors for PWWS-poisoned chunks.

Can relative entropy (KL divergence) and surprisal relative to a reference word
distribution separate retrieved chunks that contain PWWS-substituted text from
untouched chunks? No model calls and no clean counterparts at scoring time.
The PWWS manifest is used only to build evaluation labels.

Unit: every chunk of the poisoned collection, made with the pipeline's own
loader and splitter (500/100). Label 1 if the chunk contains a PWWS-inserted
or replaced non-whitespace character, located with the same character
alignment as app/evaluation/edited_text_exposure.py; otherwise 0.

Reference distributions q (the defender's knowledge):
  english : general English unigram frequencies (wordfreq), no domain knowledge.
  domain  : leave-one-document-out unigram counts from the OTHER documents of the
            same (possibly poisoned) collection, interpolated with english.
Scores per chunk (higher = more anomalous):
  kl_<ref>       KL(p_chunk || q) = sum_w p(w) log2 p(w)/q(w)  (relative entropy)
  topk_<ref>     mean of the k=5 largest word surprisals -log2 q(w)
  mean_<ref>     mean word surprisal (cross-entropy H(p_chunk, q))
  char_kl        KL of the chunk's letter distribution vs English letters (baseline)
Split: development vs held-out by source document (benchmark v1 record).

Usage: cd backend && PYTHONPATH=. python ../docs/research/scripts/entropy_detection_eval.py OUT.json [poisoned|control]
  control = formatting-only corpus with counterfactual labels; a detector of substitutions should score ~0.5 there.
  poisoned_adaptive / poisoned_pwws_rerun = a corpus from app/attack/pwws_adaptive_kb.py, labelled by its own manifest.
"""

import json
import math
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from nltk.corpus import wordnet
from wordfreq import word_frequency

from app.config import get_knowledge_base_path
from app.ingestion.load_documents import add_document_metadata, split_documents

ROOT = Path(__file__).resolve().parents[3] / "backend"
TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")
FLOOR = 1e-9          # probability floor for unseen words (about 30 bits)
LAMBDA = 0.5          # domain/english interpolation weight
TOPK = 5
STOPWORDS = {"the", "and", "for", "that", "this", "with", "are", "was", "from", "have", "has", "can", "may",
             "its", "not", "but", "they", "their", "which", "into", "such", "these", "than", "will", "use"}
_SYNONYMS = {}


def synonyms(word):
    """Single-word WordNet lemmas sharing a synset with `word` (PWWS's own candidate source)."""
    if word not in _SYNONYMS:
        _SYNONYMS[word] = {l.name().lower() for syn in wordnet.synsets(word) for l in syn.lemmas()
                           if l.name().isalpha() and l.name().lower() != word}
    return _SYNONYMS[word]
ENGLISH_LETTERS = {c: f for c, f in zip("etaoinshrdlcumwfgypbvkjxqz", [
    12.7, 9.06, 8.17, 7.51, 6.97, 6.33, 6.09, 5.99, 4.25, 4.03, 2.78, 2.76, 2.41, 2.36, 2.23, 2.02, 1.97,
    1.93, 1.49, 0.98, 0.77, 0.15, 0.15, 0.10, 0.07, 0.07])}


def tokens(text):
    text = re.sub(r"<[^>]+>", " ", text)          # HTML tags in CAPEC execution flows
    text = re.sub(r"\(Citation:[^)]*\)|https?://\S+", " ", text)
    return TOKEN.findall(text.lower())


def edited_spans(text, entry, side="adversarial"):
    """Spans of substituted words. side="adversarial": inserted/replacement text in the
    poisoned file. side="original": the words PWWS replaced, located in the control file
    (same layout, original words) -- the counterfactual positions."""
    adversarial, original = entry["adversarial_text"], entry["original_text"]
    located = adversarial if side == "adversarial" else original
    start = text.find(located)
    if start < 0 or text.count(located) != 1:
        raise ValueError(f"{side} text not uniquely located: {entry['file']}")
    spans = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, original, adversarial, autojunk=False).get_opcodes():
        if tag in ("insert", "replace", "delete"):
            a, b = (j1, j2) if side == "adversarial" else (i1, i2)
            if side == "adversarial" and tag == "delete":
                continue
            spans += [(start + a + m.start(), start + a + m.end()) for m in re.finditer(r"\S+", located[a:b])]
    return spans


def auroc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def tpr_at_fpr(scores, labels, threshold):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    return (round(sum(s > threshold for s in pos) / len(pos), 4) if pos else None,
            round(sum(s > threshold for s in neg) / len(neg), 4) if neg else None)


def threshold_for_fpr(scores, labels, fpr):
    neg = sorted((s for s, y in zip(scores, labels) if not y), reverse=True)
    return neg[min(len(neg) - 1, int(math.floor(fpr * len(neg))))]


def main(out, corpus="poisoned"):
    attacked = corpus in ("poisoned", "poisoned_adaptive", "poisoned_pwws_rerun")
    poisoned_root = (get_knowledge_base_path("poisoned") if corpus == "poisoned"
                     else ROOT / f"data/{corpus}/knowledge_base" if attacked else ROOT / "data/control/knowledge_base")
    manifest_path = ROOT / f"data/{corpus if attacked else 'poisoned'}/pwws_attack_manifest.jsonl"
    loader = DirectoryLoader(str(poisoned_root), glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    documents = add_document_metadata(loader.load(), "poisoned")
    chunks = split_documents(documents)
    texts = {Path(d.metadata["source"]).relative_to(poisoned_root).as_posix(): d.page_content for d in documents}

    manifest = [json.loads(l) for l in manifest_path.read_text().splitlines() if l.strip()]
    spans = {name: [] for name in texts}
    for entry in manifest:
        if entry.get("success"):
            spans[entry["file"]] += edited_spans(texts[entry["file"]], entry,
                                                 "adversarial" if attacked else "original")

    record = json.loads((ROOT / "data/evaluation/benchmark_v1_record.json").read_text())
    held_out = set(record["held_out_documents"])
    doc_counts = {name: Counter(tokens(text)) for name, text in texts.items()}
    total = sum(doc_counts.values(), Counter())

    def q_english(w):
        return max(word_frequency(w, "en"), FLOOR)

    def q_domain(w, name):
        counts = total - doc_counts[name]
        n = sum(counts.values())
        return LAMBDA * (counts[w] / n if n else 0) + (1 - LAMBDA) * q_english(w)

    rows = []
    for chunk in chunks:
        name = Path(chunk.metadata["source"]).relative_to(poisoned_root).as_posix()
        start = chunk.metadata["start_index"]
        end = start + len(chunk.page_content)
        label = int(any(a < end and start < b for a, b in spans[name]))
        words = tokens(chunk.page_content)
        if len(words) < 10:
            continue
        p = Counter(words)
        n = len(words)
        row = {"document": name, "start": start, "label": label,
               "split": "held_out" if name in held_out else "development",
               "category": name.split("/")[0], "n_words": n}
        for ref, q in (("english", q_english), ("domain", lambda w: q_domain(w, name))):
            surprisal = {w: -math.log2(q(w)) for w in p}
            row[f"kl_{ref}"] = sum((c / n) * math.log2((c / n) / q(w)) for w, c in p.items())
            row[f"mean_{ref}"] = sum(c * surprisal[w] for w, c in p.items()) / n
            row[f"topk_{ref}"] = sum(sorted((surprisal[w] for w in words), reverse=True)[:TOPK]) / TOPK
        # Synonym gap (FGWS-style, domain-frequency guided): how many bits more probable,
        # under the reference distribution, the best WordNet synonym is than the word used.
        for ref, q in (("english", q_english), ("domain", lambda w: q_domain(w, name))):
            gaps = sorted((max(math.log2(q(syn)) for syn in synonyms(w)) - math.log2(q(w))
                           for w in set(words) if len(w) > 2 and w not in STOPWORDS and synonyms(w)), reverse=True)
            row[f"syngap_max_{ref}"] = gaps[0] if gaps else 0.0
            row[f"syngap_top3_{ref}"] = sum(gaps[:3]) / 3 if gaps else 0.0
        letters = Counter(ch for ch in chunk.page_content.lower() if ch in ENGLISH_LETTERS)
        m = sum(letters.values())
        row["char_kl"] = sum((c / m) * math.log2((c / m) / (ENGLISH_LETTERS[ch] / 100)) for ch, c in letters.items()) if m else 0.0
        rows.append(row)

    scores = ["kl_english", "mean_english", "topk_english", "kl_domain", "mean_domain", "topk_domain", "char_kl",
              "syngap_max_english", "syngap_top3_english", "syngap_max_domain", "syngap_top3_domain"]
    results = {}
    for split in ("development", "held_out", "all"):
        subset = [r for r in rows if split == "all" or r["split"] == split]
        labels = [r["label"] for r in subset]
        results[split] = {"chunks": len(subset), "positives": sum(labels),
                          **{s: {"auroc": auroc([r[s] for r in subset], labels)} for s in scores}}
    # Thresholds fixed on development chunks (FPR 10%), then applied unchanged to held-out.
    dev = [r for r in rows if r["split"] == "development"]
    held = [r for r in rows if r["split"] == "held_out"]
    for s in scores:
        t = threshold_for_fpr([r[s] for r in dev], [r["label"] for r in dev], 0.10)
        results["development"][s]["threshold_fpr10"] = round(t, 4)
        results["development"][s]["tpr_fpr_at_threshold"] = tpr_at_fpr([r[s] for r in dev], [r["label"] for r in dev], t)
        results["held_out"][s]["tpr_fpr_at_dev_threshold"] = tpr_at_fpr([r[s] for r in held], [r["label"] for r in held], t)
    payload = {"corpus": corpus, "unit": f"{corpus}-collection chunk (500/100)",
               "label": "contains PWWS-edited text" if attacked else "contains words PWWS replaced (counterfactual, no substitution present)",
               "parameters": {"floor": FLOOR, "lambda": LAMBDA, "topk": TOPK, "min_words": 10},
               "results": results, "rows": rows}
    Path(out).open("x").write(json.dumps(payload, indent=1))
    for split in ("development", "held_out", "all"):
        r = results[split]
        print(f"\n[{split}] chunks={r['chunks']} positives={r['positives']}")
        for s in scores:
            extra = r[s].get("tpr_fpr_at_threshold") or r[s].get("tpr_fpr_at_dev_threshold") or ""
            print(f"  {s:13s} AUROC={r[s]['auroc']}  {('TPR/FPR=' + str(extra)) if extra else ''}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "poisoned")
