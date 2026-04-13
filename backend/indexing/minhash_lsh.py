"""MinHash + LSH index built with `datasketch` (INSTRUCTIONS §2.1)."""

from __future__ import annotations

import logging
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

from datasketch import MinHash, MinHashLSH

from config import settings
from ingestion.models import Chunk

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*\b")
_SHINGLE_K_WORDS = 3


def _ensure_stopwords_and_stemmer() -> tuple[set[str], object]:
    """
    Load NLTK stopwords and a Porter stemmer.

    Returns:
        Stopword set and stemmer.
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
    from nltk.stem import PorterStemmer

    return set(stopwords.words("english")), PorterStemmer()


def _normalize_terms(text: str, stop: set[str], stemmer: object) -> list[str]:
    """
    Normalize text for MinHash: lowercase, remove stopwords, stem.

    Args:
        text: Input text.
        stop: Stopword set.
        stemmer: Porter stemmer instance.

    Returns:
        Normalized term sequence.
    """

    terms = [t.lower() for t in _WORD_RE.findall(text)]
    filtered = [t for t in terms if t not in stop]
    stem = getattr(stemmer, "stem")
    return [stem(t) for t in filtered]


def shingle_k_words(terms: list[str], k: int = _SHINGLE_K_WORDS) -> set[str]:
    """
    Create word-level k-shingles (INSTRUCTIONS §2.1).

    Args:
        terms: Normalized term sequence.
        k: Shingle size in words (default 3).

    Returns:
        Set of shingles as space-joined strings.
    """

    if k <= 0:
        return set()
    if len(terms) < k:
        return {" ".join(terms)} if terms else set()
    return {" ".join(terms[i : i + k]) for i in range(0, len(terms) - k + 1)}


def build_minhash_signature(shingles: set[str], num_perm: int) -> MinHash:
    """
    Build a MinHash signature for one shingle set.

    Args:
        shingles: Set representation.
        num_perm: Number of permutations (hash functions).

    Returns:
        `datasketch.MinHash` with updated signature.
    """

    m = MinHash(num_perm=num_perm)
    for s in shingles:
        m.update(s.encode("utf-8"))
    return m


@dataclass(frozen=True)
class MinHashLshIndex:
    """
    MinHash+LSH index bundle.

    Attributes:
        lsh: LSH structure mapping chunk_id -> bucketed signature.
        signatures: Chunk id -> MinHash signature object (for signature-based Jaccard rerank).
    """

    lsh: MinHashLSH
    signatures: dict[str, MinHash]


def build_minhash_lsh_index(chunks: list[Chunk]) -> MinHashLshIndex:
    """
    Build MinHash signatures and LSH index with required parameters.

    Uses NUM_PERM=128 and LSH bands×rows = 32×4.

    Args:
        chunks: Chunk list.

    Returns:
        Built MinHash+LSH bundle.
    """

    num_perm = settings.MINHASH_NUM_PERM
    if settings.LSH_NUM_BANDS * settings.LSH_ROWS_PER_BAND != num_perm:
        raise ValueError(
            "Invalid LSH config: LSH_NUM_BANDS * LSH_ROWS_PER_BAND must equal MINHASH_NUM_PERM"
        )

    stop, stemmer = _ensure_stopwords_and_stemmer()
    lsh = MinHashLSH(num_perm=num_perm, params=(settings.LSH_NUM_BANDS, settings.LSH_ROWS_PER_BAND))
    signatures: dict[str, MinHash] = {}

    for c in chunks:
        terms = _normalize_terms(c.text, stop, stemmer)
        shingles = shingle_k_words(terms, k=_SHINGLE_K_WORDS)
        sig = build_minhash_signature(shingles, num_perm=num_perm)
        signatures[c.id] = sig
        lsh.insert(c.id, sig)

    logger.info("MinHash+LSH built: %s signatures", len(signatures))
    return MinHashLshIndex(lsh=lsh, signatures=signatures)


def save_minhash_lsh_index(index: MinHashLshIndex, out_path: Path | None = None) -> Path:
    """
    Serialize MinHash+LSH index via pickle (INSTRUCTIONS §2.1).

    Args:
        index: Built index bundle.
        out_path: Optional path; defaults to `data/index/minhash.pkl`.

    Returns:
        Path to saved artifact.
    """

    path = out_path if out_path is not None else settings.INDEX_DIR / "minhash.pkl"
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump({"lsh": index.lsh, "signatures": index.signatures}, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def load_minhash_lsh_index(path: Path | None = None) -> MinHashLshIndex:
    """
    Load a serialized MinHash+LSH index.

    Args:
        path: Optional path; defaults to `data/index/minhash.pkl`.

    Returns:
        Deserialized index bundle.
    """

    p = path if path is not None else settings.INDEX_DIR / "minhash.pkl"
    with p.open("rb") as f:
        payload = pickle.load(f)
    return MinHashLshIndex(lsh=payload["lsh"], signatures=payload["signatures"])

