"""`POST /guarded-chat`: experimental evidence-checked answers."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.defence import evidence_guard

router = APIRouter(tags=["evidence-check (experimental)"])


class GuardedChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    system_state: Literal["clean", "poisoned"] = "clean"


class QuoteResponse(BaseModel):
    source_id: str
    text: str
    verified: bool


class ClaimResponse(BaseModel):
    claim: str
    status: Literal["supported", "unsupported", "contradicted", "unavailable"]
    verifier_verdict: Literal["supported", "unsupported", "contradicted"]
    source_ids: list[str]
    quotes: list[QuoteResponse]
    explanation: str
    problems: list[str]


class GuardedSourceResponse(BaseModel):
    source_id: str
    source_number: int
    source: str
    score: float
    content: str
    metadata: dict[str, Any]


class FailureResponse(BaseModel):
    stage: str
    type: str
    timeout: bool


class AuditResponse(BaseModel):
    saved: bool
    run_id: str
    location: str | None
    error: str | None


class GuardedChatResponse(BaseModel):
    run_id: str
    question: str
    system_state: Literal["clean", "poisoned"]
    policy_version: str
    label: str
    outcome: Literal[
        "supported", "unsupported", "contradicted", "unavailable", "abstained"
    ]
    decision: Literal["released", "withheld"]
    answer: str | None
    explanation: str
    claims: list[ClaimResponse]
    sources: list[GuardedSourceResponse]
    failures: list[FailureResponse]
    audit: AuditResponse
    timings_ms: dict[str, float | None]


@router.post("/guarded-chat", response_model=GuardedChatResponse)
def guarded_chat(request: GuardedChatRequest) -> dict[str, Any]:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        return evidence_guard.run_guarded_chat(question, request.system_state)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="The evidence-checked request failed unexpectedly.",
        ) from error
