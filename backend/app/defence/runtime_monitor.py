"""Runtime verification monitor with feedback and memory."""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.defence.entropy_filter import DetectorUnavailable
from app.generation.prompt import RAG_PROMPT, SYSTEM_PROMPT

POLICY_VERSION = "runtime-monitor-v2"
POLICY_VERSION_CONTEXTUAL = "runtime-monitor-v3"  # blame="contextual"
STRICT_RESTORE_SUFFIX = (
    "+strict-restore"  # strict_restore=True (found by the CTL design check)
)
# V1: phi1 flagged any rare word outside the trusted vocabulary.
RARE_ZIPF = 3.5
MIN_WORD_LENGTH = 3
MAX_ROUNDS = 2
CANDIDATE_K = 10
KEEP = 3

BACKEND = Path(__file__).resolve().parents[2]
TRUSTED_FILES = {
    BACKEND
    / "data/external/stix-capec.json": "ee6244f48259c1963d0507535e1843d67ba08fe58b4dfe351c1b74f9e376fa69",
    BACKEND
    / "data/external/enterprise-attack.json": "fc783039f17fba646f79448f1322996457c658a9474f6d14c3bc924a2cf1c97d",
}
MAPPING_FILE = BACKEND / "app/kb_builder/source_mapping.yaml"

ABSTAIN = re.compile(  # the same refusal pattern the evaluation uses (analyse_defence.py)
    r"(does not|doesn't|do not) (provide|contain|mention|include|describe|specify)"
    r"|cannot (provide|answer|determine)|insufficient|not (enough|sufficient) information",
    re.IGNORECASE,
)
_TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")

FEEDBACK_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
Question:
{question}

Retrieved context:
{context}

