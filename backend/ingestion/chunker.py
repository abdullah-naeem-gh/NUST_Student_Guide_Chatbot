"""Sliding-window chunking with sentence boundaries and overlap."""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

import nltk
from nltk.tokenize import PunktSentenceTokenizer

from config import settings
from ingestion.cleaner import clean_text
from ingestion.models import Chunk
from ingestion.pdf_parser import ParsedPage, parse_pdf

logger = logging.getLogger(__name__)

# Prose is dominated by tables when word count is low but tables exist
_TABLE_ONLY_MAX_WORDS = 40

# Store NLTK packages under backend/nltk_data (writable; avoids ~/.nltk_data permission issues)
_NLTK_DATA_DIR = Path(__file__).resolve().parent.parent / "nltk_data"

_punkt_tokenizer: PunktSentenceTokenizer | None = None


def _ensure_punkt() -> PunktSentenceTokenizer:
    """Load Punkt tokenizer data (downloads into ``backend/nltk_data`` if missing)."""
    global _punkt_tokenizer
    if _punkt_tokenizer is not None:
        return _punkt_tokenizer
    _NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    nltk_dir = str(_NLTK_DATA_DIR)
    if nltk_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_dir)
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        logger.info("Downloading NLTK punkt tokenizer to %s", _NLTK_DATA_DIR)
        nltk.download("punkt", download_dir=nltk_dir, quiet=True)
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", download_dir=nltk_dir, quiet=True)
    _punkt_tokenizer = PunktSentenceTokenizer()
    return _punkt_tokenizer


def _word_count(text: str) -> int:
    """Count whitespace-separated words."""
    return len(text.split())


def _is_table_only_page(cleaned_text: str, has_table: bool) -> bool:
    """Heuristic: table-heavy page with little prose (INSTRUCTIONS §1.3)."""
    if not has_table:
        return False
    return _word_count(cleaned_text) <= _TABLE_ONLY_MAX_WORDS


def _char_to_page_meta(
    char_index: int,
    spans: list[tuple[int, int, int, str]],
) -> tuple[int, str]:
    """
    Map a character index into the prose buffer to page number and section title.

    Args:
        char_index: Absolute index in concatenated prose string.
        spans: ``(char_start, char_end, page_number, section_title)`` per page.

    Returns:
        Page number and section title covering the index.
    """
    for start, end, page_num, section in spans:
        if start <= char_index < end:
            return page_num, section
    if spans:
        last = spans[-1]
        return last[2], last[3]
    return 1, ""


def _majority_section_from_sentence_metas(sentence_metas: list[tuple[str, str]]) -> str:
    """
    Pick the section title with the most words contributed in this chunk.

    Args:
        sentence_metas: Sentences in the chunk with (sentence, section_title).

    Returns:
        Winning section title or empty string.
    """
    counts: Counter[str] = Counter()
    for sent, sec in sentence_metas:
        if not sec:
            continue
        counts[sec] += _word_count(sent)
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def _span_tokenize(text: str) -> list[tuple[int, int, str]]:
    """Return ``(start, end, sentence)`` using Punkt."""
    tok = _ensure_punkt()
    return [(start, end, text[start:end]) for start, end in tok.span_tokenize(text)]


