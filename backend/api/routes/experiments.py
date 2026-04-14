"""Experiments endpoint: expose Phase 5 evaluation results."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from config import settings
from evaluation.experiments import run_all_experiments, run_method_comparison, run_parameter_sensitivity, run_scalability

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _results_path(name: str) -> Path:
    """Return canonical results file path under `data/results/`."""

    return settings.DATA_DIR / "results" / name


def _read_json(path: Path) -> dict:
    """Read a JSON file from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/")
async def get_experiments(
    request: Request,
    refresh: bool = Query(default=False, description="Recompute experiments even if cached JSON exists."),
) -> dict:
    """
    Return Phase 5 experiment results (INSTRUCTIONS §6).

    By default, this returns cached `data/results/experiments.json` when present.
    """

    # Ensure indexes are available (same expectation as /query).
    retriever = getattr(request.app.state, "retriever", None)
    if retriever is None and not refresh:
        # If refresh=True we can still compute from disk, but in normal flow
        # we require the app to have loaded artifacts successfully.
        raise HTTPException(status_code=503, detail="Index not ready")

    combined_path = _results_path("experiments.json")
    if combined_path.exists() and not refresh:
        return _read_json(combined_path)

    try:
        payload = run_all_experiments()
        return payload
    except Exception as e:
        logger.exception("Failed to run experiments")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/method-comparison")
async def get_method_comparison(refresh: bool = False) -> dict:
    """Return (and optionally refresh) method comparison results."""

    p = _results_path("method_comparison.json")
    if p.exists() and not refresh:
        return _read_json(p)
    return run_method_comparison(k=5, use_pagerank=False)


@router.get("/parameter-sensitivity")
async def get_parameter_sensitivity(refresh: bool = False) -> dict:
    """Return (and optionally refresh) parameter sensitivity results."""

    p = _results_path("parameter_sensitivity.json")
    if p.exists() and not refresh:
        return _read_json(p)
    return run_parameter_sensitivity()


@router.get("/scalability")
async def get_scalability(refresh: bool = False) -> dict:
    """Return (and optionally refresh) scalability results."""

    p = _results_path("scalability.json")
    if p.exists() and not refresh:
        return _read_json(p)
    return run_scalability()

