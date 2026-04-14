"""Unified retrieval pipeline over MinHash, SimHash, and TF-IDF (Phase 3)."""

from __future__ import annotations

import json
import logging
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from sklearn.metrics.pairwise import linear_kernel

from config import settings
from indexing.index_manager import IndexManager, load_chunks
from indexing.minhash_lsh import (
    _ensure_stopwords_and_stemmer,
    _normalize_terms,
    build_minhash_signature,
    shingle_k_words,
)
from indexing.simhash import (
    hamming_distance,
    simhash_fingerprint,
    simhash_similarity,
    tokenize_terms,
    _ensure_stopwords,
)
from retrieval.reranker import fuse_scores, normalize_01

logger = logging.getLogger(__name__)

Method = Literal["minhash", "simhash", "tfidf", "all"]


@dataclass(frozen=True)
class RetrievedChunk:
    """One retrieved chunk with scores and highlight spans."""

    chunk_id: str
    text: str
    score: float
    pagerank_score: float
    final_score: float
    page_start: int
    page_end: int
    section_title: str
    highlight_spans: list[tuple[int, int]]


@dataclass(frozen=True)
class RetrievalResult:
    """Per-method retrieval result bundle (INSTRUCTIONS §3.1)."""

    method: str
    chunks: list[RetrievedChunk]
    latency_ms: float
    memory_delta_mb: float
    query: str
    fallback_to: str | None = None


def find_highlight_spans(text: str, query: str) -> list[tuple[int, int]]:
    """
    Find character spans for (lowercased) query terms in text (INSTRUCTIONS §3.1).

    Args:
        text: Chunk text.
        query: Raw query text.

    Returns:
        Sorted non-overlapping spans as (start, end) offsets.
    """

    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []
    text_lower = text.lower()
    spans: list[tuple[int, int]] = []
    for term in terms:
        start = 0
        while True:
            idx = text_lower.find(term, start)
            if idx == -1:
                break
            spans.append((idx, idx + len(term)))
            start = idx + 1
    if not spans:
        return []
    spans.sort()
    merged: list[tuple[int, int]] = []
    cur_s, cur_e = spans[0]
    for s, e in spans[1:]:
        if s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))
    return merged


