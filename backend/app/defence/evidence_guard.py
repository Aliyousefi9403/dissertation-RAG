"""
Experimental evidence-support check for RAG answers (detection batch 1).

Flow for one guarded request:

1. Draft an answer with the *unchanged* baseline pipeline
   (`app.generation.rag_chain.answer_question`: same prompt, retrieval depth,
   embeddings, model and temperature). Only a request timeout and a bounded
   retry count are added to the model client for this route.
2. Ask a separate verifier call to split the draft into claims and judge each
   one against the retrieved sources only.
3. Validate the verifier output strictly, including that every quotation
   really appears in the source it is attributed to.
4. Apply the versioned release policy below and write a create-only audit
   record.

What this is NOT:

* Not proof of truth. "Supported" only means the retrieved text says so; a
  poisoned source can support a false answer.
* Not proof that the corpus is unpoisoned.
* Not a calibrated confidence. No percentages are produced.

The verifier never receives reference answers, clean counterparts or attack
labels -- only the question, the draft and the retrieved chunk text.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import unicodedata
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# Versioned experimental policy
# ============================================================

POLICY_VERSION = "evidence-guard-policy-v2"
AUDIT_SCHEMA_VERSION = 1

EXPERIMENT_LABEL = (
    "Experimental evidence-support baseline. Not a validated poison "
    "detector: a poisoned source can support a false answer."
)

POLICY_DESCRIPTION = (
    "Release the draft only if the verifier returned at least one claim and "
    "every claim is 'supported' with at least one quotation that was found "
    "verbatim in a cited retrieved source. Withhold the draft if any claim "
    "is 'contradicted' or 'unsupported'. Missing evidence, failed or "
    "malformed verification, fabricated quotations or zero checkable claims "
    "are 'unavailable' and are never treated as a pass. v2: a draft that only "
    "declines to answer because the sources are insufficient is 'abstained' "
    "and is released as a refusal, provided none of its claims is "
    "contradicted, unsupported or unverifiable; quotation matching ignores "
    "leading/trailing punctuation."
)

VERDICTS = ("supported", "unsupported", "contradicted")
OUTCOMES = ("supported", "unsupported", "contradicted", "unavailable", "abstained")

# Bounded, explicit model-call settings for THIS route only. Existing
# callers of `create_llm()` keep their defaults.
DRAFT_TIMEOUT_SECONDS = float(os.getenv("GUARD_DRAFT_TIMEOUT_SECONDS", "30"))
VERIFIER_TIMEOUT_SECONDS = float(os.getenv("GUARD_VERIFIER_TIMEOUT_SECONDS", "45"))
MODEL_MAX_RETRIES = int(os.getenv("GUARD_MODEL_MAX_RETRIES", "1"))
VERIFIER_TEMPERATURE = 0.0

MAX_CLAIMS = 25
MIN_QUOTE_CHARS = 12
MAX_QUOTE_CHARS = 400

DEFAULT_AUDIT_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "evidence_guard_audit"
)


def get_audit_dir() -> Path:
    override = os.getenv("GUARD_AUDIT_DIR")
    return Path(override) if override else DEFAULT_AUDIT_DIR


# ============================================================
# Verifier prompt
# ============================================================

VERIFIER_PROMPT = """
You are a strict evidence checker for a cybersecurity question-answering
system. You do NOT decide what is true in the world. You only decide whether
each claim in a draft answer is stated by the retrieved sources below.

Question:
{question}

Draft answer to check:
<<<DRAFT
{draft}
DRAFT>>>

Retrieved sources (the ONLY evidence you may use):
{sources}

Instructions:
1. Split the draft into its distinct factual claims. Ignore citation markers
   such as [Source 1] and greetings. Statements that the context or sources
   are insufficient, or that the draft cannot answer, are NOT claims.
   Do not invent claims that the draft does not make.
   Set "abstention" to true if the draft declines to answer the question
   because the sources are insufficient, otherwise false.
2. For each claim choose exactly one verdict:
   - "supported": a source explicitly states it.
   - "contradicted": a source explicitly states something incompatible.
   - "unsupported": no source states it (even if you believe it is true).
3. For "supported" and "contradicted" claims, give the source IDs and copy
   one or more short quotations EXACTLY, character for character, from those
   sources (12-400 characters each). Never paraphrase inside a quotation.
