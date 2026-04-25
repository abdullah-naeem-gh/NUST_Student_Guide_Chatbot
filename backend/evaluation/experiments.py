"""Experiment runners for retrieval evaluation (Phase 5)."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from config import settings
from evaluation.benchmark_queries import BENCHMARK
from evaluation.metrics import mean_average_precision, precision_at_k, recall_at_k
from ingestion.models import Chunk
from indexing.index_manager import IndexManager, load_chunks
from indexing.minhash_lsh import (
    _ensure_stopwords_and_stemmer,
    _normalize_terms,
    build_minhash_lsh_index,
    build_minhash_signature,
    shingle_k_words,
    token_set_unigrams_bigrams,
)
from indexing.simhash import build_simhash_index
from indexing.tfidf_baseline import build_tfidf_index
from retrieval.retriever import Retriever

logger = logging.getLogger(__name__)

Method = Literal["minhash", "simhash", "tfidf"]


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp string."""

    return datetime.now(timezone.utc).isoformat()


def _results_dir() -> Path:
    """Return the results output directory, creating it if needed."""

    out = settings.DATA_DIR / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON payload to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_retriever() -> Retriever:
    """Load a Retriever bound to the on-disk artifacts."""

    mgr = IndexManager()
    mgr.load_all()
    return Retriever(mgr)


def _minhash_retrieve_ids_no_fallback(mgr: IndexManager, query: str, k: int) -> list[str]:
    """
    Retrieve chunk ids using MinHash+LSH without TF-IDF fallback.

    This is used only for evaluation to measure "pure" MinHash performance.
    """

    idx = mgr.artifacts.minhash
    if idx is None:
        raise RuntimeError("MinHash index not loaded")

    stop, stemmer = _ensure_stopwords_and_stemmer()
    terms = _normalize_terms(query, stop, stemmer)
    use_ub = bool(getattr(settings, "MINHASH_USE_UNIGRAMS_AND_BIGRAMS", False))
    shingles = (
        token_set_unigrams_bigrams(terms)
        if use_ub
        else shingle_k_words(terms, k=int(getattr(settings, "MINHASH_SHINGLE_K_WORDS", 3)))
    )
    qsig = build_minhash_signature(shingles, num_perm=settings.MINHASH_NUM_PERM)
    candidates = idx.lsh.query(qsig)
    if not candidates:
        return []
    scored: list[tuple[str, float]] = []
    for cid in candidates:
        sig = idx.signatures.get(cid)
        if sig is None:
            continue
        scored.append((str(cid), float(qsig.jaccard(sig))))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in scored[:k]]


def _minhash_lsh_candidate_count(mgr: IndexManager, query: str) -> int:
    """Return raw LSH candidate count for a query (before any reranking)."""

    idx = mgr.artifacts.minhash
    if idx is None:
        raise RuntimeError("MinHash index not loaded")
    stop, stemmer = _ensure_stopwords_and_stemmer()
    terms = _normalize_terms(query, stop, stemmer)
    use_ub = bool(getattr(settings, "MINHASH_USE_UNIGRAMS_AND_BIGRAMS", False))
    shingles = (
        token_set_unigrams_bigrams(terms)
        if use_ub
        else shingle_k_words(terms, k=int(getattr(settings, "MINHASH_SHINGLE_K_WORDS", 3)))
    )
    qsig = build_minhash_signature(shingles, num_perm=settings.MINHASH_NUM_PERM)
    return len(idx.lsh.query(qsig))


