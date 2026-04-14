"""Prompt templates for answer generation (Phase 4)."""

from __future__ import annotations

from retrieval.models import RetrievedChunkModel


def build_system_prompt() -> str:
    """Return the system prompt enforcing extractive, excerpt-only answers."""

    return (
        "You are an academic policy assistant for NUST SEECS.\n"
        "You answer student questions STRICTLY based on the provided handbook excerpts.\n"
        "- Never answer from general knowledge\n"
        "- Always cite which section your answer comes from\n"
        "- If the excerpts don't contain enough information, say so explicitly\n"
        "- Be concise and precise — students need actionable answers\n"
        "- Format policy rules as numbered lists when there are multiple conditions\n"
    )


def build_user_prompt(query: str, top_chunks: list[RetrievedChunkModel]) -> str:
    """
    Build the user prompt with attributed excerpts.

    Args:
        query: Student question.
        top_chunks: Retrieved chunks to ground the answer.

    Returns:
        Prompt text including numbered excerpts with section + page attribution.
    """

    lines: list[str] = []
    lines.append(f"Student Question: {query.strip()}")
    lines.append("")
    lines.append("Relevant Handbook Excerpts:")
    for i, chunk in enumerate(top_chunks):
        excerpt_no = i + 1
        section = chunk.section_title or "Unknown section"
        page = chunk.page_start
        lines.append(f"[Excerpt {excerpt_no} — {section}, Page {page}]")
        lines.append(chunk.text.strip())
        lines.append("")
    lines.append("Based ONLY on the above excerpts, answer the student's question.")
    lines.append("At the end, cite which excerpt(s) you used.")
    return "\n".join(lines).strip() + "\n"