class Retriever:
    """Retriever bound to in-memory indexes and corpus chunks."""

    def __init__(
        self,
        index_manager: IndexManager,
        chunks_path: Path | None = None,
    ) -> None:
        """
        Create a Retriever.

        Args:
            index_manager: Loaded index manager with artifacts in memory.
            chunks_path: Optional chunks.json path; defaults to settings.
        """

        self.mgr = index_manager
        self.chunks = load_chunks(chunks_path)
        self.chunk_by_id = {c.id: c for c in self.chunks}

        pr = (self.mgr.artifacts.pagerank.scores if self.mgr.artifacts.pagerank else {}) or {}
        self._pagerank_raw = {str(k): float(v) for k, v in pr.items()}
        if self._pagerank_raw:
            vals = list(self._pagerank_raw.values())
            self._pagerank_min = float(min(vals))
            self._pagerank_max = float(max(vals))
        else:
            self._pagerank_min = 0.0
            self._pagerank_max = 0.0

    def _pagerank_norm(self, chunk_id: str) -> float:
        """Return normalized PageRank score for a chunk_id in [0, 1]."""

        raw = float(self._pagerank_raw.get(chunk_id, 0.0))
        return normalize_01(raw, self._pagerank_min, self._pagerank_max)

    def retrieve(
        self,
        query: str,
        method: Method,
        k: int = 5,
        use_pagerank: bool = True,
        source_file: str | None = None,
    ) -> RetrievalResult:
        """
        Unified retrieval entrypoint (INSTRUCTIONS §3.1).

        Args:
            query: User query.
            method: Retrieval method.
            k: Top-k chunks to return.
            use_pagerank: Whether to fuse PageRank into final score.

        Returns:
            RetrievalResult.
        """

        if method == "minhash":
            return self._retrieve_minhash(
                query, k=k, use_pagerank=use_pagerank, source_file=source_file
            )
        if method == "simhash":
            return self._retrieve_simhash(
                query, k=k, use_pagerank=use_pagerank, source_file=source_file
            )
        if method == "tfidf":
            return self._retrieve_tfidf(
                query, k=k, use_pagerank=use_pagerank, source_file=source_file
            )
        raise ValueError(f"Unknown method: {method}")

    def _measure(self, fn):
        """Measure latency and peak tracemalloc memory for a callable."""

        tracemalloc.start()
        t0 = time.perf_counter()
        out = fn()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        _cur, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        mem_mb = float(peak) / 1024.0 / 1024.0
        return out, round(latency_ms, 4), round(mem_mb, 4)

    def _mk_chunk(
        self,
        chunk_id: str,
        score: float,
        use_pagerank: bool,
        query: str,
    ) -> RetrievedChunk:
        """Build RetrievedChunk from corpus metadata and scores."""

        c = self.chunk_by_id.get(chunk_id)
        if c is None:
            return RetrievedChunk(
                chunk_id=chunk_id,
                text="",
                score=float(score),
                pagerank_score=0.0,
                final_score=float(score),
                page_start=0,
                page_end=0,
                section_title="",
                highlight_spans=[],
            )
        pr = self._pagerank_norm(chunk_id) if use_pagerank else 0.0
        final = fuse_scores(float(score), pr) if use_pagerank else float(score)
        return RetrievedChunk(
            chunk_id=c.id,
            text=c.text,
            score=float(score),
            pagerank_score=pr,
            final_score=float(final),
            page_start=int(c.page_start),
            page_end=int(c.page_end),
            section_title=str(c.section_title or ""),
            highlight_spans=find_highlight_spans(c.text, query),
        )

    def _retrieve_minhash(
        self, query: str, k: int, use_pagerank: bool, source_file: str | None
    ) -> RetrievalResult:
        """MinHash+LSH retrieval with signature-based Jaccard rerank."""

        idx = self.mgr.artifacts.minhash
        if idx is None:
            raise RuntimeError("MinHash index not loaded")

        def _run():
            stop, stemmer = _ensure_stopwords_and_stemmer()
            terms = _normalize_terms(query, stop, stemmer)
            use_ub = bool(getattr(settings, "MINHASH_USE_UNIGRAMS_AND_BIGRAMS", False))
            if use_ub:
                # Keep consistent with indexing representation.
                shingles = set(terms) | {" ".join(terms[i : i + 2]) for i in range(0, max(0, len(terms) - 1))}
            else:
                shingles = shingle_k_words(
                    terms, k=int(getattr(settings, "MINHASH_SHINGLE_K_WORDS", 3))
                )
            qsig = build_minhash_signature(shingles, num_perm=settings.MINHASH_NUM_PERM)
            candidates = idx.lsh.query(qsig)
            if source_file:
                candidates = [
                    cid
                    for cid in candidates
                    if (self.chunk_by_id.get(str(cid)) is not None)
                    and (self.chunk_by_id[str(cid)].source_file == source_file)
                ]
            if not candidates:
                return [], "tfidf"
            # Two-stage reranking to control candidate explosion:
            # 1) preselect top-N candidates using signature-Jaccard estimate (cheap)
            # 2) exact-Jaccard rerank only that shortlist (more expensive)
            preselect_n = int(getattr(settings, "MINHASH_LSH_PRESELECT_TOP_N", 200))
            exact_n = int(getattr(settings, "MINHASH_EXACT_RERANK_TOP_N", 50))

            if preselect_n > 0 and len(candidates) > preselect_n:
                approx_scored: list[tuple[str, float]] = []
                for cid in candidates:
                    sig = idx.signatures.get(cid)
                    if sig is None:
                        continue
                    approx_scored.append((str(cid), float(qsig.jaccard(sig))))
                approx_scored.sort(key=lambda x: x[1], reverse=True)
                candidates = [cid for cid, _ in approx_scored[:preselect_n]]
            # Rerank LSH candidates by exact Jaccard on the actual representation.
            # This stays fully MinHash/set-based, but improves quality vs signature-only estimate.
            def _exact_jaccard(a: set[str], b: set[str]) -> float:
                if not a or not b:
                    return 0.0
                inter = len(a & b)
                union = len(a) + len(b) - inter
                return float(inter) / float(union) if union else 0.0

            scored: list[tuple[str, float]] = []
            for cid in candidates:
                cobj = self.chunk_by_id.get(str(cid))
                if cobj is None:
                    continue
                c_terms = _normalize_terms(cobj.text, stop, stemmer)
                if use_ub:
                    c_repr = set(c_terms) | {
                        " ".join(c_terms[i : i + 2]) for i in range(0, max(0, len(c_terms) - 1))
                    }
                else:
                    c_repr = shingle_k_words(
                        c_terms, k=int(getattr(settings, "MINHASH_SHINGLE_K_WORDS", 3))
                    )
                scored.append((str(cid), _exact_jaccard(shingles, c_repr)))
            scored.sort(key=lambda x: x[1], reverse=True)
            if exact_n > 0:
                scored = scored[:exact_n]
            return scored[:k], None

        (scored, fallback_to), latency_ms, mem_mb = self._measure(_run)

        chunks: list[RetrievedChunk] = []

        if fallback_to == "tfidf":
            tfidf_res = self._retrieve_tfidf(
                query, k=k, use_pagerank=use_pagerank, source_file=source_file
            )
            return RetrievalResult(
                method="minhash",
                chunks=tfidf_res.chunks,
                latency_ms=latency_ms + tfidf_res.latency_ms,
                memory_delta_mb=max(mem_mb, tfidf_res.memory_delta_mb),
                query=query,
                fallback_to="tfidf",
            )

        for cid, score in scored:
            chunks.append(
                self._mk_chunk(cid, score=score, use_pagerank=use_pagerank, query=query)
            )
        chunks.sort(key=lambda c: c.final_score, reverse=True)
        return RetrievalResult(
            method="minhash",
            chunks=chunks[:k],
            latency_ms=latency_ms,
            memory_delta_mb=mem_mb,
            query=query,
        )

    def _retrieve_simhash(
        self, query: str, k: int, use_pagerank: bool, source_file: str | None
    ) -> RetrievalResult:
        """SimHash retrieval via Hamming threshold + similarity rerank."""

        idx = self.mgr.artifacts.simhash
        if idx is None:
            raise RuntimeError("SimHash index not loaded")

        def _run():
            stop = _ensure_stopwords()
            q_terms = tokenize_terms(query, stop)
            q_fp = simhash_fingerprint(q_terms, idx.idf)

            scored: list[tuple[str, float]] = []
            thr = int(settings.SIMHASH_HAMMING_THRESHOLD)
            for cid, fp in idx.fingerprints.items():
                if source_file:
                    cobj = self.chunk_by_id.get(str(cid))
                    if cobj is None or cobj.source_file != source_file:
                        continue
                if hamming_distance(q_fp, fp) <= thr:
                    scored.append((cid, float(simhash_similarity(q_fp, fp))))
            if not scored:
                # Fallback: return closest fingerprints even if above threshold.
                for cid, fp in idx.fingerprints.items():
                    if source_file:
                        cobj = self.chunk_by_id.get(str(cid))
                        if cobj is None or cobj.source_file != source_file:
                            continue
                    scored.append((cid, float(simhash_similarity(q_fp, fp))))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:k]

        scored, latency_ms, mem_mb = self._measure(_run)
        chunks = [
            self._mk_chunk(cid, score=score, use_pagerank=use_pagerank, query=query)
            for cid, score in scored
        ]
        chunks.sort(key=lambda c: c.final_score, reverse=True)
        return RetrievalResult(
            method="simhash",
            chunks=chunks[:k],
            latency_ms=latency_ms,
            memory_delta_mb=mem_mb,
            query=query,
        )

    def _retrieve_tfidf(
        self, query: str, k: int, use_pagerank: bool, source_file: str | None
    ) -> RetrievalResult:
        """TF-IDF cosine similarity retrieval (baseline)."""

        idx = self.mgr.artifacts.tfidf
        if idx is None:
            raise RuntimeError("TF-IDF index not loaded")

        def _run():
            q_vec = idx.vectorizer.transform([query])
            # linear_kernel is efficient for sparse dot products.
            scores = linear_kernel(q_vec, idx.matrix).ravel()
            if scores.size == 0:
                return []
            if source_file:
                # Mask scores for chunks not from the selected PDF.
                mask = np.zeros(scores.shape, dtype=bool)
                for i, cid in enumerate(idx.chunk_ids):
                    cobj = self.chunk_by_id.get(str(cid))
                    if cobj is not None and cobj.source_file == source_file:
                        mask[i] = True
                scores = np.where(mask, scores, -1e9)
            top = np.argsort(scores)[::-1][: int(k)]
            out: list[tuple[str, float]] = []
            for i in top.tolist():
                cid = idx.chunk_ids[int(i)]
                out.append((cid, float(scores[int(i)])))
            # Normalize by the global max score so top-1 stays meaningful.
            max_s = float(scores.max()) if scores.size else 0.0
            if max_s > 0.0:
                out = [(cid, float(s) / max_s) for cid, s in out]
            return out

        scored, latency_ms, mem_mb = self._measure(_run)
        chunks = [
            self._mk_chunk(cid, score=score, use_pagerank=use_pagerank, query=query)
            for cid, score in scored
        ]
        chunks.sort(key=lambda c: c.final_score, reverse=True)
        return RetrievalResult(
            method="tfidf",
            chunks=chunks[:k],
            latency_ms=latency_ms,
            memory_delta_mb=mem_mb,
            query=query,
        )


