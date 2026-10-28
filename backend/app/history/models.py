"""Pydantic request/response shapes for the Experiment History API."""

from typing import Any, Literal, Optional

from pydantic import BaseModel

ExperimentMode = Literal["clean", "poisoned", "compare", "defended"]


class ExperimentCreate(BaseModel):
    question: str
    mode: ExperimentMode
    attack_method: Optional[str] = None

    clean_answer: Optional[str] = None
    poisoned_answer: Optional[str] = None
    defended_answer: Optional[str] = None

    clean_sources: Optional[list[dict[str, Any]]] = None
    poisoned_sources: Optional[list[dict[str, Any]]] = None
    defended_sources: Optional[list[dict[str, Any]]] = None

    clean_top_score: Optional[float] = None
    poisoned_top_score: Optional[float] = None
    defended_top_score: Optional[float] = None

    retrieval_shift: Optional[float] = None
    top_k_overlap: Optional[float] = None
    top_score_delta: Optional[float] = None
    shared_chunks: Optional[int] = None
    answer_changed: Optional[bool] = None

    clean_latency: Optional[float] = None
    poisoned_latency: Optional[float] = None
    defended_latency: Optional[float] = None

    metadata: Optional[dict[str, Any]] = None

    research_metrics: Optional[dict[str, Any]] = None


class ExperimentRecord(ExperimentCreate):
    id: int
    timestamp: str


class ExperimentStats(BaseModel):
    total: int
    clean: int
    poisoned: int
    compare: int
    defended: int
    answer_changed: int
