import logging
import time
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import KNOWLEDGE_BASE_PATHS
from app.defence.router import router as evidence_guard_router
from app.evaluation.compare_metrics import build_research_metrics
from app.evaluation.source_identity import (
    CYBERSECURITY_DATASET_NAMESPACE,
    build_document_overlap,
)
from app.generation.rag_chain import answer_question
from app.history import service as history_service
from app.history.models import ExperimentCreate, ExperimentRecord, ExperimentStats

logger = logging.getLogger(__name__)


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="AegisRAG API",
    description=(
        "Knowledge integrity platform for evaluating clean, "
        "poisoned, and defended Retrieval-Augmented Generation systems."
    ),
    version="0.1.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://192.168.1.104:3000",
        "http://192.168.1.104:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Experimental evidence-check route (POST /guarded-chat); see app/defence/.
app.include_router(evidence_guard_router)


# ============================================================
# Request / Response models
# ============================================================

class ChatRequest(BaseModel):
    question: str
    system_state: Literal[
        "clean",
        "poisoned",
        "defended",
    ] = "clean"


class SourceResponse(BaseModel):
    source_number: int
    source: str
    score: float
    content: str
    metadata: dict[str, Any]


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceResponse]
    system_state: str


class CompareRequest(BaseModel):
    question: str


class CompareResponse(BaseModel):
    question: str
    clean: dict[str, Any]
    poisoned: dict[str, Any]
    metrics: dict[str, Any]
    # Research-quality metric groups (see app/evaluation/compare_metrics.py).
    # Optional/nullable: evaluator or ground-truth lookups can legitimately
    # fail without breaking the response the user is waiting on.
    attack_quality: Optional[dict[str, Any]] = None
    retrieval_quality: Optional[dict[str, Any]] = None
    generation_quality: Optional[dict[str, Any]] = None
    attack_success: Optional[dict[str, Any]] = None


# ============================================================
# Utility functions for experiment comparison
# ============================================================

def _source_identity(source: dict[str, Any]) -> str:
    """
    Produce a stable identity for a retrieved chunk.

    We use:
        source file + start index

    This is more accurate than comparing attack_type alone,
    because multiple retrieved chunks may come from the same document.
    """

    metadata = source.get("metadata", {}) or {}

    source_path = (
        source.get("source")
        or metadata.get("source")
        or "unknown"
    )

    start_index = metadata.get(
        "start_index",
        "unknown",
    )

    return f"{source_path}::{start_index}"


def _attack_type(source: dict[str, Any]) -> str:
    """
    Extract attack type from returned source metadata.
    """

    metadata = source.get("metadata", {}) or {}

    return (
        metadata.get("attack_type")
        or source.get("attack_type")
        or "unknown"
    )


def _scores(
    sources: list[dict[str, Any]],
) -> list[float]:

    values = []

    for source in sources:
        try:
            values.append(
                float(source.get("score", 0.0))
            )
        except (TypeError, ValueError):
            values.append(0.0)

    return values


def _record_chat_history(
    result: dict[str, Any],
    system_state: str,
    latency_ms: float,
) -> None:
    """
    Auto-record a successful CLEAN or POISONED /chat answer as one
    Experiment History row. Never raises -- a persistence failure must
    not break the chat response the user is waiting on.
    """

    try:
        sources = result.get("sources", [])
        top_score = _scores(sources)[0] if sources else None

        fields: dict[str, Any] = {
            "question": result["question"],
            "mode": system_state,
        }

        if system_state == "clean":
            fields["clean_answer"] = result.get("answer")
            fields["clean_sources"] = sources
            fields["clean_top_score"] = top_score
            fields["clean_latency"] = latency_ms
        elif system_state == "poisoned":
            fields["poisoned_answer"] = result.get("answer")
            fields["poisoned_sources"] = sources
            fields["poisoned_top_score"] = top_score
            fields["poisoned_latency"] = latency_ms
        else:
            fields["defended_answer"] = result.get("answer")
            fields["defended_sources"] = sources
            fields["defended_top_score"] = top_score
            fields["defended_latency"] = latency_ms

        history_service.save_experiment(ExperimentCreate(**fields))

    except Exception:
        logger.warning(
            "Failed to record chat history (system_state=%s)",
            system_state,
            exc_info=True,
        )


