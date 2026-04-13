"""Score fusion and PageRank reranking utilities (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FusionWeights:
    """Weights for combining retrieval score with PageRank score."""

    retrieval: float = 0.7
    pagerank: float = 0.3


def fuse_scores(
    retrieval_score: float,
    pagerank_score: float,
    weights: FusionWeights | None = None,
) -> float:
    """
    Combine similarity and PageRank into a single final score (INSTRUCTIONS §2.4).

    Args:
        retrieval_score: Similarity score from the retrieval method, expected in [0, 1].
        pagerank_score: Normalized PageRank score in [0, 1].
        weights: Optional weights; defaults to 70/30.

    Returns:
        Final fused score.
    """

    w = weights or FusionWeights()
    return (w.retrieval * float(retrieval_score)) + (w.pagerank * float(pagerank_score))


def normalize_01(value: float, vmin: float, vmax: float) -> float:
    """
    Normalize a scalar to [0, 1] using min/max, guarding degenerate ranges.

    Args:
        value: Raw value.
        vmin: Minimum observed value.
        vmax: Maximum observed value.

    Returns:
        Normalized value in [0, 1].
    """

    if vmax <= vmin:
        return 0.0
    x = (float(value) - float(vmin)) / (float(vmax) - float(vmin))
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x

