"""TF-IDF weighted SimHash implementation (INSTRUCTIONS §2.2)."""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import mmh3

from config import settings
from ingestion.models import Chunk

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*\b")


def _ensure_stopwords() -> set[str]:
    """
    Load NLTK stopwords; download into `backend/nltk_data` if missing.

    Returns:
        Stopword set for English.
    """

    import nltk

    from pathlib import Path as _Path

    data_dir = _Path(__file__).resolve().parent.parent / "nltk_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    nltk_dir = str(data_dir)
    if nltk_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_dir)
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        logger.info("Downloading NLTK stopwords to %s", data_dir)
        nltk.download("stopwords", download_dir=nltk_dir, quiet=True)
    from nltk.corpus import stopwords

    return set(stopwords.words("english"))


def tokenize_terms(text: str, stopwords: set[str]) -> list[str]:
    """
    Tokenize chunk text into terms for SimHash (lowercase, no stopwords).

    Args:
        text: Input text.
        stopwords: Stopword set.

    Returns:
        List of normalized terms.
    """

    terms = [t.lower() for t in _WORD_RE.findall(text)]
    return [t for t in terms if t not in stopwords]


def hamming_distance(a: int, b: int) -> int:
    """
    Compute Hamming distance between two 64-bit fingerprints.

    Args:
        a: Fingerprint A.
        b: Fingerprint B.

    Returns:
        Hamming distance in [0, 64].
    """

    return (a ^ b).bit_count()


def simhash_similarity(a: int, b: int) -> float:
    """
    Convert Hamming distance into similarity score in [0, 1].

    Args:
        a: Fingerprint A.
        b: Fingerprint B.

    Returns:
        Similarity score.
    """

    return 1.0 - (hamming_distance(a, b) / 64.0)


def _hash64(term: str) -> int:
    """
    Hash a term to an unsigned 64-bit integer via MurmurHash3.

    Args:
        term: Input term.

    Returns:
        64-bit unsigned integer.
    """

    lo, _hi = mmh3.hash64(term, signed=False)
    return int(lo)


def compute_idf(doc_terms: list[list[str]]) -> tuple[dict[str, float], set[str]]:
    """
    Compute IDF values over the corpus.

    Args:
        doc_terms: Tokenized terms per chunk.

    Returns:
        (idf mapping, allowed term set after df filtering).
    """

    n_docs = len(doc_terms)
    df: Counter[str] = Counter()
    for terms in doc_terms:
        df.update(set(terms))

    min_df = int(getattr(settings, "SIMHASH_MIN_DF", 2))
    max_df = float(getattr(settings, "SIMHASH_MAX_DF", 0.85))
    allowed: set[str] = set()
    for term, d in df.items():
        if d < min_df:
            continue
        if (float(d) / float(max(1, n_docs))) > max_df:
            continue
        allowed.add(term)

    idf: dict[str, float] = {}
    for term, d in df.items():
        if term not in allowed:
            continue
        # Smooth to avoid div-by-zero and keep weights stable.
        idf[term] = math.log((1.0 + n_docs) / (1.0 + d)) + 1.0
    return idf, allowed


def simhash_fingerprint(terms: list[str], idf: dict[str, float]) -> int:
    """
    Compute TF-IDF weighted SimHash fingerprint packed into 64-bit integer.

    Args:
        terms: Tokenized terms for one document.
        idf: Corpus IDF map.

    Returns:
        64-bit fingerprint integer.
    """

    if not terms:
        return 0
    tf = Counter(terms)
    vec = [0.0] * 64
    for term, f in tf.items():
        idf_w = float(idf.get(term, 0.0))
        if idf_w <= 0.0:
            continue
        if bool(getattr(settings, "SIMHASH_SUBLINEAR_TF", True)):
            w = (1.0 + math.log(float(f))) * idf_w
        else:
            w = float(f) * idf_w
        h = _hash64(term)
        for i in range(64):
            bit = (h >> i) & 1
            vec[i] += w if bit == 1 else -w
    fp = 0
    for i, v in enumerate(vec):
        if v > 0:
            fp |= 1 << i
    return fp


@dataclass(frozen=True)
class SimHashIndex:
    """
    SimHash index bundle.

    Attributes:
        fingerprints: Chunk id -> fingerprint.
        idf: Term idf mapping used to compute weights.
    """

    fingerprints: dict[str, int]
    idf: dict[str, float]
    allowed_terms: set[str]


def build_simhash_index(chunks: list[Chunk]) -> SimHashIndex:
    """
    Build TF-IDF weighted SimHash fingerprints for all chunks.

    Args:
        chunks: Chunk list.

    Returns:
        Built SimHash index.
    """

    stop = _ensure_stopwords()
    docs = [tokenize_terms(c.text, stop) for c in chunks]
    idf, allowed = compute_idf(docs)
    docs_f = [[t for t in terms if t in allowed] for terms in docs]
    fingerprints = {c.id: simhash_fingerprint(docs_f[i], idf) for i, c in enumerate(chunks)}
    logger.info("SimHash built: %s fingerprints", len(fingerprints))
    return SimHashIndex(fingerprints=fingerprints, idf=idf, allowed_terms=allowed)


def save_simhash_index(index: SimHashIndex, out_path: Path | None = None) -> Path:
    """
    Save SimHash index as JSON (INSTRUCTIONS §2.2).

    Args:
        index: SimHash index.
        out_path: Optional output path; defaults to `data/index/simhash.json`.

    Returns:
        Path to saved JSON.
    """

    path = out_path if out_path is not None else settings.INDEX_DIR / "simhash.json"
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "fingerprints": {k: int(v) for k, v in index.fingerprints.items()},
        "idf": index.idf,
        "allowed_terms": sorted(index.allowed_terms),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def load_simhash_index(path: Path | None = None) -> SimHashIndex:
    """
    Load a serialized SimHash index.

    Args:
        path: Optional path; defaults to `data/index/simhash.json`.

    Returns:
        Deserialized SimHash index.
    """

    p = path if path is not None else settings.INDEX_DIR / "simhash.json"
    payload = json.loads(p.read_text(encoding="utf-8"))
    fps = {str(k): int(v) for k, v in payload["fingerprints"].items()}
    idf = {str(k): float(v) for k, v in payload.get("idf", {}).items()}
    allowed = set(str(x) for x in payload.get("allowed_terms", []))
    return SimHashIndex(fingerprints=fps, idf=idf, allowed_terms=allowed)

