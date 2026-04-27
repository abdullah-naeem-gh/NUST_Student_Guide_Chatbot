"""Helpers for qualitative evaluation scoring and reporting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

from config import settings
from evaluation.benchmark_queries import BENCHMARK

Method = Literal["minhash", "simhash", "tfidf", "hybrid"]
Score = Literal["correct", "partial", "incorrect", "unscored"]


class QualitativeMethodScore(TypedDict):
    """Score and freeform notes for one method on one query."""

    score: Score
    notes: str


class QualitativeQueryScore(TypedDict):
    """Qualitative scoring entry for one benchmark query."""

    query: str
    category: str
    methods: dict[Method, QualitativeMethodScore]


class QualitativeScoresFile(TypedDict):
    """Top-level qualitative scoring file schema."""

    generated_at: str
    k: int
    scores: list[QualitativeQueryScore]


def _utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""

    return datetime.now(timezone.utc).isoformat()


def scores_path() -> Path:
    """Return canonical path for qualitative scores JSON."""

    p = settings.DATA_DIR / "results" / "qualitative_scores.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def init_scores_file(k: int = 5, overwrite: bool = False) -> Path:
    """
    Create a qualitative scoring JSON template for manual filling.

    Args:
        k: Top-k used during evaluation.
        overwrite: When True, overwrite any existing file.

    Returns:
        Path to the created template.
    """

    path = scores_path()
    if path.exists() and not overwrite:
        return path

    payload: QualitativeScoresFile = {
        "generated_at": _utc_now_iso(),
        "k": int(k),
        "scores": [],
    }
    for b in BENCHMARK:
        payload["scores"].append(
            {
                "query": b["query"],
                "category": b["category"],
                "methods": {
                    "hybrid": {"score": "unscored", "notes": ""},
                    "minhash": {"score": "unscored", "notes": ""},
                    "simhash": {"score": "unscored", "notes": ""},
                    "tfidf": {"score": "unscored", "notes": ""},
                },
            }
        )

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_scores() -> QualitativeScoresFile | None:
    """
    Load qualitative scores JSON if present.

    Returns:
        Parsed scores file or None if missing.
    """

    path = scores_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_scores(payload: QualitativeScoresFile) -> dict[str, Any]:
    """
    Summarize qualitative scores per method.

    Args:
        payload: Qualitative scores file.

    Returns:
        Summary dict with counts per method.
    """

    methods: list[Method] = ["hybrid", "minhash", "simhash", "tfidf"]
    counts: dict[str, dict[str, int]] = {
        m: {"correct": 0, "partial": 0, "incorrect": 0, "unscored": 0} for m in methods
    }
    for entry in payload.get("scores", []):
        ms = entry.get("methods", {})
        for m in methods:
            s = ms.get(m, {}).get("score", "unscored")
            if s not in counts[m]:
                s = "unscored"
            counts[m][s] += 1
    return {
        "k": int(payload.get("k", 5)),
        "total_queries": len(payload.get("scores", [])),
        "counts": counts,
    }


if __name__ == "__main__":
    print(init_scores_file())

