"""LLM answer generation using OpenRouter (Phase 4)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import requests

from config import settings
from retrieval.models import RetrievedChunkModel

from .prompt_templates import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"


@dataclass(frozen=True)
class GeneratedAnswer:
    """Structured output from the generator for wiring into API response."""

    answer: str
    cited_chunk_ids: list[str]


def _extractive_fallback(query: str, chunks: list[RetrievedChunkModel]) -> GeneratedAnswer:
    """
    Fallback extractive answer when LLM call is unavailable.

    Strategy: pick the sentence from the top chunk with maximum query-term overlap.
    If sentence splitting is weak, fall back to the chunk text itself.
    """

    if not chunks:
        return GeneratedAnswer(
            answer="I don't have enough information in the provided excerpts to answer that.",
            cited_chunk_ids=[],
        )

    query_terms = {t for t in re.findall(r"[A-Za-z0-9]+", query.lower()) if t}
    best_sentence = ""
    best_score = -1
    top = chunks[0]

    sentences = re.split(r"(?<=[.!?])\s+", top.text.strip())
    for s in (x.strip() for x in sentences if x.strip()):
        terms = set(re.findall(r"[A-Za-z0-9]+", s.lower()))
        score = len(query_terms & terms)
        if score > best_score:
            best_score = score
            best_sentence = s

    answer = best_sentence if best_sentence else top.text.strip()
    return GeneratedAnswer(answer=answer, cited_chunk_ids=[top.chunk_id])


def _parse_cited_excerpt_numbers(text: str, max_n: int) -> list[int]:
    """
    Parse cited excerpt indices from the model's text.

    Supports patterns like 'Excerpt 1', 'Excerpts 1 and 2', or '[Excerpt 3]'.
    """
    # First, try explicit "excerpt" mentions (most reliable).
    found = re.findall(r"excerpt(?:s)?\s*#?\s*(\d+)", text, flags=re.IGNORECASE)

    # Also handle formats like:
    # - "Cited excerpts: 1, 2, 3"
    # - "**Cited excerpts:** 1, 2, 3, 4, 5"
    # - "Citations: Excerpt 2 and 4"
    citation_lines = [
        line
        for line in text.splitlines()
        if re.search(r"\b(cited|cite|citations?)\b", line, flags=re.IGNORECASE)
    ]
    for line in citation_lines:
        found.extend(re.findall(r"\b(\d+)\b", line))

    nums: list[int] = []
    for raw in found:
        try:
            n = int(raw)
        except ValueError:
            continue
        if 1 <= n <= max_n and n not in nums:
            nums.append(n)
    return nums


def generate_answer(
    query: str, top_chunks: list[RetrievedChunkModel], model: str | None = None
) -> GeneratedAnswer:
    """
    Generate a grounded answer from retrieved excerpts using OpenRouter.

    Args:
        query: Student question.
        top_chunks: Retrieved chunks to ground the answer.

    Returns:
        GeneratedAnswer with `answer` and `cited_chunk_ids`.
    """

    api_key = (settings.OPENROUTER_API_KEY or "").strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing; using extractive fallback.")
        return _extractive_fallback(query, top_chunks)

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(query, top_chunks)

    selected_model = (model or settings.OPENROUTER_DEFAULT_MODEL or OPENROUTER_MODEL).strip()
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        resp = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=30,
        )
    except Exception:
        logger.exception("OpenRouter request failed; using extractive fallback.")
        return _extractive_fallback(query, top_chunks)

    if resp.status_code < 200 or resp.status_code >= 300:
        logger.warning(
            "OpenRouter non-2xx (%s): %s", resp.status_code, resp.text[:500]
        )
        return _extractive_fallback(query, top_chunks)

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        answer_text = str(content).strip()
    except Exception:
        logger.exception("OpenRouter response parse failed; using extractive fallback.")
        return _extractive_fallback(query, top_chunks)

    cited_nums = _parse_cited_excerpt_numbers(answer_text, max_n=len(top_chunks))
    if cited_nums:
        cited_chunk_ids = [top_chunks[i - 1].chunk_id for i in cited_nums]
    else:
        cited_chunk_ids = [top_chunks[0].chunk_id] if top_chunks else []

    return GeneratedAnswer(answer=answer_text, cited_chunk_ids=cited_chunk_ids)