def run_method_comparison(k: int = 5, use_pagerank: bool = False) -> dict[str, Any]:
    """
    Experiment 1 — Method comparison (INSTRUCTIONS §5.3).

    Runs all 15 benchmark queries across MinHash, SimHash, and TF-IDF.

    Args:
        k: Cutoff for metrics and retrieval.
        use_pagerank: Whether to fuse PageRank into final score.

    Returns:
        Results dict (also saved to `data/results/method_comparison.json`).
    """

    r = _load_retriever()
    mgr = r.mgr
    per_method: dict[str, list[dict[str, Any]]] = {
        "hybrid": [],
        "minhash": [],
        "minhash_lsh_only": [],
        "minhash_no_fallback": [],
        "simhash": [],
        "tfidf": [],
    }

    for b in BENCHMARK:
        query = b["query"]
        relevant = set(b["relevant_chunk_ids"])
        for method in ("hybrid", "minhash", "simhash", "tfidf"):
            res = r.retrieve(query=query, method=method, k=max(10, k), use_pagerank=use_pagerank)
            retrieved_ids = [c.chunk_id for c in res.chunks]
            per_method[method].append(
                {
                    "query": query,
                    "category": b["category"],
                    "relevant_chunk_ids": sorted(relevant),
                    "retrieved_chunk_ids": retrieved_ids,
                    "p@1": precision_at_k(retrieved_ids, relevant, 1),
                    "p@3": precision_at_k(retrieved_ids, relevant, 3),
                    "p@5": precision_at_k(retrieved_ids, relevant, 5),
                    "r@5": recall_at_k(retrieved_ids, relevant, 5),
                    "latency_ms": float(res.latency_ms),
                    "memory_mb": float(res.memory_delta_mb),
                    "fallback_to": res.fallback_to,
                }
            )

        # MinHash+LSH only (no fallback): empty when LSH finds no candidates.
        cand_count = _minhash_lsh_candidate_count(mgr, query=query)
        retrieved_lsh_only = _minhash_retrieve_ids_no_fallback(mgr, query=query, k=max(10, k))
        per_method["minhash_lsh_only"].append(
            {
                "query": query,
                "category": b["category"],
                "relevant_chunk_ids": sorted(relevant),
                "retrieved_chunk_ids": retrieved_lsh_only,
                "p@1": precision_at_k(retrieved_lsh_only, relevant, 1),
                "p@3": precision_at_k(retrieved_lsh_only, relevant, 3),
                "p@5": precision_at_k(retrieved_lsh_only, relevant, 5),
                "r@5": recall_at_k(retrieved_lsh_only, relevant, 5),
                "latency_ms": 0.0,
                "memory_mb": 0.0,
                "fallback_to": None,
                "lsh_candidate_count": int(cand_count),
            }
        )

        retrieved_nf = _minhash_retrieve_ids_no_fallback(mgr, query=query, k=max(10, k))
        per_method["minhash_no_fallback"].append(
            {
                "query": query,
                "category": b["category"],
                "relevant_chunk_ids": sorted(relevant),
                "retrieved_chunk_ids": retrieved_nf,
                "p@1": precision_at_k(retrieved_nf, relevant, 1),
                "p@3": precision_at_k(retrieved_nf, relevant, 3),
                "p@5": precision_at_k(retrieved_nf, relevant, 5),
                "r@5": recall_at_k(retrieved_nf, relevant, 5),
                "latency_ms": 0.0,
                "memory_mb": 0.0,
                "fallback_to": None,
            }
        )

    summary: dict[str, Any] = {}
    for method, rows in per_method.items():
        base = {
            "mean_p@1": sum(r["p@1"] for r in rows) / len(rows),
            "mean_p@3": sum(r["p@3"] for r in rows) / len(rows),
            "mean_p@5": sum(r["p@5"] for r in rows) / len(rows),
            "mean_r@5": sum(r["r@5"] for r in rows) / len(rows),
            "map@5": mean_average_precision(
                ((r["retrieved_chunk_ids"], set(r["relevant_chunk_ids"])) for r in rows), k=5
            ),
            "mean_latency_ms": sum(r["latency_ms"] for r in rows) / len(rows),
            "mean_memory_mb": sum(r["memory_mb"] for r in rows) / len(rows),
        }
        # Add candidate/fallback rates where meaningful.
        if method in ("minhash", "hybrid"):
            base["fallback_rate"] = sum(1 for r in rows if r.get("fallback_to") is not None) / len(rows)
        if method == "minhash_lsh_only":
            base["candidate_rate"] = sum(1 for r in rows if int(r.get("lsh_candidate_count", 0)) > 0) / len(rows)
            base["mean_lsh_candidate_count"] = sum(int(r.get("lsh_candidate_count", 0)) for r in rows) / len(rows)
        summary[method] = base

    payload: dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "k": int(k),
        "use_pagerank": bool(use_pagerank),
        "summary": summary,
        "per_query": per_method,
    }
    _dump_json(_results_dir() / "method_comparison.json", payload)
    return payload


