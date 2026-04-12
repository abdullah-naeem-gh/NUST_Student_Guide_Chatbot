"""Schemas for ingestion: Chunk storage and ingest API responses."""

from dataclasses import asdict, dataclass

from pydantic import BaseModel, Field


@dataclass
class Chunk:
    """
    A contiguous segment of handbook text with provenance for retrieval.

    Attributes:
        id: Stable identifier (e.g. chunk_000042).
        text: Chunk body (sentence-aligned; never split mid-sentence).
        page_start: First PDF page number (1-based).
        page_end: Last PDF page number (1-based).
        section_title: Nearest detected section heading (majority vote in chunk).
        word_count: Number of whitespace-separated words.
        char_count: Character length of ``text``.
        source_file: Original PDF filename.
        has_table: True when chunk is primarily tabular content.
    """

    id: str
    text: str
    page_start: int
    page_end: int
    section_title: str
    word_count: int
    char_count: int
    source_file: str
    has_table: bool = False

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return asdict(self)


class IngestProcessingStep(BaseModel):
    """One completed ingestion step with timing."""

    step: str
    duration_s: float
    status: str = "done"


class IngestResponse(BaseModel):
    """Response body for POST /ingest (Phase 1: parse, clean, chunk only)."""

    status: str = "success"
    chunk_count: int
    page_count: int
    source_file: str
    processing_steps: list[IngestProcessingStep] = Field(default_factory=list)
    total_duration_s: float
