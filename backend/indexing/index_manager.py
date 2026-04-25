"""Orchestrate build/load of all indexing artifacts (Phase 2)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from config import settings
from ingestion.models import Chunk
from indexing.minhash_lsh import (
    MinHashLshIndex,
    build_minhash_lsh_index,
    load_minhash_lsh_index,
    save_minhash_lsh_index,
)
from indexing.models import IndexBuildResult, IndexName, file_size_bytes
from indexing.pagerank import (
    PageRankIndex,
    build_pagerank_index,
    load_pagerank_index,
    save_pagerank_index,
)
from indexing.simhash import (
    SimHashIndex,
    build_simhash_index,
    load_simhash_index,
    save_simhash_index,
)
from indexing.fim import FimIndex, build_fim_index, load_fim_index, save_fim_index
from indexing.tfidf_baseline import TfidfIndex, build_tfidf_index, load_tfidf_index, save_tfidf_index

logger = logging.getLogger(__name__)


def load_chunks(path: Path | None = None) -> list[Chunk]:
    """
    Load `chunks.json` into Chunk dataclasses.

    Args:
        path: Optional path; defaults to `data/chunks/chunks.json`.

    Returns:
        Chunk list.
    """

    p = path if path is not None else settings.CHUNKS_DIR / "chunks.json"
    payload = json.loads(p.read_text(encoding="utf-8"))
    return [Chunk(**c) for c in payload]


@dataclass
class IndexArtifacts:
    """
    In-memory handles for loaded indexes.

    Attributes:
        minhash: MinHash+LSH bundle.
        simhash: SimHash bundle.
        tfidf: TF-IDF bundle.
        pagerank: PageRank scores.
    """

    minhash: MinHashLshIndex | None = None
    simhash: SimHashIndex | None = None
    tfidf: TfidfIndex | None = None
    pagerank: PageRankIndex | None = None
    fim: FimIndex | None = None


class IndexManager:
    """Builds and loads all indexing artifacts for the corpus."""

    def __init__(self, index_dir: Path | None = None) -> None:
        """
        Create an IndexManager.

        Args:
            index_dir: Directory containing serialized index artifacts.
        """

        self.index_dir = index_dir if index_dir is not None else settings.INDEX_DIR
        self.artifacts = IndexArtifacts()

    @property
    def paths(self) -> dict[IndexName, Path]:
        """Return canonical artifact paths."""

        return {
            "minhash": self.index_dir / "minhash.pkl",
            "simhash": self.index_dir / "simhash.json",
            "tfidf": self.index_dir / "tfidf.pkl",
            "pagerank": self.index_dir / "pagerank.json",
            "fim": self.index_dir / "fim.json",
        }

    def indexes_exist(self) -> bool:
        """
        Return True if all expected artifacts exist.

        Returns:
            Whether all artifact files exist on disk.
        """

        return all(p.exists() for p in self.paths.values())

    def index_sizes_bytes(self) -> dict[IndexName, int]:
        """
        Get current on-disk artifact sizes.

        Returns:
            Mapping of index name to size in bytes (0 if missing).
        """

        return {k: file_size_bytes(p) for k, p in self.paths.items()}

    def build_all(self, chunks: list[Chunk], force: bool = False) -> list[IndexBuildResult]:
        """
        Build and save all indexes in dependency order.

        Args:
            chunks: Chunk list to index.
            force: When True, rebuild even if artifacts already exist.

        Returns:
            Per-index build summaries.
        """

        self.index_dir.mkdir(parents=True, exist_ok=True)
        results: list[IndexBuildResult] = []

        # MinHash + LSH
        results.append(self._build_one("minhash", force, chunks))

        # TF-IDF
        results.append(self._build_one("tfidf", force, chunks))

        # SimHash (requires TF-IDF weights; computed internally from corpus)
        results.append(self._build_one("simhash", force, chunks))

        # PageRank (uses SimHash fingerprints for near-duplicate edges)
        results.append(self._build_one("pagerank", force, chunks))

        # FIM (query expansion via frequent co-occurrences — optional, non-blocking)
        results.append(self._build_one("fim", force, chunks))

        return results

    def _build_one(self, name: IndexName, force: bool, chunks: list[Chunk]) -> IndexBuildResult:
        """
        Build a single index if needed.

        Args:
            name: Index name.
            force: Whether to rebuild if file exists.
            chunks: Chunk list.

        Returns:
            Build result summary.
        """

        out_path = self.paths[name]
        if out_path.exists() and not force:
            return IndexBuildResult(
                name=name,
                built=False,
                path=str(out_path.resolve()),
                size_bytes=file_size_bytes(out_path),
                build_time_s=0.0,
            )

        t0 = time.perf_counter()
        if name == "minhash":
            idx = build_minhash_lsh_index(chunks)
            save_minhash_lsh_index(idx, out_path)
            self.artifacts.minhash = idx
        elif name == "tfidf":
            idx = build_tfidf_index(chunks)
            save_tfidf_index(idx, out_path)
            self.artifacts.tfidf = idx
        elif name == "simhash":
            idx = build_simhash_index(chunks)
            save_simhash_index(idx, out_path)
            self.artifacts.simhash = idx
        elif name == "pagerank":
            if self.artifacts.simhash is None:
                # Ensure fingerprints exist for PageRank edges.
                if self.paths["simhash"].exists() and not force:
                    self.artifacts.simhash = load_simhash_index(self.paths["simhash"])
                else:
                    self.artifacts.simhash = build_simhash_index(chunks)
            idx = build_pagerank_index(chunks, self.artifacts.simhash.fingerprints)
            save_pagerank_index(idx, out_path)
            self.artifacts.pagerank = idx
        elif name == "fim":
            idx = build_fim_index(
                chunks,
                min_support=int(settings.FIM_MIN_SUPPORT),
                max_itemset_size=int(settings.FIM_MAX_ITEMSET_SIZE),
            )
            save_fim_index(idx, out_path)
            self.artifacts.fim = idx
        else:
            raise ValueError(f"Unknown index name: {name}")

        dt = round(time.perf_counter() - t0, 4)
        return IndexBuildResult(
            name=name,
            built=True,
            path=str(out_path.resolve()),
            size_bytes=file_size_bytes(out_path),
            build_time_s=dt,
        )

    def load_all(self) -> IndexArtifacts:
        """
        Load all existing artifacts into memory.

        Returns:
            Loaded artifacts bundle.
        """

        self.artifacts.minhash = load_minhash_lsh_index(self.paths["minhash"])
        self.artifacts.simhash = load_simhash_index(self.paths["simhash"])
        self.artifacts.tfidf = load_tfidf_index(self.paths["tfidf"])
        self.artifacts.pagerank = load_pagerank_index(self.paths["pagerank"])
        fim_path = self.paths["fim"]
        if fim_path.exists():
            self.artifacts.fim = load_fim_index(fim_path)
        else:
            logger.warning("FIM index not found at %s — query expansion disabled", fim_path)
        return self.artifacts

