"""Phase 4 generation tests: OpenRouter integration and fallback behavior."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from generation.llm import generate_answer
from retrieval.models import RetrievedChunkModel


def _chunks() -> list[RetrievedChunkModel]:
    """Create a minimal chunk list for prompting and citation mapping."""

    return [
        RetrievedChunkModel(
            chunk_id="chunk_000000",
            text="Graduation requirements: Students must have a minimum CGPA of 2.00 to graduate.",
            score=0.9,
            pagerank_score=0.0,
            final_score=0.9,
            page_start=10,
            page_end=10,
            section_title="Section 3.2 Graduation Requirements",
            highlight_spans=[],
        ),
        RetrievedChunkModel(
            chunk_id="chunk_000001",
            text="Probation policy: If CGPA falls below 2.00, the student may be placed on probation.",
            score=0.8,
            pagerank_score=0.0,
            final_score=0.8,
            page_start=12,
            page_end=12,
            section_title="Section 3.3 Academic Standing",
            highlight_spans=[],
        ),
    ]


def test_generate_answer_success_parses_content_and_citations(monkeypatch):
    """LLM path returns parsed answer and maps cited excerpt numbers to chunk_ids."""

    import generation.llm as llm

    monkeypatch.setattr(llm.settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(llm.settings, "OPENROUTER_DEFAULT_MODEL", "openai/gpt-oss-120b:free")

    captured = {}

    def fake_post(*_args, **_kwargs):
        captured["data"] = _kwargs.get("data")
        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                "choices": [
                    {
                        "message": {
                            "content": "Minimum CGPA mentioned is 2.00.\n\nCited: Excerpt 1"
                        }
                    }
                ]
            },
            text="ok",
        )

    monkeypatch.setattr(llm.requests, "post", fake_post)

    out = generate_answer("What is the minimum GPA requirement?", _chunks())
    assert "2.00" in out.answer
    assert out.cited_chunk_ids == ["chunk_000000"]
    assert captured["data"] is not None
    payload = llm.json.loads(captured["data"])
    assert payload["model"] == "openai/gpt-oss-120b:free"


def test_generate_answer_respects_explicit_model_override(monkeypatch):
    """Explicit model param overrides the configured default."""

    import generation.llm as llm

    monkeypatch.setattr(llm.settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(llm.settings, "OPENROUTER_DEFAULT_MODEL", "openai/gpt-oss-120b:free")

    captured = {}

    def fake_post(*_args, **_kwargs):
        captured["data"] = _kwargs.get("data")
        return SimpleNamespace(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "Answer.\nCited: Excerpt 1"}}]},
            text="ok",
        )

    monkeypatch.setattr(llm.requests, "post", fake_post)

    out = generate_answer(
        "What is the minimum GPA requirement?",
        _chunks(),
        model="qwen/qwen3-next-80b-a3b-instruct:free",
    )
    assert out.cited_chunk_ids == ["chunk_000000"]
    payload = llm.json.loads(captured["data"])
    assert payload["model"] == "qwen/qwen3-next-80b-a3b-instruct:free"


def test_generate_answer_falls_back_when_non_2xx(monkeypatch):
    """Non-2xx OpenRouter responses trigger extractive fallback."""

    import generation.llm as llm

    monkeypatch.setattr(llm.settings, "OPENROUTER_API_KEY", "test-key")

    def fake_post(*_args, **_kwargs):
        return SimpleNamespace(status_code=500, text="error")

    monkeypatch.setattr(llm.requests, "post", fake_post)

    out = generate_answer("minimum gpa requirement", _chunks())
    assert out.cited_chunk_ids == ["chunk_000000"]
    assert out.answer


def test_generate_answer_falls_back_when_key_missing(monkeypatch):
    """Missing API key triggers extractive fallback without attempting network."""

    import generation.llm as llm

    monkeypatch.setattr(llm.settings, "OPENROUTER_API_KEY", "")

    # If called, fail the test.
    def fake_post(*_args, **_kwargs):
        raise AssertionError("requests.post should not be called when key is missing")

    monkeypatch.setattr(llm.requests, "post", fake_post)

    out = generate_answer("minimum gpa requirement", _chunks())
    assert out.cited_chunk_ids == ["chunk_000000"]
    assert out.answer

