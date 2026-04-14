"""TF-IDF baseline index using scikit-learn (INSTRUCTIONS §2.3)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from config import settings
from ingestion.models import Chunk

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TfidfIndex:
    """
    Serializable TF-IDF index bundle.

    Attributes:
        vectorizer: Fit `TfidfVectorizer`.
        matrix: Sparse TF-IDF matrix (n_chunks x n_features).
        chunk_ids: Chunk ids aligned to matrix rows.
    """

    vectorizer: TfidfVectorizer
    matrix: Any
    chunk_ids: list[str]


def build_tfidf_index(chunks: list[Chunk]) -> TfidfIndex:
    """
    Build TF-IDF vectorizer + corpus matrix using the exact required configuration.

    Args:
        chunks: Chunk list loaded from `data/chunks/chunks.json`.

    Returns:
        Built TF-IDF index bundle.
    """

    vectorizer = TfidfVectorizer(
        max_features=int(getattr(settings, "TFIDF_MAX_FEATURES", 20000)),
        ngram_range=(1, int(getattr(settings, "TFIDF_NGRAM_MAX", 2))),
        min_df=int(getattr(settings, "TFIDF_MIN_DF", 2)),
        max_df=float(getattr(settings, "TFIDF_MAX_DF", 0.85)),
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
        token_pattern=r"\b[a-zA-Z][a-zA-Z0-9]*\b",
    )
    texts = [c.text for c in chunks]
    chunk_ids = [c.id for c in chunks]
    matrix = vectorizer.fit_transform(texts)
    logger.info(
        "TF-IDF built: %s chunks, %s features",
        len(chunk_ids),
        len(getattr(vectorizer, "vocabulary_", {}) or {}),
    )
    return TfidfIndex(vectorizer=vectorizer, matrix=matrix, chunk_ids=chunk_ids)


def save_tfidf_index(index: TfidfIndex, out_path: Path | None = None) -> Path:
    """
    Serialize TF-IDF index via joblib (INSTRUCTIONS §2.3).

    Args:
        index: Built TF-IDF index.
        out_path: Optional output path; defaults to `data/index/tfidf.pkl`.

    Returns:
        Path to the saved artifact.
    """

    path = out_path if out_path is not None else settings.INDEX_DIR / "tfidf.pkl"
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "vectorizer": index.vectorizer,
            "matrix": index.matrix,
            "chunk_ids": np.array(index.chunk_ids, dtype=object),
        },
        path,
    )
    return path


def load_tfidf_index(path: Path | None = None) -> TfidfIndex:
    """
    Load a previously serialized TF-IDF index.

    Args:
        path: Optional path; defaults to `data/index/tfidf.pkl`.

    Returns:
        Deserialized TF-IDF index bundle.
    """

    p = path if path is not None else settings.INDEX_DIR / "tfidf.pkl"
    payload = joblib.load(p)
    chunk_ids = [str(x) for x in payload["chunk_ids"].tolist()]
    return TfidfIndex(
        vectorizer=payload["vectorizer"],
        matrix=payload["matrix"],
        chunk_ids=chunk_ids,
    )