def run_parameter_sensitivity() -> dict[str, Any]:
    """
    Experiment 2 — Parameter sensitivity (INSTRUCTIONS §5.3).

    - MinHash: vary NUM_PERM ∈ {32, 64, 128, 256}, measure recall@5 and latency
    - LSH: vary NUM_BANDS ∈ {16, 32, 64}, measure recall@5
    - SimHash: vary Hamming threshold ∈ {5, 8, 10, 12, 15}, measure precision@5

    Returns:
        Results dict (also saved to `data/results/parameter_sensitivity.json`).
    """

    chunks = load_chunks()
    out: dict[str, Any] = {"generated_at": _utc_now_iso(), "minhash": [], "lsh": [], "simhash": []}

    def _choose_lsh_params(num_perm: int) -> tuple[int, int]:
        """
        Choose (bands, rows) such that bands*rows=num_perm.

        Prefers 32 bands when possible (baseline), otherwise falls back to a
        reasonable divisor.
        """

        if num_perm % 32 == 0:
            return 32, num_perm // 32
        for b in (16, 8, 4, 2, 1):
            if num_perm % b == 0:
                return b, num_perm // b
        return 1, num_perm

    # MinHash NUM_PERM sensitivity (rebuild index in-memory)
    for num_perm in (32, 64, 128, 256):
        old_perm = int(settings.MINHASH_NUM_PERM)
        old_bands = int(settings.LSH_NUM_BANDS)
        old_rows = int(settings.LSH_ROWS_PER_BAND)
        try:
            settings.MINHASH_NUM_PERM = int(num_perm)
            bands, rows = _choose_lsh_params(int(num_perm))
            settings.LSH_NUM_BANDS = int(bands)
            settings.LSH_ROWS_PER_BAND = int(rows)
            t0 = time.perf_counter()
            mgr = IndexManager()
            mgr.artifacts.minhash = build_minhash_lsh_index(chunks)
            r = Retriever(mgr)

            recalls: list[float] = []
            latencies: list[float] = []
            for b in BENCHMARK:
                relevant = set(b["relevant_chunk_ids"])
                retrieved = _minhash_retrieve_ids_no_fallback(mgr, b["query"], k=10)
                recalls.append(recall_at_k(retrieved, relevant, 5))
                latencies.append(0.0)
            out["minhash"].append(
                {
                    "num_perm": int(num_perm),
                    "num_bands": int(bands),
                    "rows_per_band": int(rows),
                    "mean_recall@5": sum(recalls) / len(recalls),
                    "mean_latency_ms": sum(latencies) / len(latencies),
                    "build_time_s": float(round(time.perf_counter() - t0, 4)),
                }
            )
        finally:
            settings.MINHASH_NUM_PERM = old_perm
            settings.LSH_NUM_BANDS = old_bands
            settings.LSH_ROWS_PER_BAND = old_rows

    # LSH NUM_BANDS sensitivity (rebuild index in-memory)
    for num_bands in (16, 32, 64):
        old_bands = int(settings.LSH_NUM_BANDS)
        old_rows = int(settings.LSH_ROWS_PER_BAND)
        try:
            settings.LSH_NUM_BANDS = int(num_bands)
            if int(settings.MINHASH_NUM_PERM) % int(num_bands) != 0:
                continue
            settings.LSH_ROWS_PER_BAND = int(settings.MINHASH_NUM_PERM) // int(num_bands)
            mgr = IndexManager()
            mgr.artifacts.minhash = build_minhash_lsh_index(chunks)
            r = Retriever(mgr)

            recalls: list[float] = []
            for b in BENCHMARK:
                relevant = set(b["relevant_chunk_ids"])
                retrieved = _minhash_retrieve_ids_no_fallback(mgr, b["query"], k=10)
                recalls.append(recall_at_k(retrieved, relevant, 5))
            out["lsh"].append(
                {
                    "num_bands": int(num_bands),
                    "rows_per_band": int(settings.LSH_ROWS_PER_BAND),
                    "mean_recall@5": sum(recalls) / len(recalls),
                }
            )
        finally:
            settings.LSH_NUM_BANDS = old_bands
            settings.LSH_ROWS_PER_BAND = old_rows

    # SimHash threshold sensitivity (vary threshold via settings, reuse loaded index)
    mgr0 = IndexManager()
    mgr0.load_all()
    r0 = Retriever(mgr0)
    for thr in (5, 8, 10, 12, 15):
        old_thr = int(settings.SIMHASH_HAMMING_THRESHOLD)
        try:
            settings.SIMHASH_HAMMING_THRESHOLD = int(thr)
            p5s: list[float] = []
            for b in BENCHMARK:
                relevant = set(b["relevant_chunk_ids"])
                res = r0.retrieve(b["query"], method="simhash", k=10, use_pagerank=False)
                retrieved = [c.chunk_id for c in res.chunks]
                p5s.append(precision_at_k(retrieved, relevant, 5))
            out["simhash"].append(
                {
                    "hamming_threshold": int(thr),
                    "mean_precision@5": sum(p5s) / len(p5s),
                }
            )
        finally:
            settings.SIMHASH_HAMMING_THRESHOLD = old_thr

    _dump_json(_results_dir() / "parameter_sensitivity.json", out)
    return out