def _chunk_prose_segment(
    prose_text: str,
    page_spans: list[tuple[int, int, int, str]],
    source_file: str,
    chunk_size: int,
    overlap_words: int,
    min_words: int,
    chunk_index_start: int,
) -> tuple[list[Chunk], int]:
    """
    Build overlapping chunks from prose without splitting sentences.

    Args:
        prose_text: Concatenated cleaned text for consecutive prose pages.
        page_spans: Character spans per page within ``prose_text``.
        source_file: PDF filename for metadata.
        chunk_size: Target maximum words per chunk.
        overlap_words: Words overlapped into the next chunk.
        min_words: Drop or merge chunks shorter than this.
        chunk_index_start: First numeric id for ``chunk_XXXXXX``.

    Returns:
        Chunks and the next global chunk index counter.
    """
    chunks: list[Chunk] = []
    if not prose_text.strip():
        return chunks, chunk_index_start

    sent_spans = _span_tokenize(prose_text)
    if not sent_spans:
        return chunks, chunk_index_start

    sentences = [s for _, _, s in sent_spans]
    n = len(sentences)
    sent_idx = 0
    idx = chunk_index_start

    while sent_idx < n:
        end_idx = sent_idx
        wc = 0
        while end_idx < n and wc < chunk_size:
            wc += _word_count(sentences[end_idx])
            end_idx += 1
        if end_idx == sent_idx:
            end_idx = sent_idx + 1

        piece_sents = sentences[sent_idx:end_idx]
        chunk_text = " ".join(piece_sents).strip()
        if not chunk_text:
            sent_idx = end_idx
            continue

        sent_metas: list[tuple[str, str]] = []
        for start, end, sent in sent_spans[sent_idx:end_idx]:
            mid = (start + end) // 2
            _, sec = _char_to_page_meta(mid, page_spans)
            sent_metas.append((sent, sec))

        p_start = min(
            _char_to_page_meta(sent_spans[i][0], page_spans)[0]
            for i in range(sent_idx, end_idx)
        )
        p_end = max(
            _char_to_page_meta(sent_spans[i][1] - 1, page_spans)[0]
            for i in range(sent_idx, end_idx)
        )
        section = _majority_section_from_sentence_metas(sent_metas)

        cid = f"chunk_{idx:06d}"
        idx += 1
        chunks.append(
            Chunk(
                id=cid,
                text=chunk_text,
                page_start=p_start,
                page_end=p_end,
                section_title=section,
                word_count=_word_count(chunk_text),
                char_count=len(chunk_text),
                source_file=source_file,
                has_table=False,
            )
        )

        if end_idx >= n:
            break

        overlap_target = overlap_words
        back = end_idx - 1
        ow = 0
        while back > sent_idx and ow < overlap_target:
            ow += _word_count(sentences[back])
            back -= 1
        next_start = back + 1
        if next_start <= sent_idx:
            next_start = sent_idx + 1
        sent_idx = next_start

    merged = _merge_short_tail(chunks, min_words)
    return merged, idx


def _merge_short_tail(chunks: list[Chunk], min_words: int) -> list[Chunk]:
    """Merge the last chunk into the previous one if it is too short."""
    if len(chunks) < 2:
        if len(chunks) == 1 and chunks[0].word_count < min_words:
            return chunks
        return chunks
    last = chunks[-1]
    if last.word_count >= min_words:
        return chunks
    prev = chunks[-2]
    merged_text = (prev.text + " " + last.text).strip()
    merged = Chunk(
        id=prev.id,
        text=merged_text,
        page_start=min(prev.page_start, last.page_start),
        page_end=max(prev.page_end, last.page_end),
        section_title=(
            prev.section_title
            if prev.word_count >= last.word_count
            else last.section_title
        ),
        word_count=_word_count(merged_text),
        char_count=len(merged_text),
        source_file=prev.source_file,
        has_table=prev.has_table or last.has_table,
    )
    return chunks[:-2] + [merged]


def prepare_cleaned_pages(
    pages: list[ParsedPage],
) -> list[tuple[ParsedPage, str, bool]]:
    """
    Run the eight-step cleaner on each parsed page and flag table-only pages.

    Args:
        pages: Output of :func:`ingestion.pdf_parser.parse_pdf`.

    Returns:
        Tuples of (parsed page, cleaned text, table_only heuristic flag).
    """
    cleaned_pages: list[tuple[ParsedPage, str, bool]] = []
    for p in pages:
        cleaned = clean_text(p.text)
        cleaned_pages.append((p, cleaned, _is_table_only_page(cleaned, p.has_table)))
    return cleaned_pages