def _load_retriever_from_app_state_fallback() -> Retriever:
    """
    Helper for scripts/tests: load manager + artifacts + chunks from disk.

    Returns:
        Retriever instance.
    """

    mgr = IndexManager()
    mgr.load_all()
    return Retriever(mgr)


def retrieve(
    query: str,
    method: Method,
    k: int = 5,
    use_pagerank: bool = True,
) -> RetrievalResult:
    """
    Convenience function matching the required signature (INSTRUCTIONS §3.1).

    Note: the FastAPI app uses a long-lived Retriever instance stored in app state.
    This function loads artifacts from disk when called directly.
    """

    r = _load_retriever_from_app_state_fallback()
    if method == "all":
        raise ValueError('Use the FastAPI endpoint for method="all" parallelism')
    return r.retrieve(query=query, method=method, k=k, use_pagerank=use_pagerank)


def load_chunks_lookup(path: Path | None = None) -> dict[str, int]:
    """
    Load ``chunks_lookup.json`` mapping chunk_id → index for O(1) lookup.

    Args:
        path: Optional path; defaults to settings.CHUNKS_DIR / "chunks_lookup.json".

    Returns:
        Mapping of chunk_id -> index.
    """

    p = path if path is not None else settings.CHUNKS_DIR / "chunks_lookup.json"
    if not p.exists():
        return {}
    return {str(k): int(v) for k, v in json.loads(p.read_text(encoding="utf-8")).items()}

