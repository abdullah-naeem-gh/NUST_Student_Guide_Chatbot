"""Hybrid MinHash+SimHash combined scorer (CLAUDE.md §Architecture)."""

from __future__ import annotations

from config import settings
from indexing.minhash_lsh import (
    MinHashLshIndex,
    _ensure_stopwords_and_stemmer,
    _normalize_terms,
    build_minhash_signature,
    shingle_k_words,
)
from indexing.simhash import (
    SimHashIndex,
    _ensure_stopwords,
    simhash_fingerprint,
    simhash_similarity,
    tokenize_terms,
)


def score_candidates(
    query: str,
    candidates: list[str],
    mh_idx: MinHashLshIndex,
    sh_idx: SimHashIndex,
    alpha: float | None = None,
    beta: float | None = None,
) -> list[tuple[str, float]]:
    """
    Score a candidate set with combined MinHash Jaccard + SimHash similarity.

    combined_score = alpha * minhash_jaccard + beta * simhash_sim

    Args:
        query: Raw query string.
        candidates: Chunk IDs to score (already filtered by LSH or caller).
        mh_idx: Loaded MinHash+LSH index.
        sh_idx: Loaded SimHash index.
        alpha: Weight for MinHash Jaccard (defaults to settings.HYBRID_MINHASH_WEIGHT).
        beta: Weight for SimHash similarity (defaults to settings.HYBRID_SIMHASH_WEIGHT).

    Returns:
        List of (chunk_id, combined_score) unsorted.
    """
    if alpha is None:
        alpha = float(settings.HYBRID_MINHASH_WEIGHT)
    if beta is None:
        beta = float(settings.HYBRID_SIMHASH_WEIGHT)

    stop, stemmer = _ensure_stopwords_and_stemmer()
    terms = _normalize_terms(query, stop, stemmer)
    use_ub = bool(getattr(settings, "MINHASH_USE_UNIGRAMS_AND_BIGRAMS", False))
    if use_ub:
        shingles = set(terms) | {
            " ".join(terms[i : i + 2]) for i in range(max(0, len(terms) - 1))
        }
    else:
        shingles = shingle_k_words(
            terms, k=int(getattr(settings, "MINHASH_SHINGLE_K_WORDS", 3))
        )
    qsig = build_minhash_signature(shingles, num_perm=settings.MINHASH_NUM_PERM)

    sh_stop = _ensure_stopwords()
    q_fp = simhash_fingerprint(tokenize_terms(query, sh_stop), sh_idx.idf)

    scored: list[tuple[str, float]] = []
    for cid in candidates:
        mh_score = (
            float(qsig.jaccard(mh_idx.signatures[cid]))
            if cid in mh_idx.signatures
            else 0.0
        )
        sh_fp = sh_idx.fingerprints.get(cid)
        sh_score = simhash_similarity(q_fp, sh_fp) if sh_fp is not None else 0.0
        scored.append((cid, alpha * mh_score + beta * sh_score))
    return scored


def query_minhash_candidates(
    query: str,
    mh_idx: MinHashLshIndex,
    preselect_top_n: int | None = None,
) -> list[str]:
    """
    Run LSH query and return candidate chunk IDs, optionally pre-filtered by MinHash Jaccard.

    When preselect_top_n is set, the raw LSH bucket result is re-ranked by approximate
    Jaccard similarity and trimmed to that many candidates before returning.  This prevents
    passing a near-full-corpus candidate list to the expensive SimHash scorer.

    Args:
        query: Raw query string.
        mh_idx: Loaded MinHash+LSH index.
        preselect_top_n: If > 0, keep only this many top-Jaccard candidates.
                         Defaults to settings.MINHASH_LSH_PRESELECT_TOP_N.

    Returns:
        List of candidate chunk IDs from LSH bucket lookup.
    """
    stop, stemmer = _ensure_stopwords_and_stemmer()
    terms = _normalize_terms(query, stop, stemmer)
    use_ub = bool(getattr(settings, "MINHASH_USE_UNIGRAMS_AND_BIGRAMS", False))
    if use_ub:
        shingles = set(terms) | {
            " ".join(terms[i : i + 2]) for i in range(max(0, len(terms) - 1))
        }
    else:
        shingles = shingle_k_words(
            terms, k=int(getattr(settings, "MINHASH_SHINGLE_K_WORDS", 3))
        )
    qsig = build_minhash_signature(shingles, num_perm=settings.MINHASH_NUM_PERM)
    raw = [str(cid) for cid in mh_idx.lsh.query(qsig)]

    if preselect_top_n is None:
        preselect_top_n = int(getattr(settings, "MINHASH_LSH_PRESELECT_TOP_N", 0))

    if preselect_top_n <= 0 or len(raw) <= preselect_top_n:
        return raw

    scored: list[tuple[str, float]] = []
    for cid in raw:
        if cid not in mh_idx.signatures:
            continue
        scored.append((cid, float(qsig.jaccard(mh_idx.signatures[cid]))))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in scored[:preselect_top_n]]
