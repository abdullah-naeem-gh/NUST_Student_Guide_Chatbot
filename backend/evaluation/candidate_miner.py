"""Utilities to mine candidate relevant chunks for benchmark labeling."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from config import settings
from evaluation.benchmark_queries import BENCHMARK
from indexing.index_manager import IndexManager
from retrieval.retriever import Retriever

Method = Literal["minhash", "simhash", "tfidf"]

_WORD_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*\b")


def _load_retriever() -> Retriever:
    """Load a Retriever bound to the on-disk artifacts."""

    mgr = IndexManager()
    mgr.load_all()
    return Retriever(mgr)


def _load_chunk_texts() -> dict[str, str]:
    """Load chunk_id -> text (collapsed whitespace) for quick snippet rendering."""

    chunks_path = settings.CHUNKS_DIR / "chunks.json"
    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for c in payload:
        cid = str(c.get("id", ""))
        txt = str(c.get("text", ""))
        out[cid] = " ".join(txt.split())
    return out


def _query_terms(query: str) -> set[str]:
    """Extract normalized query terms for overlap scoring."""

    return {t.lower() for t in _WORD_RE.findall(query)}


def mine_candidates(per_method_k: int = 20) -> list[dict[str, Any]]:
    """
    Mine top candidates per query from each retrieval method.

    Args:
        per_method_k: How many top results to collect per method.

    Returns:
        List of dicts with candidates per query.
    """

    r = _load_retriever()
    texts = _load_chunk_texts()

    out: list[dict[str, Any]] = []
    for b in BENCHMARK:
        q = b["query"]
        q_terms = _query_terms(q)
        per_method: dict[str, list[dict[str, Any]]] = {}
        union: dict[str, dict[str, Any]] = {}

        for method in ("tfidf", "minhash", "simhash"):
            res = r.retrieve(q, method=method, k=per_method_k, use_pagerank=False)
            rows: list[dict[str, Any]] = []
            for rank, c in enumerate(res.chunks, start=1):
                txt = texts.get(c.chunk_id, "")
                overlap = 0.0
                if txt and q_terms:
                    tset = {t.lower() for t in _WORD_RE.findall(txt)}
                    overlap = len(tset & q_terms) / float(len(q_terms))
                row = {
                    "rank": int(rank),
                    "chunk_id": c.chunk_id,
                    "score": float(c.score),
                    "final_score": float(c.final_score),
                    "term_overlap": float(round(overlap, 4)),
                    "snippet": (txt[:240] + ("…" if len(txt) > 240 else "")),
                }
                rows.append(row)
                u = union.get(c.chunk_id)
                if u is None:
                    union[c.chunk_id] = {"chunk_id": c.chunk_id, "from": {method: int(rank)}, **row}
                else:
                    u["from"][method] = int(rank)
                    u["term_overlap"] = max(float(u.get("term_overlap", 0.0)), float(row["term_overlap"]))
            per_method[method] = rows

        # Produce a union view to help labeling (high overlap + shows which methods found it).
        union_list = list(union.values())
        union_list.sort(
            key=lambda x: (
                -float(x.get("term_overlap", 0.0)),
                min(int(v) for v in x.get("from", {}).values()) if x.get("from") else 10**9,
            )
        )

        out.append(
            {
                "query": q,
                "category": b["category"],
                "current_relevant_chunk_ids": list(b["relevant_chunk_ids"]),
                "per_method": per_method,
                "union_sorted": union_list,
            }
        )
    return out


def write_worksheet_md(out_path: Path | None = None, per_method_k: int = 20, union_k: int = 30) -> Path:
    """
    Write a markdown worksheet to speed up manual ground-truth expansion.

    Args:
        out_path: Optional output path; defaults to `data/results/GROUND_TRUTH_WORKSHEET.md`.
        per_method_k: Top-k per method to mine.
        union_k: How many from the union list to display.

    Returns:
        Path to the written worksheet.
    """

    p = (
        out_path
        if out_path is not None
        else (settings.DATA_DIR / "results" / "GROUND_TRUTH_WORKSHEET.md")
    )
    p.parent.mkdir(parents=True, exist_ok=True)

    mined = mine_candidates(per_method_k=per_method_k)
    lines: list[str] = []
    lines.append("# Ground Truth Worksheet\n\n")
    lines.append(
        "Use this file to expand `relevant_chunk_ids` per query (goal: ~3–8 relevant chunks each).\n\n"
    )
    lines.append(
        "- **Suggested workflow**: For each query, scan the **Union shortlist** first (it mixes all methods).\n"
        "- Mark chunk_ids that truly answer the question.\n"
        "- Then update `backend/evaluation/benchmark_queries.py`.\n\n"
    )

    for i, q in enumerate(mined, start=1):
        lines.append(f"## Q{i}: {q['category']}\n\n")
        lines.append(f"**Query**: {q['query']}\n\n")
        cur = q["current_relevant_chunk_ids"]
        lines.append(f"**Current relevant_chunk_ids** ({len(cur)}): `{', '.join(cur)}`\n\n")

        lines.append("### Union shortlist\n\n")
        lines.append("| pick | chunk_id | overlap | from (ranks) | snippet |\n")
        lines.append("|---|---|---:|---|---|\n")
        for row in q["union_sorted"][:union_k]:
            frm = ", ".join(f"{m}:{r}" for m, r in sorted(row.get("from", {}).items()))
            snippet = str(row.get("snippet", "")).replace("|", "\\|")
            lines.append(
                f"| [ ] | `{row['chunk_id']}` | {row.get('term_overlap', 0):.2f} | {frm} | {snippet} |\n"
            )
        lines.append("\n")

    p.write_text("".join(lines), encoding="utf-8")
    return p


if __name__ == "__main__":
    path = write_worksheet_md()
    print(str(path))