Runtime monitor: a previous answer to this question was rejected.
Rejected answer:
<<<
{previous}
>>>
Violations: {violations}
Passages suspected of having been tampered with were removed from the context. Answer the
question again using only the retrieved context above, and do not repeat unsupported terms.
""".strip(),
        ),
    ]
)
WITHHELD = (
    "The runtime monitor withheld this answer: it uses terms that do not occur in the trusted "
    "MITRE reference, and the passages responsible could not be removed."
)


# ============================================================
# Text normalisation
# ============================================================


@lru_cache(maxsize=1)
def _wordnet():
    try:
        from nltk.corpus import wordnet

        wordnet.synsets("server")
        return wordnet
    except (ImportError, LookupError) as error:
        raise DetectorUnavailable(
            "WordNet data is required: python -m nltk.downloader wordnet"
        ) from error


@lru_cache(maxsize=1)
def _zipf() -> Callable[[str], float]:
    try:
        from wordfreq import zipf_frequency
    except ImportError as error:
        raise DetectorUnavailable(
            "wordfreq is required: pip install wordfreq"
        ) from error
    return lambda word: zipf_frequency(word, "en")


@lru_cache(maxsize=200_000)
def base_form(word: str) -> str:
    """Dictionary base form: plurals, verb forms and -ly adverbs map to one key."""
    word = word.split("'")[0]
    wn = _wordnet()
    for pos in ("n", "v", "a", "r"):
        found = wn.morphy(word, pos)
        if found:
            return found
    if word.endswith("ly") and len(word) > 4:
        stem = word[:-2]
        return wn.morphy(stem, "a") or stem
    return word


def words(text: str) -> list[str]:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text)).lower()
    return _TOKEN.findall(text)


def base_words(text: str) -> set[str]:
    return {base_form(w) for w in words(text)}


def rare_out_of_vocabulary(
    text: str, vocabulary: set[str], allowed: set[str] = frozenset()
) -> list[str]:
    """Rare words of `text` (Zipf < RARE_ZIPF) whose base form is in neither set."""
    zipf = _zipf()
    out = set()
    for w in words(text):
        if len(w) < MIN_WORD_LENGTH or zipf(w) >= RARE_ZIPF:
            continue
        b = base_form(w)
        if b not in vocabulary and b not in allowed and w not in vocabulary:
            out.add(w)
    return sorted(out)


# ============================================================
# Trusted reference
# ============================================================


def _check_hashes(files: dict[Path, str]) -> None:
    for path, expected in files.items():
        if not path.exists():
            raise DetectorUnavailable(f"trusted reference missing: {path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise DetectorUnavailable(
                f"trusted reference changed: {path.name} sha256 {actual}"
            )


def _stix_text(obj: dict[str, Any]) -> str:
    parts = [obj.get("name", "")]
    for key, value in obj.items():
        if key in (
            "name",
            "id",
            "type",
            "created",
            "modified",
            "spec_version",
            "created_by_ref",
        ):
            continue
        if (
            isinstance(value, str)
            and len(value) > 20
            and not value.startswith(("http", "identity--", "marking"))
        ):
            parts.append(value)
        elif (
            isinstance(value, list) and value and all(isinstance(v, str) for v in value)
        ):
            parts.extend(value)
        elif isinstance(value, dict):
            parts.extend(
                f"{k}: {', '.join(v) if isinstance(v, list) else v}"
                for k, v in value.items()
            )
    return "\n".join(html.unescape(re.sub(r"<[^>]+>", " ", p)) for p in parts if p)


class TrustedOntology:
    """Vocabulary and per-attack reference text from the pinned MITRE STIX bundles."""

    def __init__(
        self, files: dict[Path, str] | None = None, mapping_file: Path = MAPPING_FILE
    ):
        files = TRUSTED_FILES if files is None else files
        _check_hashes(files)
        self.files = {str(p): h for p, h in files.items()}
        self.vocabulary: set[str] = set()
        self.entries: dict[str, str] = {}
        for path in files:
            for obj in json.loads(Path(path).read_text(encoding="utf-8")).get(
                "objects", []
            ):
                if (
                    obj.get("type") not in ("attack-pattern", "course-of-action")
                    or obj.get("revoked")
                    or obj.get("x_mitre_deprecated")
                ):
                    continue
                text = _stix_text(obj)
                self.vocabulary |= base_words(text) | set(words(text))
                for key in obj:
                    self.vocabulary |= {
                        base_form(k)
                        for k in key.replace("x_capec_", "")
                        .replace("x_mitre_", "")
                        .split("_")
                        if k
                    }
                # hyphenated compounds also count when written as one word ("pre-computed" -> "precomputed")
                self.vocabulary |= {
                    m.replace("-", "")
                    for m in re.findall(r"[a-z]+(?:-[a-z]+)+", text.lower())
                }
                for ref in (
                    obj.get("external_references", [])
                    if obj["type"] == "attack-pattern"
                    else []
                ):
                    if ref.get("source_name") in ("capec", "mitre-attack") and ref.get(
                        "external_id"
                    ):
                        self.entries[ref["external_id"]] = text
        mapping = yaml.safe_load(mapping_file.read_text(encoding="utf-8"))["attacks"]
        self.attacks: dict[str, dict[str, Any]] = {}
        for key, spec in mapping.items():
            ids = [spec["primary_source"].get("id")] + [
                s if isinstance(s, str) else s.get("id")
                for s in spec.get("supporting_sources", [])
            ]
            self.attacks[key] = {
                "name": spec["display_name"],
                "ids": [i for i in ids if i and i in self.entries],
            }

    def attack_for(self, question: str, passages: list[Document] = ()) -> str | None:
        """The attack the question names; else the most common attack type among the passages."""
        q = question.lower()
        named = [k for k, a in self.attacks.items() if a["name"].lower() in q]
        if named:
            return max(named, key=lambda k: len(self.attacks[k]["name"]))
        types = [
            p.metadata.get("attack_type")
            for p in passages
            if p.metadata.get("attack_type") in self.attacks
        ]
        return max(set(types), key=types.count) if types else None

    def covers(self, attack: str | None) -> bool:
        return bool(attack and self.attacks.get(attack, {}).get("ids"))

    def reference(self, attack: str) -> tuple[str, str]:
        ids = self.attacks[attack]["ids"]
        return "+".join(ids), "\n\n".join(f"{i}: {self.entries[i]}" for i in ids)


@lru_cache(maxsize=1)
def trusted_ontology() -> TrustedOntology:
    return TrustedOntology()


# ============================================================
# Specifications
# ============================================================


@dataclass
class Violation:
    spec: str
    detail: str
    witnesses: list[str] = field(default_factory=list)


def abstains(answer: str) -> bool:
    return bool(ABSTAIN.search(answer or ""))


def check(
    answer: str,
    question: str,
    attack: str | None,
    ontology: TrustedOntology,
    context: list[str] | None = None,
) -> list[Violation]:
    """Check phi1 and phi2. `context` = the retrieved passages' text (v2); None reproduces v1."""
    violations = []
    oov = rare_out_of_vocabulary(
        answer, ontology.vocabulary, base_words(question) | set(words(question))
    )
    if context is not None:
        seen = set()
        for text in context:
            seen |= set(words(text)) | base_words(text)
        oov = [w for w in oov if w in seen or base_form(w) in seen]
    if oov:
        violations.append(
            Violation(
                "phi1_lexical",
                "the answer uses terms absent from the trusted MITRE reference: "
                + ", ".join(oov),
                oov,
            )
        )
    if abstains(answer) and ontology.covers(attack):
        violations.append(
            Violation(
                "phi2_availability",
                f"the answer declines although the trusted reference covers "
                f"{ontology.attacks[attack]['name']}; its evidence may have been displaced",
            )
        )
    return violations


