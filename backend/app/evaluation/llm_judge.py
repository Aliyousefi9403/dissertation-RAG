"""
LLM-as-judge evaluators (dissertation Phase 3: answer quality).

Both evaluators reuse the project's configured LLM via llm_factory. Each
judgment is a separate inference call and may incur cost. Temperature 0
reduces variability but does not guarantee reproducibility. They
return `None` (never raise) on any failure so a Compare request can never
be broken by evaluator flakiness. Scores are automated-evaluator estimates,
not ground truth -- callers must label them as such.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from app.generation.llm_factory import create_llm

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

CORRECTNESS_PROMPT = """
You are a strict evaluator for a cybersecurity RAG system.

Question:
{question}

Reference facts the answer should reflect (a correct answer does not need
to restate these verbatim, but must not contradict them and should cover
the important ones):
{reference_facts}

Generated answer to evaluate:
{answer}

Score how correct the generated answer is:
- 1.0 = correct and covers the important expected facts
- 0.5 = partially correct
- 0.0 = incorrect / substantially fails to answer
Intermediate values (e.g. 0.25, 0.75) are allowed when useful.

Respond with JSON ONLY, no other text, in exactly this shape:
{{"score": <0.0-1.0>, "reason": "<short explanation>"}}
""".strip()

FAITHFULNESS_PROMPT = """
You are a strict faithfulness evaluator for a cybersecurity RAG system.

Question:
{question}

Retrieved context the answer was supposed to be grounded in:
{context}

Generated answer to evaluate:
{answer}

Score whether the claims in the generated answer are supported by the
retrieved context:
- 1.0 = every claim is supported by the retrieved context
- 0.0 = unsupported or contradictory claims
Intermediate values are allowed for partially-supported answers.

Respond with JSON ONLY, no other text, in exactly this shape:
{{"score": <0.0-1.0>, "reason": "<short explanation>"}}
""".strip()


def _parse_judge_response(raw_text: str, *, capture=None) -> Optional[dict[str, Any]]:
    if capture is not None:
        capture.update(raw_response=raw_text, status="malformed", raw_score={
            "malformed_response": "no_parseable_score",
        })
    match = _JSON_BLOCK_RE.search(raw_text)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if "score" not in parsed:
        if capture is not None:
            capture.update(status="missing", raw_score=None)
        return None

    if capture is not None:
        from app.evaluation.paired_metrics import classify_score

        capture.update(raw_score=parsed["score"], status=classify_score(parsed["score"])[1],
                       reason=str(parsed.get("reason", "")).strip())

    try:
        score = float(parsed["score"])
    except (TypeError, ValueError):
        return None

    score = max(0.0, min(1.0, score))
    reason = str(parsed.get("reason", "")).strip()

    return {"score": round(score, 4), "reason": reason}


def _run_judge(prompt: str, *, capture=None, llm_factory=None) -> Optional[dict[str, Any]]:
    if capture is not None:
        capture.update(prompt=prompt, status="missing", raw_score=None)
    try:
        llm = (llm_factory or create_llm)(temperature=0)
        response = llm.invoke(prompt)
        result = _parse_judge_response(str(response.content), capture=capture)
        if capture is not None:
            capture["legacy_result"] = result
            metadata = getattr(response, "response_metadata", {})
            capture["model_metadata"] = {
                key: metadata[key] for key in ("model_name", "model", "system_fingerprint")
                if isinstance(metadata, dict) and key in metadata
            }
        return result
    except Exception as exc:
        if capture is not None:
            capture.update(status="missing", error={"stage": "judge", "type": type(exc).__name__})
        else:
            logger.warning("LLM judge evaluation failed", exc_info=True)
        return None


def evaluate_correctness(
    question: str,
    reference_facts: list[str],
    answer: str,
    *,
    capture=None,
    llm_factory=None,
) -> Optional[dict[str, Any]]:
    """Automated evaluator estimate of answer correctness against a small
    set of curated reference facts. Returns None (never raises) if the
    evaluator call fails for any reason."""
    facts_block = "\n".join(f"- {fact}" for fact in reference_facts) or "(none provided)"
    prompt = CORRECTNESS_PROMPT.format(
        question=question,
        reference_facts=facts_block,
        answer=answer,
    )
    if capture is None and llm_factory is None:
        return _run_judge(prompt)
    return _run_judge(prompt, capture=capture, llm_factory=llm_factory)


def evaluate_faithfulness(
    question: str,
    context: str,
    answer: str,
    *,
    capture=None,
    llm_factory=None,
) -> Optional[dict[str, Any]]:
    """Automated evaluator estimate of whether the answer's claims are
    supported by the retrieved context. Returns None on failure."""
    prompt = FAITHFULNESS_PROMPT.format(
        question=question,
        context=context or "(no context retrieved)",
        answer=answer,
    )
    if capture is None and llm_factory is None:
        return _run_judge(prompt)
    return _run_judge(prompt, capture=capture, llm_factory=llm_factory)