# ============================================================
# Health endpoint
# ============================================================

@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }


# ============================================================
# Normal RAG chat endpoint
# ============================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
) -> dict[str, Any]:

    try:
        started_at = time.perf_counter()
        result = answer_question(
            request.question,
            system_state=request.system_state,
        )
        latency_ms = (time.perf_counter() - started_at) * 1000

        _record_chat_history(result, request.system_state, latency_ms)

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "The RAG pipeline failed "
                "to answer the question."
            ),
        ) from error


# ============================================================
# Clean vs PWWS-poisoned comparison endpoint
# ============================================================

@app.post(
    "/compare",
    response_model=CompareResponse,
)
def compare_states(
    request: CompareRequest,
) -> dict[str, Any]:

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        # ----------------------------------------------------
        # Run EXACTLY the same question against clean RAG
        # ----------------------------------------------------

        clean_started_at = time.perf_counter()
        clean = answer_question(
            question,
            system_state="clean",
        )
        clean_latency_ms = (time.perf_counter() - clean_started_at) * 1000

        # ----------------------------------------------------
        # Run EXACTLY the same question against PWWS KB
        # ----------------------------------------------------

        poisoned_started_at = time.perf_counter()
        poisoned = answer_question(
            question,
            system_state="poisoned",
        )
        poisoned_latency_ms = (time.perf_counter() - poisoned_started_at) * 1000

        clean_sources = clean.get(
            "sources",
            [],
        )

        poisoned_sources = poisoned.get(
            "sources",
            [],
        )

        # ----------------------------------------------------
        # Identify exact retrieved chunks
        # ----------------------------------------------------

        clean_ids = [
            _source_identity(source)
            for source in clean_sources
        ]

        poisoned_ids = [
            _source_identity(source)
            for source in poisoned_sources
        ]

        clean_set = set(clean_ids)
        poisoned_set = set(poisoned_ids)

        intersection = (
            clean_set & poisoned_set
        )

        union = (
            clean_set | poisoned_set
        )

        # Jaccard overlap
        if union:
            top_k_overlap = (
                len(intersection)
                / len(union)
            )
        else:
            top_k_overlap = 1.0

        retrieval_shift = (
            1.0 - top_k_overlap
        )

        # ----------------------------------------------------
        # Retrieval scores
        # ----------------------------------------------------

        clean_scores = _scores(
            clean_sources
        )

        poisoned_scores = _scores(
            poisoned_sources
        )

        clean_top_score = (
            clean_scores[0]
            if clean_scores
            else 0.0
        )

        poisoned_top_score = (
            poisoned_scores[0]
            if poisoned_scores
            else 0.0
        )

        top_score_delta = (
            poisoned_top_score
            - clean_top_score
        )

        # ----------------------------------------------------
        # Attack types appearing in retrieval
        # ----------------------------------------------------

        clean_attack_types = [
            _attack_type(source)
            for source in clean_sources
        ]

        poisoned_attack_types = [
            _attack_type(source)
            for source in poisoned_sources
        ]

        # ----------------------------------------------------
        # Answer comparison
        # ----------------------------------------------------

        clean_answer = (
            clean.get("answer", "")
            .strip()
        )

        poisoned_answer = (
            poisoned.get("answer", "")
            .strip()
        )

        answer_changed = (
            clean_answer
            != poisoned_answer
        )

        # ----------------------------------------------------
        # Metrics returned to frontend
        # ----------------------------------------------------

        metrics = {
            "attack_method": "PWWS",

            "top_k": max(
                len(clean_sources),
                len(poisoned_sources),
            ),

            "top_k_overlap": round(
                top_k_overlap,
                4,
            ),

            "retrieval_shift": round(
                retrieval_shift,
                4,
            ),

            "clean_top_score": round(
                clean_top_score,
                4,
            ),

            "poisoned_top_score": round(
                poisoned_top_score,
                4,
            ),

            "top_score_delta": round(
                top_score_delta,
                4,
            ),

            "answer_changed": answer_changed,

            "shared_chunks": len(
                intersection
            ),

            "clean_source_ids": clean_ids,

            "poisoned_source_ids": (
                poisoned_ids
            ),

            "clean_attack_types": (
                clean_attack_types
            ),

            "poisoned_attack_types": (
                poisoned_attack_types
            ),
        }

        # Add document overlap independently of the legacy path/offset
        # metrics above. It is not retrieval correctness or chunk alignment.
        metrics["document_overlap"] = build_document_overlap(
            clean_sources,
            poisoned_sources,
            corpus_roots={
                root: CYBERSECURITY_DATASET_NAMESPACE
                for root in KNOWLEDGE_BASE_PATHS.values()
            },
        )

        # ----------------------------------------------------
        # Research-quality metrics (attack/retrieval/generation
        # quality + RAG attack success). Never allowed to break the
        # Compare response -- a failure here just means these groups
        # come back null, exactly like a failed evaluator call.
        # ----------------------------------------------------

        research_metrics: dict[str, Any] = {
            "attack_quality": None,
            "retrieval_quality": None,
            "generation_quality": None,
            "attack_success": None,
        }

        try:
            research_metrics = build_research_metrics(
                question=question,
                clean_answer=clean_answer,
                poisoned_answer=poisoned_answer,
                clean_sources=clean_sources,
                poisoned_sources=poisoned_sources,
            )
        except Exception:
            logger.warning("Failed to compute research metrics", exc_info=True)

        try:
            history_service.save_experiment(
                ExperimentCreate(
                    question=question,
                    mode="compare",
                    attack_method="PWWS",
                    clean_answer=clean.get("answer"),
                    poisoned_answer=poisoned.get("answer"),
                    clean_sources=clean_sources,
                    poisoned_sources=poisoned_sources,
                    clean_top_score=clean_top_score,
                    poisoned_top_score=poisoned_top_score,
                    retrieval_shift=metrics["retrieval_shift"],
                    top_k_overlap=metrics["top_k_overlap"],
                    top_score_delta=metrics["top_score_delta"],
                    shared_chunks=metrics["shared_chunks"],
                    answer_changed=answer_changed,
                    clean_latency=clean_latency_ms,
                    poisoned_latency=poisoned_latency_ms,
                    research_metrics=research_metrics,
                )
            )
        except Exception:
            logger.warning("Failed to record compare history", exc_info=True)

        return {
            "question": question,
            "clean": clean,
            "poisoned": poisoned,
            "metrics": metrics,
            **research_metrics,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Comparison failed: "
                f"{error}"
            ),
        ) from error


