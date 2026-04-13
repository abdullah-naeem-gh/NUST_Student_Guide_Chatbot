"""Phase 2 indexing tests: artifact builds and persistence."""

from __future__ import annotations

import json

import pytest

from config import settings
from indexing.index_manager import IndexManager, load_chunks


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


def test_build_all_indexes_creates_artifacts(temp_data_dirs):
    """Building all indexes creates the four expected files and sizes > 0."""

    _root, chunks_dir, index_dir = temp_data_dirs

    chunks = [
        {
            "id": "chunk_000000",
            "text": "Section 3.2 describes the minimum GPA requirement for graduation.",
            "page_start": 1,
            "page_end": 1,
            "section_title": "Section 3.2 Graduation Requirements",
            "word_count": 10,
            "char_count": 70,
            "source_file": "sample.pdf",
            "has_table": False,
        },
        {
            "id": "chunk_000001",
            "text": "See Section 3.2 for details. Attendance policy is strict for students.",
            "page_start": 2,
            "page_end": 2,
            "section_title": "Section 4 Attendance Policy",
            "word_count": 13,
            "char_count": 78,
            "source_file": "sample.pdf",
            "has_table": False,
        },
        {
            "id": "chunk_000002",
            "text": "Probation rules apply when CGPA is below the minimum threshold.",
            "page_start": 3,
            "page_end": 3,
            "section_title": "Section 5 Academic Standing",
            "word_count": 11,
            "char_count": 68,
            "source_file": "sample.pdf",
            "has_table": False,
        },
    ]
    _write_chunks(chunks_dir, chunks)

    loaded = load_chunks()
    mgr = IndexManager()
    results = mgr.build_all(loaded, force=True)
    assert {r.name for r in results} == {"minhash", "tfidf", "simhash", "pagerank"}

    expected = {
        "minhash.pkl",
        "tfidf.pkl",
        "simhash.json",
        "pagerank.json",
    }
    actual = {p.name for p in index_dir.iterdir()}
    assert expected.issubset(actual)

    for name in expected:
        assert (index_dir / name).stat().st_size > 0

