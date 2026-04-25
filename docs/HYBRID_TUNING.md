# Hybrid Retriever Tuning — Before vs After

## Problem

The original hybrid retriever (MinHash+LSH candidate filter → combined MinHash/SimHash scorer)
was producing worse results than standalone SimHash, despite being architecturally more
sophisticated. Root cause: the LSH candidate pool was nearly empty for most queries.

### Why the candidate pool was empty

MinHash LSH works by hashing shingle sets into buckets. Two documents collide in a bucket
(become candidates) when their Jaccard similarity exceeds the LSH threshold:

```
threshold ≈ (1 / NUM_BANDS) ^ (1 / ROWS_PER_BAND)
```

With the original config (`64 bands × 2 rows`, k=1 word shingles):

- Threshold: `(1/64)^(1/2) ≈ 0.125` — only chunks with ≥12.5% Jaccard overlap became candidates
- Short QA queries (8–15 words) produce very few shingles → almost no overlap with 2000-char chunks
- Mean LSH candidate count: **~6 chunks** out of 229 total
- Fallback rate (LSH returning 0 candidates): **6.7%** of queries
- The combined scorer had almost nothing to rerank

---

## Fix

Two config changes in `backend/config.py`, followed by a full MinHash index rebuild:

### 1. Switch to unigram + bigram shingles

```python
# Before
MINHASH_USE_UNIGRAMS_AND_BIGRAMS: bool = False   # k=1 word shingles only

# After
MINHASH_USE_UNIGRAMS_AND_BIGRAMS: bool = True    # unigrams ∪ bigrams
```

A query like *"minimum GPA requirement"* now produces shingles:
`{"minimum", "GPA", "requirement", "minimum GPA", "GPA requirement"}`
instead of just `{"minimum", "GPA", "requirement"}`.

Richer shingle sets → more bucket collisions with relevant chunks.

### 2. Relax LSH band/row configuration

```python
# Before
LSH_NUM_BANDS: int = 64
LSH_ROWS_PER_BAND: int = 2    # threshold ≈ 0.125 (strict)

# After
LSH_NUM_BANDS: int = 128
LSH_ROWS_PER_BAND: int = 1    # threshold ≈ 0.008 (permissive)
```

`128 × 1 = 128 = MINHASH_NUM_PERM` (constraint still satisfied).

The lower threshold means a document pair only needs ~0.8% Jaccard overlap to become
candidates. This trades candidate-stage precision for recall — the combined scorer handles
the precision step.

---

## Results

All numbers from `run_method_comparison(k=5, use_pagerank=False)` over 15 benchmark queries.

### Hybrid — before vs after

| Metric | Before | After | Change |
|---|---:|---:|---:|
| Mean P@1 | 0.133 | 0.267 | +100% |
| Mean P@3 | 0.067 | 0.178 | +166% |
| Mean P@5 | 0.080 | 0.187 | +134% |
| Mean R@5 | 0.085 | 0.229 | +169% |
| MAP@5 | 0.063 | 0.167 | +165% |
| Mean latency (ms) | 27.3 | 23.0 | −16% |
| Mean LSH candidates | ~6 | ~70 | +11× |
| Fallback rate | 6.7% | 0.0% | eliminated |

### Full method comparison (after tuning)

| Method | P@1 | P@3 | P@5 | R@5 | MAP@5 | Latency (ms) |
|---|---:|---:|---:|---:|---:|---:|
| TF-IDF (exact baseline) | **0.733** | **0.556** | **0.453** | **0.615** | **0.547** | 0.78 |
| MinHash w/ exact rerank | 0.467 | 0.422 | 0.413 | 0.583 | 0.431 | 403.9 |
| **Hybrid LSH (tuned)** | 0.267 | 0.178 | 0.187 | 0.229 | 0.167 | **23.0** |
| SimHash | 0.200 | 0.133 | 0.120 | 0.140 | 0.110 | 1.38 |

---

## Tradeoff Analysis

This tuning illustrates the core approximate vs exact tradeoff the project is built around:

| Dimension | TF-IDF (exact) | Hybrid LSH (approx) |
|---|---|---|
| MAP@5 | 0.547 | 0.167 |
| Accuracy loss | — | ~3× lower |
| Latency | 0.78 ms | 23 ms |
| Scales with corpus? | O(n) scan every query | O(1) LSH lookup + small rerank set |
| Memory at 8× corpus | grows linearly | index size grows, query cost stable |

The accuracy gap is expected and honest — it is the fundamental cost of approximation.
At handbook scale (229 chunks) the gap is large because the corpus is small enough that
TF-IDF's full scan is cheap. At 10×–100× scale the LSH approach amortizes the candidate
reduction over a much larger denominator, and latency advantage grows.

This tradeoff is what the Scalability experiment (`run_scalability()`) quantifies.

---

## Config snapshot (current)

```python
MINHASH_NUM_PERM: int = 128
MINHASH_SHINGLE_K_WORDS: int = 1        # unused when USE_UNIGRAMS_AND_BIGRAMS=True
MINHASH_USE_UNIGRAMS_AND_BIGRAMS: bool = True
LSH_NUM_BANDS: int = 128
LSH_ROWS_PER_BAND: int = 1
HYBRID_MINHASH_WEIGHT: float = 0.5
HYBRID_SIMHASH_WEIGHT: float = 0.5
```

To reproduce: after changing config, rebuild the index then rerun experiments.

```bash
cd backend
python -c "
from indexing.index_manager import IndexManager, load_chunks
from indexing.minhash_lsh import build_minhash_lsh_index, save_minhash_lsh_index
chunks = load_chunks()
save_minhash_lsh_index(build_minhash_lsh_index(chunks))
"
python ../scripts/run_experiments.py --experiment comparison
```
