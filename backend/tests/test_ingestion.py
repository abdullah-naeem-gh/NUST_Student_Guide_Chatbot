"""Tests for PDF ingestion: cleaner, chunker, and real handbook PDFs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import settings
from ingestion.chunker import build_chunks_from_pdf
from ingestion.cleaner import clean_text
from ingestion.pdf_parser import parse_pdf

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


@pytest.mark.skipif(not UG_PDF.is_file(), reason="UG handbook PDF not in data/raw")
def test_semantic_chunks_have_required_fields() -> None:
    """Unstructured chunks carry id, text, page metadata, and source_file."""
    chunks = build_chunks_from_pdf(UG_PDF, "UG_Handbook.pdf")
    assert len(chunks) > 0
    for ch in chunks:
        assert ch.id.startswith("chunk_")
        assert len(ch.text) > 0
        assert ch.page_start >= 1
        assert ch.source_file == "UG_Handbook.pdf"


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
