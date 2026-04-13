"""PageRank over chunk cross-references and near-duplicates (INSTRUCTIONS §2.4)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import networkx as nx

from config import settings
from ingestion.models import Chunk
from indexing.simhash import hamming_distance

logger = logging.getLogger(__name__)

_REF_PATTERNS = (
    re.compile(r"[Ss]ection\s+(\d+(?:\.\d+)*)"),
    re.compile(r"[Aa]rticle\s+(\d+)"),
    re.compile(r"[Cc]lause\s+(\d+)"),
)


def _extract_reference_keys(text: str) -> set[str]:
    """
    Extract normalized reference keys from chunk text.

    Args:
        text: Chunk text.

    Returns:
        Set of reference keys (e.g. "3.2", "12").
    """

    keys: set[str] = set()
    for pat in _REF_PATTERNS:
        for m in pat.finditer(text):
            keys.add(m.group(1))
    return keys


def _section_keys_from_title(title: str) -> set[str]:
    """
    Extract section-like identifiers from section titles.

    Args:
        title: Section title string.

    Returns:
        Set of numeric keys found in the title.
    """

    if not title:
        return set()
    return set(re.findall(r"\b\d+(?:\.\d+)*\b", title))


def _build_reference_resolution_map(chunks: list[Chunk]) -> dict[str, str]:
    """
    Map a reference key (e.g. "3.2") to a target chunk_id using section titles.

    Args:
        chunks: Chunk list.

    Returns:
        Mapping key -> chunk_id (first occurrence wins).
    """

    mapping: dict[str, str] = {}
    for c in chunks:
        for k in _section_keys_from_title(c.section_title):
            mapping.setdefault(k, c.id)
    return mapping


def _add_simhash_edges(G: nx.DiGraph, fingerprints: dict[str, int], max_hamming: int = 5) -> int:
    """
    Add directed edges between near-duplicate chunks using SimHash distance.

    Args:
        G: Graph to mutate.
        fingerprints: Chunk id -> fingerprint.
        max_hamming: Strict distance threshold (<5 per spec; we use <=4).

    Returns:
        Number of edges added.
    """

    items = list(fingerprints.items())
    n = len(items)
    if n <= 1:
        return 0

    threshold = max_hamming - 1
    edges = 0

    # Fast path for small corpora.
    if n <= 5000:
        for i in range(n):
            id_a, fp_a = items[i]
            for j in range(i + 1, n):
                id_b, fp_b = items[j]
                if hamming_distance(fp_a, fp_b) <= threshold:
                    G.add_edge(id_a, id_b)
                    G.add_edge(id_b, id_a)
                    edges += 2
        return edges

    # Scaled path: bucket by 16-bit prefix to reduce comparisons.
    buckets: dict[int, list[tuple[str, int]]] = {}
    for cid, fp in items:
        buckets.setdefault((fp >> 48) & 0xFFFF, []).append((cid, fp))

    for b in buckets.values():
        m = len(b)
        for i in range(m):
            id_a, fp_a = b[i]
            for j in range(i + 1, m):
                id_b, fp_b = b[j]
                if hamming_distance(fp_a, fp_b) <= threshold:
                    G.add_edge(id_a, id_b)
                    G.add_edge(id_b, id_a)
                    edges += 2
    return edges


@dataclass(frozen=True)
class PageRankIndex:
    """
    PageRank scores keyed by chunk_id.

    Attributes:
        scores: Chunk id -> score.
    """

    scores: dict[str, float]


def build_pagerank_index(chunks: list[Chunk], simhash_fingerprints: dict[str, int]) -> PageRankIndex:
    """
    Build a directed chunk graph from cross-references and near-duplicate SimHash edges.

    Args:
        chunks: Chunk list.
        simhash_fingerprints: Chunk id -> SimHash fingerprint.

    Returns:
        PageRank score map.
    """

    G = nx.DiGraph()
    for c in chunks:
        G.add_node(c.id)

    resolver = _build_reference_resolution_map(chunks)
    ref_edges = 0
    for c in chunks:
        for key in _extract_reference_keys(c.text):
            target = resolver.get(key)
            if target and target != c.id:
                G.add_edge(c.id, target)
                ref_edges += 1

    sim_edges = _add_simhash_edges(G, simhash_fingerprints, max_hamming=5)
    logger.info("PageRank graph: %s nodes, %s ref edges, %s simhash edges", G.number_of_nodes(), ref_edges, sim_edges)

    scores = nx.pagerank(G, alpha=0.85, max_iter=100)
    return PageRankIndex(scores={str(k): float(v) for k, v in scores.items()})


def save_pagerank_index(index: PageRankIndex, out_path: Path | None = None) -> Path:
    """
    Save PageRank scores as JSON.

    Args:
        index: PageRank index.
        out_path: Optional output path; defaults to `data/index/pagerank.json`.

    Returns:
        Saved artifact path.
    """

    path = out_path if out_path is not None else settings.INDEX_DIR / "pagerank.json"
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"scores": index.scores}, ensure_ascii=False), encoding="utf-8")
    return path


def load_pagerank_index(path: Path | None = None) -> PageRankIndex:
    """
    Load PageRank JSON.

    Args:
        path: Optional path; defaults to `data/index/pagerank.json`.

    Returns:
        Deserialized PageRank index.
    """

    p = path if path is not None else settings.INDEX_DIR / "pagerank.json"
    payload = json.loads(p.read_text(encoding="utf-8"))
    scores = {str(k): float(v) for k, v in payload.get("scores", {}).items()}
    return PageRankIndex(scores=scores)

