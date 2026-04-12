"""Health and connectivity endpoints."""

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/ping")
async def ping(request: Request) -> dict[str, str | bool]:
    """
    Liveness check and index readiness flag for the demo UI.

    Returns:
        Status payload with ``indexed`` True when all index files exist on disk.
    """
    indexed = bool(getattr(request.app.state, "indexed", False))
    logger.debug("Ping: indexed=%s", indexed)
    return {"status": "ok", "indexed": indexed}
