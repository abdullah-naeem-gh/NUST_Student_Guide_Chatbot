"""Index presence checks and future load hooks for serialized retrieval indexes."""

from pathlib import Path

from config import settings


def indexes_exist(data_dir: Path | None = None) -> bool:
    """
    Return True if all expected index artifact files exist on disk.

    Actual deserialization is implemented in the indexing phase; startup only
    verifies presence so the API can report status and skip redundant builds.

    Args:
        data_dir: Root data directory; defaults to ``settings.DATA_DIR``.

    Returns:
        Whether minhash, simhash, and tf-idf index files are all present.
    """
    root = data_dir if data_dir is not None else settings.DATA_DIR
    idx = root / "index"
    required = (
        idx / "minhash.pkl",
        idx / "simhash.pkl",
        idx / "tfidf.pkl",
    )
    return all(p.exists() for p in required)


def describe_index_paths(data_dir: Path | None = None) -> dict[str, str]:
    """
    Return absolute paths to index files for logging and diagnostics.

    Args:
        data_dir: Root data directory; defaults to ``settings.DATA_DIR``.

    Returns:
        Mapping of logical name to string path.
    """
    root = data_dir if data_dir is not None else settings.DATA_DIR
    idx = root / "index"
    return {
        "minhash": str((idx / "minhash.pkl").resolve()),
        "simhash": str((idx / "simhash.pkl").resolve()),
        "tfidf": str((idx / "tfidf.pkl").resolve()),
    }