4. Use only the source IDs listed above (S1, S2, ...).

Respond with JSON ONLY, no prose and no code fences, in exactly this shape:
{{"abstention": false, "claims": [{{"claim": "<claim text>", "verdict": "supported|unsupported|contradicted", "source_ids": ["S1"], "quotes": [{{"source_id": "S1", "text": "<exact quotation>"}}], "explanation": "<one sentence>"}}]}}
""".strip()


def source_id_for(source_number: int) -> str:
    return f"S{source_number}"


def format_sources_for_verifier(sources: list[dict[str, Any]]) -> str:
    # Only the neutral ID and chunk text: file paths (e.g. data/poisoned/...)
    # and metadata (attack_type, origin, ...) would leak experiment labels.
    return "\n\n".join(
        f"[{source_id_for(source['source_number'])}]\n{source.get('content', '')}"
        for source in sources
    )


def build_verifier_prompt(
    question: str,
    draft: str,
    sources: list[dict[str, Any]],
) -> str:
    return VERIFIER_PROMPT.format(
        question=question,
        draft=draft,
        sources=format_sources_for_verifier(sources),
    )


# ============================================================
# Strict verifier-output validation
# ============================================================


class VerifierOutputError(ValueError):
    """The verifier response does not match the required schema."""


_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return " ".join(text.split()).casefold()


_QUOTE_EDGE_CHARS = " \t\n.,;:!?\"'()[]{}-\u2026"


def quote_in_source(quote: str, source_text: str) -> bool:
    # Words must still match verbatim; only punctuation at the quotation's
    # edges is ignored (verifiers often add a closing full stop).
    needle = _normalise(quote).strip(_QUOTE_EDGE_CHARS)
    return len(needle) >= MIN_QUOTE_CHARS and needle in _normalise(source_text)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifierOutputError(message)


def parse_verifier_output(
    raw_text: str,
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Claims only; see `parse_verification` for the abstention flag."""
    return parse_verification(raw_text, sources)[1]


