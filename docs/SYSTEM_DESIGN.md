# 🏗️ SYSTEM_DESIGN.md — Architecture & Design Decisions

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  IngestPage  │  QueryPage  │  AnalyticsPage                     │
│     ↕              ↕              ↕                             │
│              Axios HTTP Client                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP (localhost:8000)
┌──────────────────────▼──────────────────────────────────────────┐
│                    FASTAPI BACKEND                               │
│  POST /ingest   POST /query   GET /experiments   GET /status    │
│       ↓              ↓                                          │
│  ┌─────────┐   ┌──────────────────────────────────────────┐    │
│  │Ingestion│   │           Retrieval Layer                 │    │
│  │Pipeline │   │  MinHash+LSH │ SimHash │ TF-IDF Baseline  │    │
│  └────┬────┘   └──────┬───────────┬──────────┬────────────┘    │
│       │               │           │          │                  │
│       ▼               └─────────┬─┘          │                  │
│  ┌─────────┐              ┌─────▼─────┐      │                  │
│  │ Chunks  │              │ Reranker  │◄─────┘                  │
│  │  JSON   │              │(PageRank) │                          │
│  └─────────┘              └─────┬─────┘                         │
│                                 ▼                               │
│                          ┌────────────┐                         │
│                          │    LLM     │ (Anthropic API)         │
│                          │ Generation │                         │
│                          └────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │      Data Layer      │
                    │  chunks.json         │
                    │  minhash.pkl         │
                    │  simhash.pkl         │
                    │  tfidf.pkl           │
                    │  pagerank_scores.json│
                    └──────────────────────┘
```

---

## Data Flow: Ingestion

```
PDF File
  │
  ▼
pdf_parser.py
  • pdfplumber extracts text per page
  • Detects section titles from font metadata
  • Records page numbers
  │
  ▼
cleaner.py
  • 8-step cleaning pipeline
  • Removes headers, footers, page numbers
  • Fixes hyphenation, unicode, whitespace
  │
  ▼
chunker.py
  • nltk sentence tokenization
  • Sliding window: 350 words, 75 overlap
  • Preserves page and section metadata
  │
  ▼
chunks.json (342 chunks average for UG handbook)
  │
  ├──► minhash_lsh.py   → minhash.pkl
  ├──► simhash.py        → simhash.pkl  
  ├──► tfidf_baseline.py → tfidf.pkl
  └──► pagerank.py       → pagerank_scores.json
```

---

## Data Flow: Query (method="all")

```
User Query: "What is the minimum GPA?"
  │
  ▼
retriever.py
  │
  ├──► [async] minhash_lsh.py
  │      • Shinglize + MinHash query
  │      • LSH.query() → candidates
  │      • Rerank by Jaccard
  │      • Measure latency + memory
  │
  ├──► [async] simhash.py
  │      • SimHash query fingerprint
  │      • Linear scan by Hamming distance
  │      • Measure latency + memory
  │
  └──► [async] tfidf_baseline.py
         • TF-IDF transform query
         • Cosine similarity
         • Measure latency + memory
         
  All three run via asyncio.gather() — parallel execution
  │
  ▼
reranker.py
  • Fuse scores with PageRank weights
  • final_score = 0.7 * retrieval + 0.3 * pagerank
  │
  ▼
generation/llm.py
  • Top-3 chunks from best method → Claude API
  • Grounded answer with section citations
  │
  ▼
API Response JSON
  • answer + cited_chunks
  • results.minhash + results.simhash + results.tfidf
  • Each with: chunks, latency_ms, memory_mb
```

---

## Key Design Decisions & Justifications

### Why FastAPI over Flask?
- Native async support — critical for running three retrieval methods in parallel
- Automatic OpenAPI docs at `/docs` — useful during development
- Pydantic v2 integration for request/response validation

### Why Pydantic for data models?
- Automatic validation catches malformed data at API boundaries
- JSON serialization built in
- Type safety across the codebase

### Why serialize indexes to disk?
- Cold start: server loads pre-built indexes in < 2 seconds
- Decouples ingestion (slow, once) from querying (fast, many times)
- In demo: indexes already built, show instant query responses

### Why asyncio.gather for parallel retrieval?
- The three methods are I/O-free (CPU-bound), but using async allows FastAPI to handle concurrent requests cleanly
- For true CPU parallelism, could use ProcessPoolExecutor — but for demo scale it's unnecessary

### Why 350 word chunks with 75 word overlap?
- 200 words: too small — policy rules often span multiple paragraphs
- 500 words: too large — reduces precision, LLM gets noisy context
- 75 word overlap: catches sentences split at chunk boundaries (the most common failure mode)

### Why 3-word shingles for MinHash?
- Character shingles (k=5): too fine-grained for long-form text, high false positive rate
- 1-word shingles: too coarse, doesn't capture phrase structure
- 3-word shingles: captures short phrases like "minimum GPA requirement" as a unit

### Why PageRank as extension?
- Mathematically principled (not just a hack)
- Demonstrably from the course content
- Visually explainable: "these sections are more important because they're referenced more"
- Improves retrieval without adding latency (scores precomputed at index time)

---

## Scalability Analysis (for report)

| Component | Current Scale | Bottleneck | Scaling Strategy |
|-----------|--------------|------------|------------------|
| Chunking | 342 chunks | CPU (PDF parse) | Parallel per-page processing |
| MinHash index | 342 × 128 ints | Memory | LSH Forest for millions of docs |
| SimHash query | O(n) linear scan | CPU | Bit prefix hash tables, O(1) lookup |
| TF-IDF query | O(V×n) matrix mult | Memory | Sparse matrix + FAISS for scale |
| LLM generation | 1 API call | Network/Cost | Caching frequent queries |

For the scalability experiment: duplicate corpus to 2x, 4x, 8x.
- MinHash: query latency barely increases (LSH is sublinear)
- SimHash: linear increase (O(n) scan)
- TF-IDF: linear increase (matrix multiply scales with n)
This demonstrates exactly why approximate methods (LSH) are valuable at scale.

---

## Security Considerations (mention in report)
- API key stored in `.env`, never committed
- PDF parsing sandboxed (pdfplumber doesn't execute PDF scripts)
- LLM prompt injection: user query is clearly delimited from system prompt
- No user data stored persistently (query history in localStorage only)
- CORS configured to allow only `localhost:5173` in development