"""Serves handbook PDFs from data/raw for the embedded viewer in the frontend."""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pdf"])


@router.get("/pdf", summary="Serve a handbook PDF from data/raw")
async def serve_pdf(
    file: str | None = Query(
        None,
        description="PDF filename inside data/raw (e.g. UG_Handbook.pdf). "
        "If omitted, prefers UG / handbook naming then the first PDF.",
    ),
):
    """
    Stream a PDF from the data/raw directory.

    The frontend loads it in react-pdf-viewer and jumps to chunk pages.
    """
    pdf_dir = settings.RAW_PDF_DIR
    candidates = list(pdf_dir.glob("*.pdf"))

    if not candidates:
        logger.warning("No PDF found in %s", pdf_dir)
        raise HTTPException(status_code=404, detail="PDF not found. Please ingest a document first.")

    by_name = {p.name: p for p in candidates}

    if file:
        safe = file.strip()
        if not safe or safe != file or "/" in safe or "\\" in safe or ".." in safe:
            raise HTTPException(status_code=400, detail="Invalid file name")
        preferred = by_name.get(safe)
        if preferred is None or not preferred.is_file():
            raise HTTPException(status_code=404, detail="Requested PDF not found in data/raw")
    else:
        # Prefer the NUST handbook by name, fall back to first PDF available
        preferred = next(
            (p for p in candidates if "handbook" in p.name.lower() or "ug" in p.name.lower()),
            candidates[0],
        )

    logger.info("Serving PDF: %s", preferred.name)
    # Starlette defaults to Content-Disposition: attachment when filename= is set,
    # which forces a download instead of embedding in <iframe>. Use inline explicitly.
    return FileResponse(
        path=str(preferred),
        media_type="application/pdf",
        filename=preferred.name,
        content_disposition_type="inline",
    )
