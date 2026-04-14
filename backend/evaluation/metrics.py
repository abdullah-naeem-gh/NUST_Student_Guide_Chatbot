"""Evaluation metrics for retrieval experiments (Phase 5)."""

from __future__ import annotations

from collections.abc import Iterable


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """
    Compute Precision@k.

    Args:
        retrieved: Ranked list of retrieved chunk ids.
        relevant: Set of relevant (ground-truth) chunk ids.
        k: Cutoff.

    Returns:
        Precision@k in [0, 1].
    """

    if k <= 0:
        return 0.0
    if not relevant:
        return 0.0
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k) & relevant)
    return hits / float(k)


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """
    Compute Recall@k.

    Args:
        retrieved: Ranked list of retrieved chunk ids.
        relevant: Set of relevant (ground-truth) chunk ids.
        k: Cutoff.

    Returns:
        Recall@k in [0, 1].
    """

    if k <= 0:
        return 0.0
    if not relevant:
        return 0.0
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k) & relevant)
    return hits / float(len(relevant))


def average_precision(retrieved: list[str], relevant: set[str], k: int | None = None) -> float:
    """
    Compute average precision for a single query.

    This is the mean of precision@i at each rank i where the item is relevant.

    Args:
        retrieved: Ranked list of retrieved ids.
        relevant: Set of relevant ids.
        k: Optional cutoff. When provided, only considers the first k retrieved items.

    Returns:
        Average precision in [0, 1].
    """

    if not relevant:
        return 0.0
    if k is None:
        retrieved_k = retrieved
    else:
        if k <= 0:
            return 0.0
        retrieved_k = retrieved[:k]

    hit_count = 0
    ap_sum = 0.0
    for i, cid in enumerate(retrieved_k, start=1):
        if cid in relevant:
            hit_count += 1
            ap_sum += hit_count / float(i)
    if hit_count == 0:
        return 0.0
    return ap_sum / float(len(relevant))


def mean_average_precision(results_per_query: Iterable[tuple[list[str], set[str]]], k: int | None = None) -> float:
    """
    Compute mean average precision (MAP) across queries.

    Args:
        results_per_query: Iterable of (retrieved_ids, relevant_set).
        k: Optional cutoff passed to average_precision.

    Returns:
        MAP in [0, 1].
    """

    aps: list[float] = []
    for retrieved, relevant in results_per_query:
        aps.append(average_precision(retrieved=retrieved, relevant=relevant, k=k))
    return (sum(aps) / float(len(aps))) if aps else 0.0

