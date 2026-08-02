from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.generation.rag_chain import answer_question


app = FastAPI(
    title="Dissertation RAG API",
    description=(
        "A cybersecurity RAG system for investigating "
        "knowledge integrity and adversarial poisoning."
    ),
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        examples=["How can SQL injection be prevented?"],
    )


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict[str, Any]:
    try:
        return answer_question(request.question)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="The RAG pipeline failed to answer the question.",
        ) from error