def parse_verification(
    raw_text: str,
    sources: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """
    Parse and validate the verifier's JSON. Raises VerifierOutputError for any
    structural problem (whole response unusable). Per-claim evidence problems
    (unknown source, quotation not found) do not raise; they downgrade that
    claim to "unavailable" with a reason, so they can never count as a pass.
    """

    text = raw_text.strip()
    fenced = _FENCE_RE.match(text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise VerifierOutputError(f"not valid JSON ({error.msg})") from error

    _require(isinstance(payload, dict), "top level must be a JSON object")
    _require(
        set(payload) == {"claims", "abstention"},
        "top level must contain exactly 'abstention' and 'claims'",
    )
    _require(isinstance(payload["abstention"], bool), "'abstention' must be a boolean")
    claims = payload["claims"]
    _require(isinstance(claims, list), "'claims' must be a list")
    _require(len(claims) <= MAX_CLAIMS, f"more than {MAX_CLAIMS} claims")

    content_by_id = {
        source_id_for(source["source_number"]): source.get("content", "")
        for source in sources
    }

    findings = []
    for index, item in enumerate(claims):
        where = f"claims[{index}]"
        _require(isinstance(item, dict), f"{where} must be an object")
        claim = item.get("claim")
        verdict = item.get("verdict")
        source_ids = item.get("source_ids", [])
        quotes = item.get("quotes", [])
        explanation = item.get("explanation", "")

        _require(
            isinstance(claim, str) and claim.strip() != "",
            f"{where}.claim must be a non-empty string",
        )
        _require(verdict in VERDICTS, f"{where}.verdict must be one of {VERDICTS}")
        _require(
            isinstance(source_ids, list)
            and all(isinstance(s, str) for s in source_ids),
            f"{where}.source_ids must be a list of strings",
        )
        _require(isinstance(quotes, list), f"{where}.quotes must be a list")
        _require(isinstance(explanation, str), f"{where}.explanation must be a string")

        checked_quotes = []
        for q_index, quote in enumerate(quotes):
            _require(
                isinstance(quote, dict)
                and isinstance(quote.get("source_id"), str)
                and isinstance(quote.get("text"), str),
                f"{where}.quotes[{q_index}] must have string source_id and text",
            )
            quote_source = quote["source_id"]
            quote_text = quote["text"]
            known = quote_source in content_by_id
            verified = (
                known
                and quote_source in source_ids
                and len(quote_text) <= MAX_QUOTE_CHARS
                and quote_in_source(quote_text, content_by_id[quote_source])
            )
            checked_quotes.append(
                {"source_id": quote_source, "text": quote_text, "verified": verified}
            )

        status = verdict
        problems = []
        unknown_ids = [s for s in source_ids if s not in content_by_id]
        if unknown_ids:
            problems.append(f"cites unknown source IDs {unknown_ids}")
        if verdict in ("supported", "contradicted"):
            if not source_ids:
                problems.append(f"'{verdict}' verdict gives no source IDs")
            if not checked_quotes:
                problems.append(f"'{verdict}' verdict gives no quotation")
            elif not all(q["verified"] for q in checked_quotes):
                problems.append(
                    "a quotation was not found verbatim in the cited source"
                )
        if problems:
            status = "unavailable"

        findings.append(
            {
                "claim": claim.strip(),
                "verifier_verdict": verdict,
                "status": status,
                "source_ids": source_ids,
                "quotes": checked_quotes,
                "explanation": explanation.strip(),
                "problems": problems,
            }
        )

    return payload["abstention"], findings


# ============================================================
# Release decision
# ============================================================


@dataclass(frozen=True)
class Decision:
    outcome: str
    released: bool
    reason: str


def decide(
    *,
    sources: list[dict[str, Any]],
    findings: list[dict[str, Any]] | None,
    failure_stage: str | None = None,
    abstention: bool = False,
) -> Decision:
    if failure_stage == "retrieval":
        return Decision(
            "unavailable",
            False,
            "Retrieval failed, so there is no evidence to check against.",
        )
    if not sources:
        return Decision(
            "unavailable",
            False,
            "No evidence was retrieved, so the answer cannot be checked.",
        )
    if failure_stage == "generation":
        return Decision(
            "unavailable", False, "The draft answer could not be generated."
        )
    if failure_stage == "verification" or findings is None:
        return Decision(
            "unavailable",
            False,
            "The evidence check could not be completed, so the draft is withheld.",
        )
    statuses = [finding["status"] for finding in findings]
    count = lambda status: statuses.count(status)  # noqa: E731

    if abstention and not (
        count("contradicted") or count("unsupported") or count("unavailable")
    ):
        return Decision(
            "abstained",
            True,
            "The draft declines to answer because the retrieved sources are "
            "insufficient; it is released as a refusal, not as an answer.",
        )
    if not findings:
        return Decision(
            "unavailable", False, "The verifier found no checkable claims in the draft."
        )

    if count("contradicted"):
        return Decision(
            "contradicted",
            False,
            f"{count('contradicted')} claim(s) are contradicted by the retrieved sources.",
        )
    if count("unsupported"):
        return Decision(
            "unsupported",
            False,
            f"{count('unsupported')} claim(s) are not stated in the retrieved sources.",
        )
    if count("unavailable"):
        return Decision(
            "unavailable",
            False,
            f"{count('unavailable')} claim(s) could not be tied to verified quotations.",
        )
    return Decision(
        "supported",
        True,
        f"All {len(findings)} claim(s) are stated in the retrieved sources. "
        "This does not show the sources themselves are correct or unpoisoned.",
    )


# ============================================================
# Model clients for this route only
# ============================================================


def guarded_model_settings() -> dict[str, Any]:
    from app import config

    return {
        "provider": config.LLM_PROVIDER,
        "model": config.LLM_MODEL,
        "draft_temperature": config.LLM_TEMPERATURE,
        "verifier_temperature": VERIFIER_TEMPERATURE,
        "draft_timeout_seconds": DRAFT_TIMEOUT_SECONDS,
        "verifier_timeout_seconds": VERIFIER_TIMEOUT_SECONDS,
        "max_retries": MODEL_MAX_RETRIES,
        "embedding_model": config.EMBEDDING_MODEL,
        "retrieval_top_k": config.RETRIEVAL_TOP_K,
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
    }


def create_guarded_llm(*, temperature: float, timeout: float):
    """Same provider/model/key as `create_llm`, plus explicit timeout and
    bounded retries. Does not change `create_llm` or its callers."""
    from langchain_openai import ChatOpenAI

    from app import config

    if config.LLM_PROVIDER.lower() != "openai":
        raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}.")
    if not config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is missing.")

    return ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=config.LLM_API_KEY,
        temperature=temperature,
        timeout=timeout,
        max_retries=MODEL_MAX_RETRIES,
    )