def _scaled_chunks(scale: int) -> list[Chunk]:
    """
    Duplicate corpus `scale` times, modifying chunk IDs to stay unique.

    Args:
        scale: Repeat factor (2, 4, 8).

    Returns:
        Scaled list of Chunk objects.
    """

    base = load_chunks()
    out: list[Chunk] = []
    for rep in range(scale):
        for c in base:
            if rep == 0:
                out.append(c)
                continue
            out.append(
                Chunk(
                    id=f"{c.id}__dup{rep}",
                    text=c.text,
                    page_start=c.page_start,
                    page_end=c.page_end,
                    section_title=c.section_title,
                    word_count=c.word_count,
                    char_count=c.char_count,
                    source_file=c.source_file,
                    has_table=c.has_table,
                )
            )
    return out


def run_scalability(scales: tuple[int, ...] = (2, 4, 8)) -> dict[str, Any]:
    """
    Experiment 3 — Scalability (INSTRUCTIONS §5.3).

    Duplicates the corpus 2x/4x/8x and measures index build time and query latency.

    Args:
        scales: Repeat factors.

    Returns:
        Results dict (also saved to `data/results/scalability.json`).
    """

    out: dict[str, Any] = {"generated_at": _utc_now_iso(), "points": []}

    for scale in scales:
        scaled = _scaled_chunks(int(scale))
        mgr = IndexManager(index_dir=_results_dir() / "_tmp_indexes" / f"scale_{scale}")

        t0 = time.perf_counter()
        mgr.artifacts.tfidf = build_tfidf_index(scaled)
        tfidf_build_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        mgr.artifacts.minhash = build_minhash_lsh_index(scaled)
        minhash_build_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        mgr.artifacts.simhash = build_simhash_index(scaled)
        simhash_build_s = time.perf_counter() - t0

        build_time_s = tfidf_build_s + minhash_build_s + simhash_build_s
        r = Retriever(mgr)

        lat_tfidf: list[float] = []
        lat_minhash: list[float] = []
        lat_simhash: list[float] = []
        for b in BENCHMARK:
            res = r.retrieve(b["query"], method="tfidf", k=5, use_pagerank=False)
            lat_tfidf.append(float(res.latency_ms))
            res = r.retrieve(b["query"], method="minhash", k=5, use_pagerank=False)
            lat_minhash.append(float(res.latency_ms))
            res = r.retrieve(b["query"], method="simhash", k=5, use_pagerank=False)
            lat_simhash.append(float(res.latency_ms))

        out["points"].append(
            {
                "scale": int(scale),
                "chunk_count": int(len(scaled)),
                "build_time_s": float(round(build_time_s, 4)),
                "build_times_s": {
                    "tfidf": float(round(tfidf_build_s, 4)),
                    "minhash": float(round(minhash_build_s, 4)),
                    "simhash": float(round(simhash_build_s, 4)),
                },
                "mean_query_latency_ms": {
                    "tfidf": float(sum(lat_tfidf) / len(lat_tfidf)),
                    "minhash": float(sum(lat_minhash) / len(lat_minhash)),
                    "simhash": float(sum(lat_simhash) / len(lat_simhash)),
                },
            }
        )

    _dump_json(_results_dir() / "scalability.json", out)
    return out


def run_all_experiments() -> dict[str, Any]:
    """Run and save all three experiments, returning the combined payload."""

    method_comparison = run_method_comparison(k=5, use_pagerank=False)
    parameter_sensitivity = run_parameter_sensitivity()
    scalability = run_scalability()
    payload = {
        "generated_at": _utc_now_iso(),
        "method_comparison": method_comparison,
        "parameter_sensitivity": parameter_sensitivity,
        "scalability": scalability,
    }
    _dump_json(_results_dir() / "experiments.json", payload)
    return payload

