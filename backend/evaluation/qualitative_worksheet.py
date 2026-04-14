"""Generate a markdown worksheet for qualitative answer correctness evaluation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from evaluation.benchmark_queries import BENCHMARK
from indexing.index_manager import IndexManager
from retrieval.retriever import Retriever


def _utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""

    return datetime.now(timezone.utc).isoformat()


def _results_path() -> Path:
    """Return results directory path."""

    p = settings.DATA_DIR / "results"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_retriever() -> Retriever:
    """Load a Retriever bound to on-disk artifacts."""

    mgr = IndexManager()
    mgr.load_all()
    return Retriever(mgr)


def write_qualitative_worksheet(k: int = 5) -> Path:
    """
    Write `data/results/QUALITATIVE_WORKSHEET.md`.

    This worksheet is meant for the required qualitative evaluation:
    manually judge whether the retrieved evidence supports a correct answer.
    """

    r = _load_retriever()
    out_path = _results_path() / "QUALITATIVE_WORKSHEET.md"

    lines: list[str] = []
    lines.append("# Qualitative Evaluation Worksheet\n\n")
    lines.append(f"Generated at `{_utc_now_iso()}`.\n\n")
    lines.append(
        "## How to score\n\n"
        "For each query and method:\n"
        "- **Correct**: top evidence clearly contains the policy rule needed to answer.\n"
        "- **Partially correct**: evidence is related but missing a key condition/number.\n"
        "- **Incorrect**: evidence does not support the answer.\n\n"
    )

    for i, b in enumerate(BENCHMARK, start=1):
        q = b["query"]
        lines.append(f"## Q{i} — {b['category']}\n\n")
        lines.append(f"**Query**: {q}\n\n")

        for method in ("minhash", "simhash", "tfidf"):
            res = r.retrieve(q, method=method, k=k, use_pagerank=False)
            ids = [c.chunk_id for c in res.chunks]
            lines.append(f"### Method: {method}\n\n")
            lines.append(f"- Score: [ ] Correct  [ ] Partially correct  [ ] Incorrect\n")
            lines.append(f"- Notes: \n\n")
            lines.append("| rank | chunk_id | section | pages | snippet |\n")
            lines.append("|---:|---|---|---:|---|\n")
            for rank, c in enumerate(res.chunks, start=1):
                snippet = " ".join(c.text.split())[:240].replace("|", "\\|")
                lines.append(
                    f"| {rank} | `{c.chunk_id}` | {c.section_title[:40].replace('|','\\|')} | {c.page_start}-{c.page_end} | {snippet} |\n"
                )
            lines.append("\n")

    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    print(write_qualitative_worksheet())

