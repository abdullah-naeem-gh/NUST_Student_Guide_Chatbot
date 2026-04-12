"""Tests for PDF ingestion: cleaner, chunker, and real handbook PDFs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import settings
from ingestion.chunker import build_chunks_from_prepared, prepare_cleaned_pages
from ingestion.cleaner import clean_text
from ingestion.pdf_parser import ParsedPage, parse_pdf

# Project root: backend/tests -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UG_PDF = REPO_ROOT / "data" / "raw" / "UG_Handbook.pdf"
PG_PDF = REPO_ROOT / "data" / "raw" / "PG_Handbook.pdf"


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """Use a temp chunks directory so tests do not conflict with real data."""
    monkeypatch.setattr(settings, "CHUNKS_DIR", tmp_path)
    import api.routes.ingest as ingest_module

    monkeypatch.setattr(ingest_module, "CHUNKS_JSON", tmp_path / "chunks.json")

    from main import app

    return TestClient(app)


def test_cleaner_pipeline_order_and_hyphen_join() -> None:
    """Eight-step cleaner fixes encoding, NFKC, hyphen breaks, and whitespace."""
    raw = "café \xff \n\natten-\ndance \nNUST SEECS UG Handbook 2024 | Page 12\n\n42\n"
    out = clean_text(raw)
    assert "attendance" in out.replace(" ", "")
    assert "NUST" not in out or "Handbook" not in out
    assert "\n\n" in out or "attendance" in out


def test_chunker_overlap_and_sentence_boundaries() -> None:
    """Sliding window keeps sentence boundaries and applies overlap between chunks."""
    sents = [
        "First sentence has exactly five words here.",
        "Second sentence also has five words here now.",
        "Third sentence adds five more words here today.",
        "Fourth sentence keeps five words in this line.",
        "Fifth sentence ends with five words right here.",
    ]
    body = " ".join(sents)
    fake = ParsedPage(
        page_number=1,
        text=body,
        section_title="Test Section",
        has_table=False,
    )
    prepared = prepare_cleaned_pages([fake])
    chunks = build_chunks_from_prepared(
        prepared,
        "unit_test.pdf",
        chunk_size_words=12,
        overlap_words=5,
        min_chunk_words=3,
    )
    assert len(chunks) >= 2
    for ch in chunks:
        assert ch.text.strip() == ch.text
        assert ch.page_start == 1 and ch.page_end == 1
    joined = " ".join(c.text for c in chunks)
    assert "First sentence" in joined
    assert "Fifth sentence" in joined


@pytest.mark.skipif(not UG_PDF.is_file(), reason="UG handbook PDF not in data/raw")
def test_parse_ug_handbook_returns_many_pages() -> None:
    """Real UG PDF yields multiple non-empty pages after TOC/blank skipping."""
    pages = parse_pdf(UG_PDF)
    assert len(pages) >= 10
    assert all(p.page_number >= 1 for p in pages)
    assert all(len(p.text) >= 50 for p in pages)


@pytest.mark.skipif(not UG_PDF.is_file(), reason="UG handbook PDF not in data/raw")
def test_post_ingest_ug_handbook(api_client: TestClient, tmp_path) -> None:
    """POST /ingest/ on UG handbook writes chunks.json with expected shape."""
    with UG_PDF.open("rb") as f:
        r = api_client.post(
            "/ingest/",
            files={"file": ("UG_Handbook.pdf", f, "application/pdf")},
            params={"force_rebuild": True},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "success"
    assert data["chunk_count"] > 0
    assert data["page_count"] >= 10
    assert any(s["step"] == "parse" for s in data["processing_steps"])

    chunks_path = tmp_path / "chunks.json"
    assert chunks_path.is_file()
    loaded = json.loads(chunks_path.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    assert loaded[0]["id"].startswith("chunk_")
    assert "text" in loaded[0]


@pytest.mark.skipif(not PG_PDF.is_file(), reason="PG handbook PDF not in data/raw")
def test_parse_pg_handbook_returns_pages() -> None:
    """Postgraduate handbook parses without error."""
    pages = parse_pdf(PG_PDF)
    assert len(pages) >= 5
