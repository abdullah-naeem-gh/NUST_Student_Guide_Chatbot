"""PDF ingestion endpoint: parse, clean, chunk, persist chunks.json."""

import logging
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from config import settings
from ingestion.chunker import build_chunks_from_pdf, save_chunks_json
from ingestion.models import IngestProcessingStep, IngestResponse
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

        t_chunk = time.perf_counter()
        try:
            safe_name = Path(file.filename).name
            chunks = build_chunks_from_pdf(tmp_path, safe_name)
            out = save_chunks_json(chunks)
        except Exception as e:
            logger.exception("Semantic chunking failed")
            raise HTTPException(
                status_code=500, detail=f"Chunking failed: {e}"
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
        page_count = max((c.page_end for c in chunks), default=0)
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


@router.post("/from-raw", response_model=IngestResponse)
async def ingest_from_raw(
    force_rebuild: bool = Query(
        False,
        description="Overwrite existing chunks/indexes when true",
    ),
) -> IngestResponse:
    """
    Ingest ALL PDFs present in ``data/raw`` (project demo workflow).

    This is the recommended path when you have multiple handbooks (e.g., UG + PG)
    and want the index to cover both documents.
    """
    t0 = time.perf_counter()
    steps: list[IngestProcessingStep] = []

    if CHUNKS_JSON.exists() and not force_rebuild:
        raise HTTPException(
            status_code=409,
            detail="Chunks already exist; pass force_rebuild=true to overwrite",
        )

    raw_dir = settings.RAW_PDF_DIR
    pdfs = sorted(raw_dir.glob("*.pdf"))
    if not pdfs:
        raise HTTPException(status_code=400, detail=f"No PDFs found in {raw_dir}")

    # Parse + clean + chunk for each PDF, then merge chunk lists and build one index.
    all_chunks = []
    page_count_total = 0
    source_files = []
    chunk_counter = 0

    t_parse = time.perf_counter()
    for pdf_path in pdfs:
        t_chunk = time.perf_counter()
        try:
            chunks = build_chunks_from_pdf(pdf_path, pdf_path.name)
        except Exception as e:
            logger.exception("Chunking failed for %s", pdf_path)
            raise HTTPException(
                status_code=400, detail=f"Could not chunk {pdf_path.name}: {e}"
            ) from e
        # Ensure globally unique, stable chunk IDs across multiple PDFs.
        for c in chunks:
            c.id = f"chunk_{chunk_counter:06d}"
            chunk_counter += 1
        page_count_total += max((c.page_end for c in chunks), default=0)
        source_files.append(pdf_path.name)
        steps.append(
            IngestProcessingStep(
                step=f"chunk:{pdf_path.name}",
                duration_s=round(time.perf_counter() - t_chunk, 4),
                status="done",
            )
        )
        all_chunks.extend(chunks)

    steps.append(
        IngestProcessingStep(
            step="ingest",
            duration_s=round(time.perf_counter() - t_parse, 4),
            status="done",
        )
    )

    t_persist = time.perf_counter()
    out = save_chunks_json(all_chunks)
    steps.append(
        IngestProcessingStep(
            step="persist",
            duration_s=round(time.perf_counter() - t_persist, 4),
            status="done",
        )
    )

    t_index = time.perf_counter()
    try:
        mgr = IndexManager()
        build_results = mgr.build_all(all_chunks, force=True)
    except Exception as e:
        logger.exception("Index build failed")
        raise HTTPException(status_code=500, detail="Indexing failed; see server logs") from e

    index_build_time_s = round(time.perf_counter() - t_index, 4)
    total = round(time.perf_counter() - t0, 4)
    methods_indexed = [r.name for r in build_results if r.built]

    return IngestResponse(
        status="success",
        chunk_count=len(all_chunks),
        page_count=page_count_total,
        source_file=" + ".join(source_files),
        processing_steps=steps,
        total_duration_s=total,
        index_build_time_s=index_build_time_s,
        methods_indexed=methods_indexed,
    )
