"""Index and corpus status endpoint (INSTRUCTIONS §6)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter

from config import settings
from index_state import describe_index_paths, indexes_exist
from indexing.index_manager import IndexManager
from indexing.models import IndexStatusResponse, file_size_bytes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["status"])


def _chunk_summary(chunks_path: Path) -> tuple[int, str, list[str]]:
    """
    Compute chunk_count, first source_file, and unique source_files from chunks.json.

    Args:
        chunks_path: Path to chunks.json.

    Returns:
        (chunk_count, source_file, source_files sorted).
    """

    if not chunks_path.exists():
        return 0, "", []
    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    if not payload:
        return 0, "", []
    first = str(payload[0].get("source_file", "")) if isinstance(payload[0], dict) else ""
    seen: set[str] = set()
    sources: list[str] = []
    for row in payload:
        if isinstance(row, dict):
            sf = str(row.get("source_file", "") or "")
            if sf and sf not in seen:
                seen.add(sf)
                sources.append(sf)
    sources.sort()
    return len(payload), first, sources


@router.get("/status", response_model=IndexStatusResponse)
async def status() -> IndexStatusResponse:
    """
    Report whether indexes are present and their on-disk sizes.

    Returns:
        Status payload used by the frontend to show readiness and artifact sizes.
    """

    indexed = indexes_exist()
    mgr = IndexManager()
    chunk_count, source_file, source_files = _chunk_summary(settings.CHUNKS_DIR / "chunks.json")

    paths = describe_index_paths()
    sizes = {k: file_size_bytes(p) for k, p in mgr.paths.items()}

    logger.debug("Status: indexed=%s chunk_count=%s", indexed, chunk_count)
    return IndexStatusResponse(
        indexed=indexed,
        chunk_count=chunk_count,
        source_file=source_file,
        source_files=source_files,
        index_paths={k: v for k, v in paths.items()},  # type: ignore[arg-type]
        index_sizes_bytes=sizes,
    )

