"""PDF ingestion endpoint: parse, clean, chunk, persist chunks.json."""

import logging
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from config import settings
from ingestion.chunker import (
    build_chunks_from_prepared,
    prepare_cleaned_pages,
    save_chunks_json,
)
from ingestion.models import IngestProcessingStep, IngestResponse
from ingestion.pdf_parser import parse_pdf
from indexing.index_manager import IndexManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

CHUNKS_JSON = settings.CHUNKS_DIR / "chunks.json"


@router.post("/", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(..., description="PDF handbook file"),
    force_rebuild: bool = Query(
        False,
        description="Overwrite existing chunks.json when true",
    ),
) -> IngestResponse:
    """
    Accept a PDF upload, run the ingestion pipeline, and write chunk JSON files.

    Phase 2 additionally builds MinHash, SimHash, TF-IDF, and PageRank artifacts.

    Args:
        file: Multipart PDF upload.
        force_rebuild: When False and ``chunks.json`` already exists, respond 409.

    Returns:
        Summary with chunk counts and per-step durations.

    Raises:
        HTTPException: 400 for invalid input, 409 when chunks exist and not forced.
    """
    t0 = time.perf_counter()
    steps: list[IngestProcessingStep] = []

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload must be a .pdf file")

    if CHUNKS_JSON.exists() and not force_rebuild:
        raise HTTPException(
            status_code=409,
            detail="Chunks already exist; pass force_rebuild=true to overwrite",
        )

    suffix = Path(file.filename).suffix or ".pdf"
    tmp_path = settings.CHUNKS_DIR / f"_upload_{int(t0 * 1000)}{suffix}"

    try:
        settings.CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file upload")

        tmp_path.write_bytes(contents)

        t_parse = time.perf_counter()
        try:
            pages = parse_pdf(tmp_path)
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            logger.exception("PDF parse failed")
            raise HTTPException(
                status_code=400, detail=f"Could not parse PDF: {e}"
            ) from e

        steps.append(
            IngestProcessingStep(
                step="parse",
                duration_s=round(time.perf_counter() - t_parse, 4),
                status="done",
            )
        )

        t_clean = time.perf_counter()
        try:
            prepared = prepare_cleaned_pages(pages)
        except Exception as e:
            logger.exception("Clean failed")
            raise HTTPException(
                status_code=500, detail="Cleaning failed; see server logs"
            ) from e

        steps.append(
            IngestProcessingStep(
                step="clean",
                duration_s=round(time.perf_counter() - t_clean, 4),
                status="done",
            )
        )

        t_chunk = time.perf_counter()
        try:
            safe_name = Path(file.filename).name
            chunks = build_chunks_from_prepared(prepared, safe_name)
            out = save_chunks_json(chunks)
        except Exception as e:
            logger.exception("Chunk failed")
            raise HTTPException(
                status_code=500, detail="Chunking failed; see server logs"
            ) from e

        steps.append(
            IngestProcessingStep(
                step="chunk",
                duration_s=round(time.perf_counter() - t_chunk, 4),
                status="done",
            )
        )

        t_index = time.perf_counter()
        try:
            mgr = IndexManager()
            # Rebuild indexes when chunks are forced to rebuild as well.
            build_results = mgr.build_all(chunks, force=force_rebuild)
        except Exception as e:
            logger.exception("Index build failed")
            raise HTTPException(
                status_code=500, detail="Indexing failed; see server logs"
            ) from e

        total = round(time.perf_counter() - t0, 4)
        page_count = max((p.page_number for p in pages), default=0)
        index_build_time_s = round(time.perf_counter() - t_index, 4)
        methods_indexed = [r.name for r in build_results if r.built]

        logger.info(
            "Ingest complete: %s chunks, %s pages, written %s",
            len(chunks),
            page_count,
            out,
        )

        return IngestResponse(
            status="success",
            chunk_count=len(chunks),
            page_count=page_count,
            source_file=Path(file.filename).name,
            processing_steps=steps,
            total_duration_s=total,
            index_build_time_s=index_build_time_s,
            methods_indexed=methods_indexed,
        )
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError as e:
                logger.warning("Could not remove temp upload %s: %s", tmp_path, e)