def _default_draft_llm():
    from app import config

    return create_guarded_llm(
        temperature=config.LLM_TEMPERATURE, timeout=DRAFT_TIMEOUT_SECONDS
    )


def _default_verifier_llm():
    return create_guarded_llm(
        temperature=VERIFIER_TEMPERATURE, timeout=VERIFIER_TIMEOUT_SECONDS
    )


def _default_answer_fn(*args, **kwargs):
    from app.generation.rag_chain import answer_question

    return answer_question(*args, **kwargs)


def _default_retrieval_fn(question: str, system_state: str):
    from app.generation.rag_chain import retrieve_documents

    return retrieve_documents(question, system_state=system_state)


# ============================================================
# Audit recording (create-only, never stores credentials)
# ============================================================

_SECRET_PATTERNS = [re.compile(r"sk-[A-Za-z0-9_\-]{16,}")]


def _redact(text: str) -> str:
    from app import config

    if config.LLM_API_KEY:
        text = text.replace(config.LLM_API_KEY, "[REDACTED]")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def write_audit_record(record: dict[str, Any], audit_dir: Path) -> Path:
    """Write `record` to `<audit_dir>/<run_id>.json` without ever replacing an
    existing file. Content is written to a temporary exclusive file first and
    then hard-linked into place, so a crash never leaves a partial record
    under the final name."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    final_path = audit_dir / f"{record['run_id']}.json"
    temp_path = audit_dir / f".{record['run_id']}.{uuid.uuid4().hex}.tmp"
    data = _redact(json.dumps(record, indent=2, ensure_ascii=False, default=str))

    fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_path, final_path)  # FileExistsError if the run ID exists
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
    return final_path


# ============================================================
# Orchestration
# ============================================================


def _failure(stage: str, error: BaseException) -> dict[str, Any]:
    name = type(error).__name__
    is_timeout = isinstance(error, TimeoutError) or "timeout" in name.lower()
    return {
        "stage": stage,
        "type": name,
        "timeout": is_timeout,
        "detail": _redact(str(error))[:300],
    }


def _new_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex}"


def run_guarded_chat(
    question: str,
    system_state: str,
    *,
    answer_fn: Callable[..., dict[str, Any]] | None = None,
    retrieval_fn: Callable[..., Any] | None = None,
    draft_llm_factory: Callable[[], Any] | None = None,
    verifier_llm_factory: Callable[[], Any] | None = None,
    audit_dir: Path | None = None,
    audit_writer: Callable[[dict[str, Any], Path], Path] = write_audit_record,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    question = (question or "").strip()
    if not question:
        raise ValueError("Question cannot be empty.")
    if system_state not in ("clean", "poisoned"):
        raise ValueError(
            "Evidence check supports the 'clean' and 'poisoned' states only."
        )

    run_id = _new_run_id()
    started = time.perf_counter()
    timings: dict[str, float | None] = {
        "retrieval_ms": None,
        "draft_ms": None,
        "verification_ms": None,
        "total_ms": None,
    }
    failures: list[dict[str, Any]] = []
    capture: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    draft: str | None = None
    failure_stage: str | None = None

    base_retrieval = retrieval_fn or _default_retrieval_fn

    def timed_retrieval(q: str, system_state: str):
        t0 = time.perf_counter()
        try:
            return base_retrieval(q, system_state=system_state)
        finally:
            timings["retrieval_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # ---- 1. Draft with the unchanged baseline pipeline ----------------
    draft_started = time.perf_counter()
    try:
        result = (answer_fn or _default_answer_fn)(
            question,
            system_state=system_state,
            capture=capture,
            llm_factory=draft_llm_factory or _default_draft_llm,
            retrieval_fn=timed_retrieval,
        )
        sources = result.get("sources", [])
        draft = result.get("answer")
    except Exception as error:
        failure_stage = (
            "retrieval" if capture.get("retrieval_status") != "ok" else "generation"
        )
        failures.append(_failure(failure_stage, error))
        sources = capture.get("sources", []) or []
    timings["draft_ms"] = round(
        (time.perf_counter() - draft_started) * 1000 - (timings["retrieval_ms"] or 0), 1
    )

    # ---- 2. Independent verifier call --------------------------------
    verifier_prompt: str | None = None
    raw_verifier: str | None = None
    verifier_metadata: dict[str, Any] = {}
    findings: list[dict[str, Any]] | None = None
    abstention = False
    verifier_status = "not_run"

    if failure_stage is None and sources and draft:
        verifier_prompt = build_verifier_prompt(question, draft, sources)
        verify_started = time.perf_counter()
        try:
            llm = (verifier_llm_factory or _default_verifier_llm)()
            response = llm.invoke(verifier_prompt)
            raw_verifier = str(response.content)
            metadata = getattr(response, "response_metadata", {}) or {}
            if isinstance(metadata, dict):
                verifier_metadata = {
                    key: metadata[key]
                    for key in ("model_name", "model", "system_fingerprint")
                    if key in metadata
                }
            abstention, findings = parse_verification(raw_verifier, sources)
            verifier_status = "ok"
        except VerifierOutputError as error:
            failure_stage = "verification"
            verifier_status = "malformed"
            failures.append(_failure("verification", error))
        except Exception as error:
            failure_stage = "verification"
            verifier_status = "failed"
            failures.append(_failure("verification", error))
        timings["verification_ms"] = round(
            (time.perf_counter() - verify_started) * 1000, 1
        )

    # ---- 3. Policy ----------------------------------------------------
    decision = decide(
        sources=sources,
        findings=findings,
        failure_stage=failure_stage,
        abstention=abstention,
    )
    timings["total_ms"] = round((time.perf_counter() - started) * 1000, 1)

    if settings is None:
        try:
            settings = guarded_model_settings()
        except Exception as error:  # configuration problems are recorded, not fatal
            settings = {"unavailable": type(error).__name__}

    record = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "policy_version": POLICY_VERSION,
        "policy": POLICY_DESCRIPTION,
        "label": EXPERIMENT_LABEL,
        "question": question,
        "system_state": system_state,
        "retrieved_evidence": [
            {"source_id": source_id_for(s["source_number"]), **s} for s in sources
        ],
        "draft": {
            "answer": draft,
            "generation_status": capture.get("generation_status"),
            "model_metadata": capture.get("model_metadata", {}),
        },
        "verifier": {
            "status": verifier_status,
            "prompt": verifier_prompt,
            "raw_response": raw_verifier,
            "abstention": abstention,
            "model_metadata": verifier_metadata,
        },
        "findings": findings,
        "decision": {
            "outcome": decision.outcome,
            "released": decision.released,
            "reason": decision.reason,
        },
        "settings": settings,
        "timings_ms": timings,
        "failures": failures,
    }

    target_dir = audit_dir or get_audit_dir()
    audit: dict[str, Any] = {
        "saved": False,
        "run_id": run_id,
        "location": None,
        "error": None,
    }
    try:
        path = audit_writer(record, target_dir)
        audit.update(saved=True, location=str(path))
    except Exception as error:
        audit["error"] = f"{type(error).__name__}: audit record was NOT saved"
        logger.error(
            "Evidence-guard audit write failed for run %s", run_id, exc_info=True
        )

    return {
        "run_id": run_id,
        "question": question,
        "system_state": system_state,
        "policy_version": POLICY_VERSION,
        "label": EXPERIMENT_LABEL,
        "outcome": decision.outcome,
        "decision": "released" if decision.released else "withheld",
        "answer": draft if decision.released else None,
        "explanation": decision.reason,
        "claims": [
            {
                key: f[key]
                for key in (
                    "claim",
                    "status",
                    "verifier_verdict",
                    "source_ids",
                    "quotes",
                    "explanation",
                    "problems",
                )
            }
            for f in (findings or [])
        ],
        "sources": [
            {"source_id": source_id_for(s["source_number"]), **s} for s in sources
        ],
        "failures": [{k: f[k] for k in ("stage", "type", "timeout")} for f in failures],
        "audit": audit,
        "timings_ms": timings,
    }
