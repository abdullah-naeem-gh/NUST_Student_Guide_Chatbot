"""Query endpoint: run retrieval methods and return structured results (Phase 3)."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from generation import generate_answer
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
        fallback_to=("tfidf" if res.fallback_to == "tfidf" else None),
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
            asyncio.to_thread(r.retrieve, query, "minhash", k, use_pr, payload.source_file),
            asyncio.to_thread(r.retrieve, query, "simhash", k, use_pr, payload.source_file),
            asyncio.to_thread(r.retrieve, query, "tfidf", k, use_pr, payload.source_file),
        ]
        minhash_res, simhash_res, tfidf_res = await asyncio.gather(*tasks)
        results = {
            "minhash": _as_method_result(minhash_res),
            "simhash": _as_method_result(simhash_res),
            "tfidf": _as_method_result(tfidf_res),
        }
    else:
        res = await asyncio.to_thread(
            r.retrieve, query, payload.method, k, use_pr, payload.source_file
        )
        mr = _as_method_result(res)
        results = {
            "minhash": MethodResultModel(),
            "simhash": MethodResultModel(),
            "tfidf": MethodResultModel(),
        }
        results[str(payload.method)] = mr  # type: ignore[index]

    answer = ""
    cited_chunks: list[str] = []

    if payload.generate_answer:
        # Prefer TF-IDF chunks for generation (most stable/precise baseline),
        # falling back to a merged list if TF-IDF returns nothing.
        top_chunks = list(results["tfidf"].chunks)[:k]
        if not top_chunks:
            # Combine all retrieved chunks, dedupe by chunk_id, then pick the best-k by final_score.
            merged: dict[str, RetrievedChunkModel] = {}
            for method_bundle in results.values():
                for c in method_bundle.chunks:
                    prev = merged.get(c.chunk_id)
                    if prev is None or c.final_score > prev.final_score:
                        merged[c.chunk_id] = c
            top_chunks = sorted(merged.values(), key=lambda c: c.final_score, reverse=True)[
                :k
            ]

        # Guardrail: if evidence looks weak/noisy, avoid generating a confident answer.
        # (Still allow the model to respond "not enough info" if it wants, but ensure
        # we don't pass completely junk excerpts.)
        def _text_quality(t: str) -> float:
            letters = sum(ch.isalpha() for ch in t)
            return letters / max(1, len(t))

        top_chunks = [c for c in top_chunks if _text_quality(c.text) >= 0.25]
        if not top_chunks:
            answer = "I don't have enough clean handbook evidence to answer that from the current index."
            cited_chunks = []
            return QueryResponse(
                query=query,
                answer=answer,
                cited_chunks=cited_chunks,
                results=results,  # type: ignore[arg-type]
            )

        gen = await asyncio.to_thread(
            generate_answer, query, top_chunks, payload.llm_model
        )
        answer = gen.answer
        cited_chunks = list(gen.cited_chunk_ids)

    return QueryResponse(
        query=query,
        answer=answer,
        cited_chunks=cited_chunks,
        results=results,  # type: ignore[arg-type]
    )