def diagnose(
    violations: list[Violation], passages: list[Document], ontology: TrustedOntology
) -> dict[str, list[str]]:
    """Passage key -> suspicious words, for passages that explain the violations."""
    witnesses = {w for v in violations for w in v.witnesses}
    suspects = {}
    for doc in passages:
        oov = rare_out_of_vocabulary(doc.page_content, ontology.vocabulary)
        hit = sorted(set(oov) & witnesses) if witnesses else oov
        if hit:
            suspects[passage_key(doc)] = hit
    return suspects


def contextual_scorer(source_state: str) -> Callable[[Document], dict[str, Any]]:
    """Score a passage with the contextual synonym gap (same threshold as the contextual filter)."""
    from app.config import get_knowledge_base_path
    from app.defence import contextual_filter as cf
    from app.defence.entropy_filter import _relative_document, reference_for

    root = get_knowledge_base_path(source_state)
    reference = reference_for(str(root))

    def score(doc: Document) -> dict[str, Any]:
        name = _relative_document(doc.metadata.get("source", ""), root)
        key = (str(root), name, doc.page_content)
        if key not in cf._SCORE_CACHE:
            cf._SCORE_CACHE[key] = cf.score_text(doc.page_content, name, reference)
        return cf._SCORE_CACHE[key]

    return score


def diagnose_contextual(
    violations: list[Violation],
    passages: list[Document],
    scorer: Callable[[Document], dict[str, Any]],
) -> dict[str, list[str]]:
    """v3 blame: passages that contain a phi1 witness, or whose contextual synonym gap is flagged."""
    witnesses = {w for v in violations for w in v.witnesses}
    suspects = {}
    for doc in passages:
        seen = set(words(doc.page_content)) | base_words(doc.page_content)
        hit = sorted(w for w in witnesses if w in seen or base_form(w) in seen)
        verdict = scorer(doc)
        if verdict["flagged"]:
            hit += [
                f"{t['word']}<-{t['likely_original']}" for t in verdict["top_words"]
            ]
        if hit:
            suspects[passage_key(doc)] = hit
    return suspects


# ============================================================
# Memory
# ============================================================


