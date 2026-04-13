"""Pydantic schemas for retrieval and query API (Phase 3)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RetrievalMethod = Literal["minhash", "simhash", "tfidf", "all"]


class QueryRequest(BaseModel):
    """Request model for POST /query (INSTRUCTIONS §6)."""

    query: str = Field(..., min_length=1)
    method: RetrievalMethod = "all"
    k: int = Field(default=5, ge=1, le=50)
    use_pagerank: bool = True
    generate_answer: bool = False


class RetrievedChunkModel(BaseModel):
    """A single retrieved chunk with scores and highlight spans."""

    chunk_id: str
    text: str
    score: float
    pagerank_score: float = 0.0
    final_score: float
    page_start: int
    page_end: int
    section_title: str = ""
    highlight_spans: list[tuple[int, int]] = Field(default_factory=list)


class MethodResultModel(BaseModel):
    """Per-method retrieval result bundle returned inside QueryResponse."""

    chunks: list[RetrievedChunkModel] = Field(default_factory=list)
    latency_ms: float = 0.0
    memory_mb: float = 0.0
    fallback_to: Literal["tfidf"] | None = None


class QueryResponse(BaseModel):
    """Response model for POST /query (Phase 3)."""

    query: str
    answer: str = ""
    cited_chunks: list[str] = Field(default_factory=list)
    results: dict[Literal["minhash", "simhash", "tfidf"], MethodResultModel]