def build_chunks_from_prepared(
    cleaned_pages: list[tuple[ParsedPage, str, bool]],
    source_file: str,
    chunk_size_words: int | None = None,
    overlap_words: int | None = None,
    min_chunk_words: int | None = None,
) -> list[Chunk]:
    """
    Chunk already-cleaned pages (sliding window + table-only segments).

    Args:
        cleaned_pages: Output of :func:`prepare_cleaned_pages`.
        source_file: PDF filename for metadata.
        chunk_size_words: Target words per chunk (default from settings).
        overlap_words: Overlap between chunks (default from settings).
        min_chunk_words: Minimum words; short tail merged (default from settings).

    Returns:
        Ordered list of :class:`Chunk` instances.
    """
    size = (
        chunk_size_words if chunk_size_words is not None else settings.CHUNK_SIZE_WORDS
    )
    overlap = (
        overlap_words if overlap_words is not None else settings.CHUNK_OVERLAP_WORDS
    )
    min_w = min_chunk_words if min_chunk_words is not None else settings.MIN_CHUNK_WORDS

    all_chunks: list[Chunk] = []
    chunk_counter = 0

    prose_buffer: list[tuple[ParsedPage, str]] = []
    for page, cleaned, table_only in cleaned_pages:
        if table_only:
            if prose_buffer:
                text, spans = _join_prose_buffer(prose_buffer)
                batch, chunk_counter = _chunk_prose_segment(
                    text,
                    spans,
                    source_file,
                    size,
                    overlap,
                    min_w,
                    chunk_counter,
                )
                all_chunks.extend(batch)
                prose_buffer = []
            cid = f"chunk_{chunk_counter:06d}"
            chunk_counter += 1
            all_chunks.append(
                Chunk(
                    id=cid,
                    text=cleaned,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    section_title=page.section_title,
                    word_count=_word_count(cleaned),
                    char_count=len(cleaned),
                    source_file=source_file,
                    has_table=True,
                )
            )
        else:
            prose_buffer.append((page, cleaned))

    if prose_buffer:
        text, spans = _join_prose_buffer(prose_buffer)
        batch, chunk_counter = _chunk_prose_segment(
            text,
            spans,
            source_file,
            size,
            overlap,
            min_w,
            chunk_counter,
        )
        all_chunks.extend(batch)

    return _merge_short_tail(all_chunks, min_w)


def build_chunks_from_pages(
    pages: list[ParsedPage],
    source_file: str,
    chunk_size_words: int | None = None,
    overlap_words: int | None = None,
    min_chunk_words: int | None = None,
) -> list[Chunk]:
    """
    Convert parsed pages into overlapping chunks; table-only pages become one chunk each.

    Args:
        pages: Output of :func:`ingestion.pdf_parser.parse_pdf` (ordered).
        source_file: PDF filename (e.g. ``UG_Handbook.pdf``).
        chunk_size_words: Target words per chunk (default from settings).
        overlap_words: Overlap between chunks (default from settings).
        min_chunk_words: Minimum words; short tail merged (default from settings).

    Returns:
        Ordered list of :class:`Chunk` instances.
    """
    prepared = prepare_cleaned_pages(pages)
    return build_chunks_from_prepared(
        prepared,
        source_file,
        chunk_size_words=chunk_size_words,
        overlap_words=overlap_words,
        min_chunk_words=min_chunk_words,
    )


def _join_prose_buffer(
    prose_buffer: list[tuple[ParsedPage, str]],
) -> tuple[str, list[tuple[int, int, int, str]]]:
    """
    Join prose pages with ``\\n\\n`` and record character spans per page.

    Args:
        prose_buffer: List of (parsed page, cleaned text).

    Returns:
        Full prose string and ``(start, end, page_number, section_title)`` spans.
    """
    parts: list[str] = []
    spans: list[tuple[int, int, int, str]] = []
    pos = 0
    for j, (pg, txt) in enumerate(prose_buffer):
        start = pos
        parts.append(txt)
        pos += len(txt)
        end = pos
        spans.append((start, end, pg.page_number, pg.section_title))
        if j < len(prose_buffer) - 1:
            pos += 2
    return "\n\n".join(parts), spans


def save_chunks_json(chunks: list[Chunk], chunks_dir: Path | None = None) -> Path:
    """
    Persist chunks and id→index lookup next to ``chunks.json``.

    Args:
        chunks: Chunk list to serialize.
        chunks_dir: Directory for JSON files (default ``settings.CHUNKS_DIR``).

    Returns:
        Path to ``chunks.json``.
    """
    import json

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

    return path


def ingest_pdf_file(
    pdf_path: Path,
    chunk_size_words: int | None = None,
    overlap_words: int | None = None,
    min_chunk_words: int | None = None,
) -> list[Chunk]:
    """
    End-to-end ingest: parse PDF, clean per page inside chunker, chunk, return list.

    Args:
        pdf_path: Path to a PDF under ``data/raw`` or elsewhere.
        chunk_size_words: Optional chunk size override.
        overlap_words: Optional overlap override.
        min_chunk_words: Optional minimum chunk size override.

    Returns:
        Chunks ready to serialize.
    """
    pages = parse_pdf(pdf_path)
    source = pdf_path.name
    return build_chunks_from_pages(
        pages,
        source,
        chunk_size_words=chunk_size_words,
        overlap_words=overlap_words,
        min_chunk_words=min_chunk_words,
    )
