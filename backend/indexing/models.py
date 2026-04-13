"""Pydantic schemas and typed containers for indexing artifacts (Phase 2)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


IndexName = Literal["minhash", "simhash", "tfidf", "pagerank"]


class IndexBuildResult(BaseModel):
    """Summary of one index build operation."""

    name: IndexName
    built: bool = True
    path: str
    size_bytes: int = 0
    build_time_s: float = 0.0


class IndexStatusResponse(BaseModel):
    """Response model for GET /status."""

    indexed: bool
    chunk_count: int = 0
    source_file: str = ""
    index_paths: dict[IndexName, str] = Field(default_factory=dict)
    index_sizes_bytes: dict[IndexName, int] = Field(default_factory=dict)


def file_size_bytes(path: Path) -> int:
    """
    Return file size in bytes, 0 if missing.

    Args:
        path: File path.

    Returns:
        Size in bytes.
    """

    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0