# ============================================================
# Experiment History endpoints
# ============================================================

@app.post(
    "/history",
    response_model=ExperimentRecord,
)
def create_history_entry(
    payload: ExperimentCreate,
) -> ExperimentRecord:
    return history_service.save_experiment(payload)


@app.get(
    "/history/stats",
    response_model=ExperimentStats,
)
def history_stats() -> ExperimentStats:
    return history_service.get_stats()


@app.get(
    "/history",
    response_model=list[ExperimentRecord],
)
def list_history(
    mode: Optional[str] = None,
    attack_method: Optional[str] = None,
    answer_changed: Optional[bool] = None,
    limit: int = 50,
) -> list[ExperimentRecord]:
    return history_service.list_experiments(
        mode=mode,
        attack_method=attack_method,
        answer_changed=answer_changed,
        limit=limit,
    )


@app.get(
    "/history/{experiment_id}",
    response_model=ExperimentRecord,
)
def get_history_entry(
    experiment_id: int,
) -> ExperimentRecord:
    record = history_service.get_experiment(experiment_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found.",
        )

    return record


@app.delete("/history/{experiment_id}")
def delete_history_entry(
    experiment_id: int,
) -> dict[str, bool]:
    deleted = history_service.delete_experiment(experiment_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found.",
        )

    return {"deleted": True}