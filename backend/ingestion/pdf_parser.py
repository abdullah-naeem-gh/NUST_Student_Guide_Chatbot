"""PDF extraction with pdfplumber: layout, TOC skip, section heuristics, and tables."""

from __future__ import annotations

import logging
import re
import statistics
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber
from pdfplumber.page import Page

from ingestion.cleaner import clean_text

logger = logging.getLogger(__name__)

# Skip pages with almost no content after the full eight-step clean (INSTRUCTIONS §1.1)
_MIN_CHARS_AFTER_CLEAN = 50
# Heuristic: many dot leaders or TOC-style lines
_MIN_DOT_LEADER_MATCHES = 8
_MIN_TOC_LINE_PATTERN = 5


@dataclass
class ParsedPage:
    """One PDF page after extraction (before the eight-step cleaner)."""

    page_number: int
    text: str
    section_title: str
    has_table: bool


def _ligature_normalize(text: str) -> str:
    """Normalize ligatures and compatibility forms early (INSTRUCTIONS §1.1)."""
    return unicodedata.normalize("NFKD", text)


def _hyphen_join_linebreaks(text: str) -> str:
    """Join hyphenated words split across lines (also applied again in cleaner)."""
    return re.sub(r"-\n", "", text)


def _is_table_of_contents(text: str) -> bool:
    """
    Detect TOC pages via dot-leader density and 'section … 12' style lines.

    Args:
        text: Raw or lightly normalized page text.

    Returns:
        True if the page should be skipped as a table of contents.
    """
    if not text.strip():
        return False
    if len(re.findall(r"\.{4,}", text)) >= _MIN_DOT_LEADER_MATCHES:
        return True
    lines = text.split("\n")
    toc_lines = sum(1 for line in lines if re.search(r"\.{3,}\s*\d+\s*$", line.strip()))
    return toc_lines >= _MIN_TOC_LINE_PATTERN


def _extract_words_multicolumn(page: Page) -> str:
    """
    Reconstruct reading order for multi-column layouts using word x-positions.

    Uses a vertical midline split when two columns are present; otherwise sorts
    all words top-to-bottom, left-to-right.

    Args:
        page: pdfplumber page object.

    Returns:
        Space-joined text for the page body.
    """
    words: list[dict[str, Any]] = page.extract_words(x_tolerance=3) or []
    if not words:
        return page.extract_text() or ""

    width = float(page.width)
    mid = width / 2.0
    left = [w for w in words if (float(w["x0"]) + float(w["x1"])) / 2.0 < mid]
    right = [w for w in words if (float(w["x0"]) + float(w["x1"])) / 2.0 >= mid]

    def sort_key(w: dict[str, Any]) -> tuple[float, float]:
        return (-float(w["top"]), float(w["x0"]))

    # Single-column or sparse right column: global sort
    if len(right) < max(3, len(words) // 10):
        ordered = sorted(words, key=sort_key)
        return " ".join(w["text"] for w in ordered)

    left.sort(key=sort_key)
    right.sort(key=sort_key)
    return (
        " ".join(w["text"] for w in left) + " " + " ".join(w["text"] for w in right)
    ).strip()


def _detect_section_title(page: Page) -> str:
    """
    Infer a section heading from font sizes (INSTRUCTIONS §1.1 heuristic).

    Args:
        page: pdfplumber page object with character-level geometry.

    Returns:
        Concatenated heading characters, position-ordered, or empty string.
    """
    chars = page.chars
    if not chars:
        return ""

    sizes = [float(c.get("size", 0.0)) for c in chars if c.get("size") is not None]
    if not sizes:
        return ""

    try:
        body_size = statistics.mode(sizes)
    except statistics.StatisticsError:
        body_size = statistics.median(sizes)

    headings = [c for c in chars if float(c.get("size", 0.0)) > body_size + 2.0]
    if not headings:
        return ""

    headings.sort(key=lambda c: (-float(c.get("top", 0.0)), float(c.get("x0", 0.0))))
    return "".join(c.get("text", "") for c in headings).strip()


def _page_has_table(page: Page) -> bool:
    """Return True if pdfplumber finds at least one table on the page."""
    try:
        return bool(page.find_tables())
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("find_tables failed: %s", exc)
        return False


def parse_pdf(pdf_path: Path) -> list[ParsedPage]:
    """
    Extract per-page text and metadata from an academic handbook PDF.

    Handles headers/footers via downstream cleaning; removes hyphen breaks and
    ligatures here; skips TOC and near-empty pages; uses multi-column word order.

    Args:
        pdf_path: Path to a readable PDF file.

    Returns:
        Parsed pages in order (1-based page numbers), excluding TOC and empty pages.

    Raises:
        FileNotFoundError: If ``pdf_path`` does not exist.
        ValueError: If the file is not a PDF or cannot be opened.
    """
    path = pdf_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    results: list[ParsedPage] = []

    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                raw = _extract_words_multicolumn(page)
                raw = _ligature_normalize(raw)
                raw = _hyphen_join_linebreaks(raw)
                raw = re.sub(r"[ \t]+", " ", raw).strip()

                if _is_table_of_contents(raw):
                    logger.debug("Skipping TOC page %s", i)
                    continue

                cleaned_len = len(clean_text(raw))
                if cleaned_len < _MIN_CHARS_AFTER_CLEAN:
                    logger.debug(
                        "Skipping near-empty page %s (cleaned chars=%s)",
                        i,
                        cleaned_len,
                    )
                    continue

                section = _detect_section_title(page)
                has_tbl = _page_has_table(page)

                results.append(
                    ParsedPage(
                        page_number=i,
                        text=raw,
                        section_title=section,
                        has_table=has_tbl,
                    )
                )
    except Exception as exc:
        raise ValueError(f"Failed to read PDF {path}: {exc}") from exc

    return results
