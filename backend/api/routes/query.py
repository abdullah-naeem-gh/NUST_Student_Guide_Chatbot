"""Query endpoint: run retrieval methods and return structured results (Phase 3)."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from retrieval.models import MethodResultModel, QueryRequest, QueryResponse, RetrievedChunkModel
from retrieval.retriever import Retriever, RetrievalResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


def _as_method_result(res: RetrievalResult) -> MethodResultModel:
    """Convert internal RetrievalResult dataclass to API model."""

    return MethodResultModel(
        chunks=[
            RetrievedChunkModel(
                chunk_id=c.chunk_id,
                text=c.text,
                score=float(c.score),
                pagerank_score=float(c.pagerank_score),
                final_score=float(c.final_score),
                page_start=int(c.page_start),
                page_end=int(c.page_end),
                section_title=str(c.section_title or ""),
                highlight_spans=list(c.highlight_spans),
            )
            for c in res.chunks
        ],
        latency_ms=float(res.latency_ms),
        memory_mb=float(res.memory_delta_mb),
        fallback_to=(str(res.fallback_to) if res.fallback_to else None),
    )


def _get_retriever(request: Request) -> Retriever:
    """Fetch the long-lived Retriever from app state or raise 503."""

    retriever = getattr(request.app.state, "retriever", None)
    if retriever is None:
        raise HTTPException(status_code=503, detail="Index not ready")
    return retriever


@router.post("/", response_model=QueryResponse)
async def run_query(payload: QueryRequest, request: Request) -> QueryResponse:
    """
    Run one or all retrieval methods and return top-k chunks (INSTRUCTIONS §6).

    Args:
        payload: QueryRequest including method and k.
        request: FastAPI request (used to access app state retriever).

    Returns:
        QueryResponse with per-method retrieval bundles.
    """

    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must be non-empty")

    r = _get_retriever(request)
    k = int(payload.k)
    use_pr = bool(payload.use_pagerank)

    if payload.method == "all":
        tasks = [
            asyncio.to_thread(r.retrieve, query, "minhash", k, use_pr),
            asyncio.to_thread(r.retrieve, query, "simhash", k, use_pr),
            asyncio.to_thread(r.retrieve, query, "tfidf", k, use_pr),
        ]
        minhash_res, simhash_res, tfidf_res = await asyncio.gather(*tasks)
        results = {
            "minhash": _as_method_result(minhash_res),
            "simhash": _as_method_result(simhash_res),
            "tfidf": _as_method_result(tfidf_res),
        }
    else:
        res = await asyncio.to_thread(r.retrieve, query, payload.method, k, use_pr)
        mr = _as_method_result(res)
        results = {
            "minhash": MethodResultModel(),
            "simhash": MethodResultModel(),
            "tfidf": MethodResultModel(),
        }
        results[str(payload.method)] = mr  # type: ignore[index]

    # Phase 4 will populate answer + citations. Keep fields stable now.
    return QueryResponse(
        query=query,
        answer="",
        cited_chunks=[],
        results=results,  # type: ignore[arg-type]
    )

