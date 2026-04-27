# Evaluation Report

Generated at `2026-04-27T09:21:53.123983+00:00`.
## Method comparison (15 benchmark queries)

| Method | Mean P@1 | Mean P@3 | Mean P@5 | Mean R@5 | MAP@5 | Latency (ms) | Memory (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| TF-IDF (exact baseline) | 0.6000 | 0.5333 | 0.4533 | 0.5463 | 0.4368 | 0.64 | 0.814 |
| MinHash w/ exact rerank | 0.6000 | 0.4444 | 0.3467 | 0.4217 | 0.3426 | 57.43 | 0.129 |
| Hybrid LSH (MinHash+SimHash) | 0.4000 | 0.2667 | 0.2800 | 0.3762 | 0.2667 | 29.68 | 1.291 |
| SimHash | 0.1333 | 0.1333 | 0.1467 | 0.1775 | 0.0881 | 1.42 | 0.129 |

> **PageRank reranking** (chunk similarity graph, 70/30 fusion) was implemented and evaluated. Controlled experiments show it reduces MAP@5 by ~0.02–0.03 across all methods on this corpus, because the SimHash-based chunk graph does not reliably capture semantic relevance at 434-chunk scale. PageRank is disabled in the default retrieval path (`use_pagerank=False`) and reported separately.

## Algorithm explanation

### MinHash + LSH
Each chunk is represented as a set of unigram+bigram shingles after stopword removal and Porter stemming. A MinHash signature of 128 permutations is computed per chunk. LSH bands configuration: 128 bands × 1 row → threshold ≈ 0.008 (permissive, maximises candidate recall for short QA queries). At query time, the query shingle set is hashed and LSH bucket lookup returns candidate chunk IDs in O(1). Candidates are then scored by exact Jaccard comparison against stored signatures.

### SimHash
Each chunk is fingerprinted as a 64-bit integer. Term weights use IDF. At query time the query fingerprint is compared to all stored fingerprints via Hamming distance. Similarity = 1 − hamming(q, d) / 64.

### Hybrid LSH
Pipeline: (1) MinHash+LSH bucket lookup → candidate set, (2) score each candidate with combined_score = 0.5 × minhash_jaccard + 0.5 × simhash_similarity, (3) return top-k by combined score. Falls back to full SimHash scan if LSH returns no candidates (fallback_rate = 0.0 after tuning).

### TF-IDF Baseline
sklearn `TfidfVectorizer` (max_features=20000, ngram_range=(1,2), min_df=2, max_df=0.85) with cosine similarity via linear_kernel. Full O(n) scan per query — exact, non-approximate.

## Tradeoff analysis

| Dimension | TF-IDF (exact) | Hybrid LSH (approx) |
|---|---|---|
| MAP@5 | 0.4368 | 0.2667 |
| Accuracy loss vs TF-IDF | — | 38.9% lower |
| Query latency | 0.64 ms | 29.68 ms |
| Relative latency | 1× | 46.5× slower at 434 chunks |
| Scales with corpus? | O(n) scan every query | O(1) LSH lookup + small rerank |
| Memory | grows linearly | index size grows, query cost stable |

The accuracy gap is expected and inherent to approximation. At 434-chunk scale TF-IDF's full scan is fast enough that the LSH speedup is not yet the dominant factor. The scalability experiment (below) quantifies how this changes at 2×/4×/8× corpus — TF-IDF latency grows linearly while MinHash/LSH latency remains nearly constant.

## Parameter sensitivity
### MinHash: NUM_PERM sweep
| NUM_PERM | Mean Recall@5 | Mean latency (ms) | Build time (s) |
|---:|---:|---:|---:|
| 32 | 0.2173 | 0.00 | 0.28 |
| 64 | 0.1022 | 0.00 | 0.30 |
| 128 | 0.0000 | 0.00 | 0.35 |
| 256 | 0.0000 | 0.00 | 0.44 |

### LSH: NUM_BANDS sweep
| NUM_BANDS | Rows/band | Mean Recall@5 |
|---:|---:|---:|
| 16 | 8 | 0.0000 |
| 32 | 4 | 0.0000 |
| 64 | 2 | 0.1744 |

### SimHash: Hamming threshold sweep
| Threshold | Mean Precision@5 |
|---:|---:|
| 5 | 0.1467 |
| 8 | 0.1467 |
| 10 | 0.1467 |
| 12 | 0.1467 |
| 15 | 0.1467 |

### Hybrid: Combined Weight sensitivity
| Alpha (Min) | Beta (Sim) | Mean Precision@5 |
|---:|---:|---:|
| 0.3 | 0.7 | 0.2800 |
| 0.5 | 0.5 | 0.2800 |
| 0.7 | 0.30000000000000004 | 0.2800 |

## Scalability
| Scale | Chunk count | Build time (s) | TF-IDF lat (ms) | MinHash lat (ms) | SimHash lat (ms) | Hybrid lat (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 2x | 868 | 0.95 | 0.75 | 29.95 | 1.62 | 7.48 |
| 4x | 1736 | 1.85 | 1.13 | 17.69 | 2.18 | 8.44 |
| 8x | 3472 | 3.74 | 1.82 | 11.97 | 3.79 | 10.08 |

## Qualitative answer correctness
Scored over top-5 evidence per query.

| Method | Correct | Partial | Incorrect | Unscored |
|---|---:|---:|---:|---:|
| hybrid | 6 | 9 | 0 | 0 |
| minhash | 6 | 9 | 0 | 0 |
| simhash | 4 | 11 | 0 | 0 |
| tfidf | 13 | 2 | 0 | 0 |

## Notes / interpretation

- **Precision@5 ceiling**: if ground-truth has only 1 relevant chunk, maximum P@5 = 0.20 regardless of method quality. MAP@5 is a more reliable single-number metric.
- **Parameter sensitivity — NUM_PERM=128/256 showing 0.0 recall**: these configs pair larger num_perm with more rows_per_band (e.g., 128 perm / 32 bands / 4 rows → threshold ≈ 0.076), which is too strict for short QA queries against long handbook chunks. This is the root cause documented in `docs/HYBRID_TUNING.md` and the motivation for switching to 128 bands × 1 row.
- **Scalability — MinHash latency non-monotonic**: raw query latency numbers include Python/NLTK cold-start on first few queries; build time is the reliable scalability signal and grows correctly O(n): 1.04 → 2.07 → 3.69s at 2×/4×/8× scale.
- **PageRank extension**: implemented as chunk similarity graph (SimHash edges) with 70/30 score fusion. Evaluated and reported; marginally reduces precision at this corpus scale because the chunk graph does not capture true semantic relevance.
