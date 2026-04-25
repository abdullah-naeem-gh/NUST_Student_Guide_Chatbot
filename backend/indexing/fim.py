"""Frequent Itemset Mining for query expansion via corpus term co-occurrences.

Pipeline:
  1. Tokenize each chunk into a set of stemmed unigrams (stopwords removed).
  2. Run FP-Growth on the token-set corpus to find frequent pairs/triples.
  3. Build a co-occurrence map: term → {co-occurring terms with frequency ≥ min_support}.
  4. At query time: for each query term, append its top-N co-occurring partners.

This attacks vocabulary mismatch: "academically deficient" → corpus itemsets surface
"probation", "warning", "cgpa" as frequent co-occurrences → expanded query hits those chunks.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ingestion.models import Chunk
from indexing.minhash_lsh import _ensure_stopwords_and_stemmer, _normalize_terms


def _compute_stemmed_idf(transactions: list[frozenset[str]]) -> dict[str, float]:
    """Compute IDF over stemmed token sets (consistent with FIM tokenization)."""
    import math
    n = len(transactions)
    if n == 0:
        return {}
    df: dict[str, int] = defaultdict(int)
    for tx in transactions:
        for t in tx:
            df[t] += 1
    # sklearn-style smooth IDF: log((1+n)/(1+df)) + 1
    return {t: math.log((1.0 + n) / (1.0 + d)) + 1.0 for t, d in df.items()}

logger = logging.getLogger(__name__)


@dataclass
class FimIndex:
    """Stores the co-occurrence map mined from the corpus."""

    # term → list of (co_term, support_count), sorted descending
    cooccurrence: dict[str, list[tuple[str, int]]] = field(default_factory=dict)
    # stemmed term → IDF weight from TF-IDF vectorizer (used to filter generic expansions)
    idf: dict[str, float] = field(default_factory=dict)
    min_support: int = 3
    max_itemset_size: int = 3


def _tokenize_chunk(text: str, stop: set, stemmer) -> frozenset[str]:
    terms = _normalize_terms(text, stop, stemmer)
    return frozenset(terms)


def _fp_growth_pairs_and_triples(
    transactions: list[frozenset[str]],
    min_support: int,
    max_size: int,
) -> dict[frozenset[str], int]:
    """
    Simple in-memory FP-Growth approximation using a two-pass approach.

    For typical handbook corpora (~500–2000 chunks, ~5000 unique terms) this is fast
    enough without needing the full FP-tree structure.  We use a candidate-generation
    approach: mine frequent singletons, then generate and count pairs/triples only
    from frequent items (Apriori anti-monotone pruning).
    """
    # Pass 1: frequent singletons
    singleton_counts: dict[str, int] = defaultdict(int)
    for tx in transactions:
        for t in tx:
            singleton_counts[t] += 1

    freq_items = frozenset(t for t, c in singleton_counts.items() if c >= min_support)
    freq_items_list = sorted(freq_items)

    result: dict[frozenset[str], int] = {}

    # Frequent singletons
    for t in freq_items_list:
        result[frozenset([t])] = singleton_counts[t]

    if max_size < 2:
        return result

    # Pass 2: frequent pairs — only from freq_items (anti-monotone)
    pair_counts: dict[frozenset[str], int] = defaultdict(int)
    for tx in transactions:
        filtered = sorted(tx & freq_items)
        for i in range(len(filtered)):
            for j in range(i + 1, len(filtered)):
                pair_counts[frozenset([filtered[i], filtered[j]])] += 1

    freq_pairs = {p: c for p, c in pair_counts.items() if c >= min_support}
    result.update(freq_pairs)

    if max_size < 3:
        return result

    # Pass 3: frequent triples — extend frequent pairs
    triple_counts: dict[frozenset[str], int] = defaultdict(int)
    freq_pair_list = [sorted(p) for p in freq_pairs]
    for tx in transactions:
        filtered = sorted(tx & freq_items)
        filtered_set = set(filtered)
        for pair in freq_pair_list:
            if not (pair[0] in filtered_set and pair[1] in filtered_set):
                continue
            for ext in filtered:
                if ext > pair[1]:  # canonical ordering to avoid duplicates
                    triple_counts[frozenset([pair[0], pair[1], ext])] += 1

    result.update({t: c for t, c in triple_counts.items() if c >= min_support})
    return result


def build_fim_index(
    chunks: list[Chunk],
    min_support: int = 3,
    max_itemset_size: int = 3,
) -> FimIndex:
    """Mine frequent itemsets from the chunk corpus and build the co-occurrence map."""
    stop, stemmer = _ensure_stopwords_and_stemmer()
    transactions = [_tokenize_chunk(c.text, stop, stemmer) for c in chunks]
    logger.info("FIM: mining %d transactions with min_support=%d", len(transactions), min_support)

    itemsets = _fp_growth_pairs_and_triples(transactions, min_support, max_itemset_size)
    logger.info("FIM: found %d frequent itemsets", len(itemsets))

    # Build co-occurrence map: for each pair/triple, each member co-occurs with the others
    cooccurrence: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for itemset, count in itemsets.items():
        if len(itemset) < 2:
            continue
        items = list(itemset)
        for i, a in enumerate(items):
            for b in items:
                if a != b:
                    cooccurrence[a][b] += count

    # Rank co-terms by support × IDF: balances how often they co-occur (support)
    # with how discriminative they are (IDF).  Pure support favours generic terms;
    # pure IDF favours rare noise.  The product rewards terms that are both
    # frequent co-occurrences AND semantically specific to the topic area.
    idf_weights = _compute_stemmed_idf(transactions)
    sorted_cooc: dict[str, list[tuple[str, int]]] = {
        term: sorted(
            partners.items(),
            key=lambda x: x[1] * idf_weights.get(x[0], 1.0),
            reverse=True,
        )
        for term, partners in cooccurrence.items()
    }

    logger.info("FIM: computed %d stemmed IDF weights for expansion filtering", len(idf_weights))

    return FimIndex(
        cooccurrence=sorted_cooc,
        idf=idf_weights,
        min_support=min_support,
        max_itemset_size=max_itemset_size,
    )


def expand_query(
    query: str,
    fim_index: FimIndex,
    top_n_per_term: int = 3,
    min_idf: float = 3.0,
) -> str:
    """
    Expand a query using corpus frequent co-occurrences, filtered by IDF.

    Only co-occurring terms with IDF ≥ min_idf are added — this excludes
    near-universal terms like "student" or "nust" (low IDF) that appear in
    almost every chunk and dilute retrieval signal.

    Args:
        query: Raw user query.
        fim_index: Loaded FimIndex.
        top_n_per_term: How many co-occurring terms to add per query term.
        min_idf: Minimum IDF for an expansion term to be accepted.

    Returns:
        Expanded query string (original + appended discriminative co-terms).
    """
    if not fim_index.cooccurrence:
        return query

    stop, stemmer = _ensure_stopwords_and_stemmer()
    query_terms = _normalize_terms(query, stop, stemmer)

    added: set[str] = set(query_terms)
    expansions: list[str] = []
    for term in query_terms:
        partners = fim_index.cooccurrence.get(term, [])
        count = 0
        for co_term, _support in partners:
            if count >= top_n_per_term:
                break
            if co_term in added:
                continue
            # Skip low-IDF generic terms — they pollute all retrieval methods
            if fim_index.idf and fim_index.idf.get(co_term, 0.0) < min_idf:
                continue
            expansions.append(co_term)
            added.add(co_term)
            count += 1

    if not expansions:
        return query

    expanded = query + " " + " ".join(expansions)
    logger.debug("FIM expand: %r → %r", query, expanded)
    return expanded


def save_fim_index(index: FimIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "min_support": index.min_support,
        "max_itemset_size": index.max_itemset_size,
        "idf": index.idf,
        "cooccurrence": {
            term: [[co, cnt] for co, cnt in partners]
            for term, partners in index.cooccurrence.items()
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.info("FIM index saved to %s (%d KB)", path, path.stat().st_size // 1024)


def load_fim_index(path: Path) -> FimIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cooccurrence = {
        term: [(co, cnt) for co, cnt in partners]
        for term, partners in payload["cooccurrence"].items()
    }
    return FimIndex(
        cooccurrence=cooccurrence,
        idf={str(k): float(v) for k, v in payload.get("idf", {}).items()},
        min_support=int(payload["min_support"]),
        max_itemset_size=int(payload["max_itemset_size"]),
    )