def passage_key(doc: Document) -> str:
    raw = f"{doc.metadata.get('source', '')}\n{doc.metadata.get('start_index')}\n{doc.page_content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class QuarantineMemory:
    """Append-only JSONL of quarantined passages; survives restarts by re-reading the file."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.keys: set[str] = set()
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.keys.add(json.loads(line)["key"])

    def __contains__(self, key: str) -> bool:
        return key in self.keys

    def add(self, key: str, **details: Any) -> bool:
        if key in self.keys:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {"key": key, "at": time.time(), **details}, ensure_ascii=False
                )
                + "\n"
            )
        self.keys.add(key)
        return True


# ============================================================
# The monitored answer
# ============================================================


def _generate(
    question: str,
    results: list[tuple[Document, float]],
    llm_factory,
    feedback: dict | None,
) -> str:
    from app.generation.rag_chain import format_context

    context = format_context(results)
    if feedback is None:  # round 0: exactly the pipeline's prompt
        response = (RAG_PROMPT | llm_factory()).invoke(
            {"question": question, "context": context}
        )
    else:
        response = (FEEDBACK_PROMPT | llm_factory()).invoke(
            {"question": question, "context": context, **feedback}
        )
    return str(response.content)


def monitored_answer(
    question: str,
    source_state: str,
    *,
    memory: QuarantineMemory,
    llm_factory,
    mode: str = "verify",
    ontology: TrustedOntology | None = None,
    search_fn: Callable | None = None,
    capture: dict | None = None,
    blame: str = "rare_words",
    scorer: Callable[[Document], dict[str, Any]] | None = None,
    strict_restore: bool = False,
) -> dict[str, Any]:
    """Answer `question` from `source_state` under the runtime monitor. Returns answer and final sources.

    blame="rare_words" is policy v2 (default). blame="contextual" is v3: only the blame step differs.
    strict_restore=True closes two gaps of the restore step that the CTL design check found (both
    occur in the recorded runs): restore drops passages quarantined in the last round from its
    context (otherwise phi3 is violated), and a restored answer that violates phi1 is withheld
    like a draft (otherwise it is released). The default keeps the behaviour of the recorded runs.
    """
    if mode not in ("verify", "restore"):
        raise ValueError(f"unknown mode {mode}")
    if blame not in ("rare_words", "contextual"):
        raise ValueError(f"unknown blame {blame}")
    if blame == "contextual" and scorer is None:
        scorer = contextual_scorer(source_state)
    from app.generation.rag_chain import build_sources

    if search_fn is None:
        from app.retrieval.search import search_knowledge_base

        def search_fn(q, k):
            return search_knowledge_base(query=q, k=k, system_state=source_state)

    ontology = ontology or trusted_ontology()
    trace, feedback, answer, kept = [], None, None, []
    attack, violations = None, []
    for round_ in range(MAX_ROUNDS + 1):
        candidates = search_fn(question, CANDIDATE_K)
        kept = [(d, s) for d, s in candidates if passage_key(d) not in memory][:KEEP]
        skipped = sum(passage_key(d) in memory for d, _ in candidates)
        attack = attack or ontology.attack_for(question, [d for d, _ in candidates])
        answer = _generate(question, kept, llm_factory, feedback)
        violations = check(
            answer, question, attack, ontology, [d.page_content for d, _ in kept]
        )
        step = {
            "round": round_,
            "skipped_quarantined": skipped,
            "context_keys": [passage_key(d) for d, _ in kept],
            "answer": answer,
            "violations": [asdict(v) for v in violations],
        }
        trace.append(step)
        if not violations:
            break
        if blame == "contextual":
            suspects = diagnose_contextual(violations, [d for d, _ in kept], scorer)
        else:
            suspects = diagnose(violations, [d for d, _ in kept], ontology)
        added = [
            k
            for k, ws in suspects.items()
            if memory.add(
                k,
                question=question,
                round=round_,
                words=ws,
                specs=[v.spec for v in violations],
                source=next(
                    (d.metadata.get("source") for d, _ in kept if passage_key(d) == k),
                    None,
                ),
            )
        ]
        step["quarantined"] = added
        if not added or round_ == MAX_ROUNDS:
            break
        feedback = {
            "previous": answer,
            "violations": "; ".join(v.detail for v in violations),
        }

    outcome, final_sources = "released", kept
    if violations:
        lexical = any(v.spec == "phi1_lexical" for v in violations)
        if mode == "restore" and ontology.covers(attack) and not lexical:
            ids, text = ontology.reference(attack)
            trusted = Document(
                page_content=text,
                metadata={
                    "source": f"trusted-mitre:{ids}",
                    "start_index": 0,
                    "trusted_reference": True,
                },
            )
            if strict_restore:
                kept = [(d, s) for d, s in kept if passage_key(d) not in memory]
            final_sources = kept + [(trusted, 1.0)]
            answer = _generate(question, final_sources, llm_factory, None)
            violations = check(
                answer, question, attack, ontology, [d.page_content for d, _ in kept]
            )
            trace.append(
                {
                    "round": "restore",
                    "trusted_ids": ids,
                    "context_keys": [passage_key(d) for d, _ in kept],
                    "answer": answer,
                    "violations": [asdict(v) for v in violations],
                }
            )
            outcome = "restored"
            if strict_restore and any(v.spec == "phi1_lexical" for v in violations):
                answer, outcome = WITHHELD, "withheld"
        elif lexical:
            answer, outcome = WITHHELD, "withheld"
        else:
            outcome = "released_refusal"
    if capture is not None:
        capture.update(
            retrieval_status="ok",
            generation_status="ok",
            sources=build_sources(final_sources),
            monitor={
                "policy_version": (
                    POLICY_VERSION_CONTEXTUAL
                    if blame == "contextual"
                    else POLICY_VERSION
                )
                + (STRICT_RESTORE_SUFFIX if strict_restore else ""),
                "mode": mode,
                "attack": attack,
                "outcome": outcome,
                "rounds": trace,
                "generations": sum(1 for t in trace if "answer" in t),
                "final_violations": [asdict(v) for v in violations],
            },
        )
    return {
        "question": question,
        "answer": answer,
        "sources": build_sources(final_sources),
        "outcome": outcome,
    }
