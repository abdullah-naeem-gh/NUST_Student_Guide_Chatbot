"""Semantic chunking via Unstructured — groups content by section-title boundaries."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from config import settings
from ingestion.models import Chunk

logger = logging.getLogger(__name__)


def _word_count(text: str) -> int:
    return len(text.split())


def _page_range(chunk_element) -> tuple[int, int]:
    """Return (page_start, page_end) from an Unstructured CompositeElement."""
    pn = getattr(chunk_element.metadata, "page_number", None)
    if pn is None:
        return 1, 1
    if isinstance(pn, list):
        nums = [p for p in pn if isinstance(p, int)]
        return (min(nums), max(nums)) if nums else (1, 1)
    return int(pn), int(pn)


def _extract_section(chunk_element) -> str:
    """
    Extract the nearest section heading from an Unstructured CompositeElement.

    Checks metadata.section first, then walks orig_elements for a Title element.
    """
    meta = chunk_element.metadata
    if getattr(meta, "section", None):
        return str(meta.section).strip()
    for el in getattr(meta, "orig_elements", None) or []:
        if el.category == "Title":
            return el.text.strip()
    return ""


def build_chunks_from_pdf(pdf_path: Path, source_file: str) -> list[Chunk]:
    """
    Partition a PDF into semantic chunks using Unstructured's chunk_by_title.

    Each chunk stays within one logical section. Tables are detected from
    element categories so downstream code can handle them specially.

    Args:
        pdf_path: Absolute path to the PDF file.
        source_file: Filename stored in chunk metadata (e.g. ``UG_Handbook.pdf``).

    Returns:
        Ordered list of :class:`Chunk` instances.
    """
    from unstructured.chunking.title import chunk_by_title
    from unstructured.partition.pdf import partition_pdf

    strategy = settings.UNSTRUCTURED_STRATEGY
    max_chars = settings.CHUNK_MAX_CHARACTERS
    new_after = settings.CHUNK_NEW_AFTER_N_CHARS
    min_w = settings.MIN_CHUNK_WORDS

    logger.info("Partitioning %s (strategy=%s)", pdf_path.name, strategy)
    elements = partition_pdf(
        filename=str(pdf_path),
        strategy=strategy,
        include_page_breaks=True,
    )
    logger.info("Got %d raw elements; chunking by title...", len(elements))

    raw_chunks = chunk_by_title(
        elements,
        max_characters=max_chars,
        new_after_n_chars=new_after,
        combine_text_under_n_chars=200,
        multipage_sections=True,
    )

    chunks: list[Chunk] = []
    for i, raw in enumerate(raw_chunks):
        text = raw.text.strip()
        if not text or _word_count(text) < min_w:
            continue

        p_start, p_end = _page_range(raw)
        section = _extract_section(raw)
        orig = getattr(raw.metadata, "orig_elements", None) or []
        has_tbl = any(getattr(el, "category", "") == "Table" for el in orig)

        chunks.append(
            Chunk(
                id=f"chunk_{i:06d}",
                text=text,
                page_start=p_start,
                page_end=p_end,
                section_title=section,
                word_count=_word_count(text),
                char_count=len(text),
                source_file=source_file,
                has_table=has_tbl,
            )
        )

    logger.info("Built %d semantic chunks from %s", len(chunks), source_file)
    return chunks


def ingest_pdf_file(pdf_path: Path) -> list[Chunk]:
    """
    End-to-end ingest: semantically chunk a PDF and return chunks.

    Args:
        pdf_path: Path to the PDF file to ingest.

    Returns:
        Chunks ready to serialize.
    """
    return build_chunks_from_pdf(pdf_path, source_file=pdf_path.name)


def save_chunks_json(chunks: list[Chunk], chunks_dir: Path | None = None) -> Path:
    """
    Persist chunks and id→index lookup to ``chunks.json`` and ``chunks_lookup.json``.

    Args:
        chunks: Chunk list to serialize.
        chunks_dir: Output directory (default ``settings.CHUNKS_DIR``).

    Returns:
        Path to ``chunks.json``.
    """
    out_dir = chunks_dir if chunks_dir is not None else settings.CHUNKS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "chunks.json"
    lookup_path = out_dir / "chunks_lookup.json"

    payload = [c.to_dict() for c in chunks]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lookup = {c["id"]: i for i, c in enumerate(payload)}
    lookup_path.write_text(
        json.dumps(lookup, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info("Saved %d chunks to %s", len(chunks), path)
    return path
