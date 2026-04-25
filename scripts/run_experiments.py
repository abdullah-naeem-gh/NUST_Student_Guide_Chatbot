#!/usr/bin/env python3
"""CLI entry point for running all retrieval experiments.

Usage:
    python scripts/run_experiments.py [--experiment {all,comparison,sensitivity,scalability}]

Results are written to data/results/ as JSON files.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add backend to path so imports resolve without installation.
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from evaluation.experiments import (
    run_all_experiments,
    run_method_comparison,
    run_parameter_sensitivity,
    run_scalability,
)
from indexing.index_manager import IndexManager
from retrieval.retriever import Retriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _build_retriever() -> Retriever:
    mgr = IndexManager()
    mgr.load_all()
    return Retriever(mgr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BDA retrieval experiments")
    parser.add_argument(
        "--experiment",
        choices=["all", "comparison", "sensitivity", "scalability"],
        default="all",
        help="Which experiment to run (default: all)",
    )
    args = parser.parse_args()

    logger.info("Loading indexes…")
    retriever = _build_retriever()

    if args.experiment == "all":
        logger.info("Running all experiments")
        run_all_experiments()
    elif args.experiment == "comparison":
        logger.info("Running method comparison")
        run_method_comparison()
    elif args.experiment == "sensitivity":
        logger.info("Running parameter sensitivity")
        run_parameter_sensitivity()
    elif args.experiment == "scalability":
        logger.info("Running scalability experiment")
        run_scalability()

    logger.info("Done. Results written to data/results/")


if __name__ == "__main__":
    main()
