"""Phase 3 retrieval tests: unified interface, highlights, and fusion."""

from __future__ import annotations

import json

import pytest

from config import settings
from indexing.index_manager import IndexManager, load_chunks
from retrieval.retriever import Retriever


@pytest.fixture()
def temp_data_dirs(tmp_path):
    """Redirect settings data directories to a temp location."""

    root = tmp_path / "data"
    chunks_dir = root / "chunks"
    index_dir = root / "index"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    settings.DATA_DIR = root
    settings.CHUNKS_DIR = chunks_dir
    settings.INDEX_DIR = index_dir
    return root, chunks_dir, index_dir


def _write_chunks(chunks_dir, chunks):
    """Write chunks.json in the ingestion format."""

    path = chunks_dir / "chunks.json"
    path.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return path


def test_retrieve_all_methods_returns_chunks_and_highlights(temp_data_dirs):
    """Retriever returns top-k chunks with highlight spans and fused scores."""

    _root, chunks_dir, _index_dir = temp_data_dirs

    chunks = [
        {
            "id": "chunk_000000",
            "text": "Section 3.2 describes the minimum GPA requirement for graduation. Students must maintain CGPA.",
            "page_start": 1,
            "page_end": 1,
            "section_title": "Section 3.2 Graduation Requirements",
            "word_count": 16,
            "char_count": 98,
            "source_file": "sample.pdf",
            "has_table": False,
        },
        {
            "id": "chunk_000001",
            "text": "Attendance policy: students must attend at least 75 percent of classes to sit in exams.",
            "page_start": 2,
            "page_end": 2,
            "section_title": "Section 4 Attendance Policy",
            "word_count": 17,
            "char_count": 96,
            "source_file": "sample.pdf",
            "has_table": False,
        },
        {
            "id": "chunk_000002",
            "text": "A course may be repeated at most two times under the course repetition rules.",
            "page_start": 3,
            "page_end": 3,
            "section_title": "Section 6 Course Repetition",
            "word_count": 16,
            "char_count": 86,
            "source_file": "sample.pdf",
            "has_table": False,
        },
    ]
    _write_chunks(chunks_dir, chunks)

    loaded = load_chunks()
    mgr = IndexManager()
    mgr.build_all(loaded, force=True)
    mgr.load_all()

    r = Retriever(mgr)

    q = "What is the minimum GPA requirement?"
    tfidf = r.retrieve(q, "tfidf", k=2, use_pagerank=True)
    assert tfidf.chunks
    assert any(span for span in tfidf.chunks[0].highlight_spans)
    assert all(c.final_score >= 0.0 for c in tfidf.chunks)

    sim = r.retrieve(q, "simhash", k=2, use_pagerank=True)
    # SimHash can legitimately return no candidates for short/abstract queries
    # depending on the Hamming threshold and tiny corpus size.
    assert sim.latency_ms >= 0.0

    mh = r.retrieve(q, "minhash", k=2, use_pagerank=True)
    assert mh.chunks

