# 📡 API_REFERENCE.md — Complete FastAPI Endpoint Specification

> This file is the contract between frontend and backend.
> Frontend developers read this. Backend developers implement exactly this.

Base URL: `http://localhost:8000`

---

## GET /ping
Health check.

**Response 200**:
```json
{
  "status": "ok",
  "indexed": true,
  "chunk_count": 342
}
```

---

## GET /status
Returns current index state.

**Response 200**:
```json
{
  "indexed": true,
  "chunk_count": 342,
  "source_file": "UG_Handbook_2024.pdf",
  "index_built_at": "2025-04-12T10:30:00Z",
  "index_sizes": {
    "minhash_mb": 4.2,
    "simhash_mb": 0.08,
    "tfidf_mb": 8.7,
    "pagerank_mb": 0.02
  },
  "methods_available": ["minhash", "simhash", "tfidf"]
}
```

**Response 200 (not indexed)**:
```json
{
  "indexed": false,
  "chunk_count": 0,
  "source_file": null,
  "index_built_at": null,
  "index_sizes": {},
  "methods_available": []
}
```

---

## POST /ingest
Parse PDF, chunk, and build all indexes.
Accepts multipart form data with PDF file upload.

**Request**: `multipart/form-data`
- `file`: PDF file (required)
- `force_rebuild`: boolean (optional, default false) — rebuild even if index exists

**Response 200**:
```json
{
  "status": "success",
  "chunk_count": 342,
  "page_count": 87,
  "processing_steps": [
    {"step": "parse", "duration_s": 2.1, "status": "done"},
    {"step": "clean", "duration_s": 0.3, "status": "done"},
    {"step": "chunk", "duration_s": 0.5, "status": "done"},
    {"step": "index_tfidf", "duration_s": 1.2, "status": "done"},
    {"step": "index_minhash", "duration_s": 4.7, "status": "done"},
    {"step": "index_simhash", "duration_s": 0.8, "status": "done"},
    {"step": "index_pagerank", "duration_s": 0.4, "status": "done"}
  ],
  "total_duration_s": 10.1
}
```

**Response 400**: File is not a PDF or is corrupt.
**Response 409**: Index already exists and force_rebuild=false.
**Response 500**: Unexpected server error.

---

## POST /query
Run a query and return retrieved chunks + optional LLM answer.

**Request Body**:
```json
{
  "query": "What is the minimum GPA requirement?",
  "method": "all",
  "k": 5,
  "use_pagerank": true,
  "generate_answer": true
}
```

Fields:
- `query` (string, required): The student's question
- `method` ("minhash" | "simhash" | "tfidf" | "all", default "all")
- `k` (int, 1-20, default 5): Number of chunks to retrieve
- `use_pagerank` (bool, default true): Apply PageRank score fusion
- `generate_answer` (bool, default true): Call LLM to generate answer

**Response 200**:
```json
{
  "query": "What is the minimum GPA requirement?",
  "answer": {
    "text": "According to Section 4.2 of the handbook, students must maintain a minimum CGPA of 2.0 to remain in good academic standing. Students falling below this threshold are placed on academic probation.",
    "cited_chunk_ids": ["chunk_0023", "chunk_0024"],
    "generation_method": "llm",
    "model": "claude-sonnet-4-20250514"
  },
  "results": {
    "minhash": {
      "chunks": [
        {
          "chunk_id": "chunk_0023",
          "text": "Students are required to maintain a minimum cumulative GPA...",
          "score": 0.72,
          "pagerank_score": 0.0043,
          "final_score": 0.5165,
          "page_start": 24,
          "page_end": 24,
          "section_title": "4.2 Academic Standing",
          "highlight_spans": [[32, 35], [54, 65]],
          "is_cited": true
        }
      ],
      "latency_ms": 4.2,
      "memory_delta_mb": 0.31,
      "candidate_count": 18
    },
    "simhash": {
      "chunks": [...],
      "latency_ms": 12.8,
      "memory_delta_mb": 0.08,
      "candidate_count": 342
    },
    "tfidf": {
      "chunks": [...],
      "latency_ms": 8.1,
      "memory_delta_mb": 1.24,
      "candidate_count": 342
    }
  },
  "overlap": {
    "minhash_simhash": ["chunk_0023", "chunk_0025"],
    "minhash_tfidf": ["chunk_0023"],
    "simhash_tfidf": ["chunk_0023", "chunk_0024"],
    "all_three": ["chunk_0023"]
  }
}
```

Notes:
- `highlight_spans`: list of `[start, end]` character offsets in `text`
- `is_cited`: true if this chunk was used in the LLM answer
- `overlap`: which chunk_ids appear in multiple methods — used for visual indicator
- If `method` is not "all", only that method's results are returned
- If `generate_answer=false`, the `answer` field is null

**Response 503**: Index not built yet.
**Response 400**: Invalid request parameters.

---

## GET /experiments
Returns precomputed experiment results. Run `scripts/run_experiments.py` to generate these.

**Response 200**:
```json
{
  "generated_at": "2025-04-12T15:00:00Z",
  "method_comparison": {
    "queries_tested": 15,
    "results": {
      "minhash": {
        "precision_at_1": 0.60,
        "precision_at_3": 0.55,
        "precision_at_5": 0.51,
        "precision_at_10": 0.44,
        "recall_at_5": 0.78,
        "map": 0.62,
        "avg_latency_ms": 4.8,
        "avg_memory_mb": 0.31
      },
      "simhash": {
        "precision_at_1": 0.47,
        "precision_at_3": 0.43,
        "precision_at_5": 0.41,
        "precision_at_10": 0.38,
        "recall_at_5": 0.65,
        "map": 0.49,
        "avg_latency_ms": 13.2,
        "avg_memory_mb": 0.08
      },
      "tfidf": {
        "precision_at_1": 0.73,
        "precision_at_3": 0.69,
        "precision_at_5": 0.64,
        "precision_at_10": 0.57,
        "recall_at_5": 0.91,
        "map": 0.74,
        "avg_latency_ms": 8.7,
        "avg_memory_mb": 1.24
      }
    }
  },
  "parameter_sensitivity": {
    "minhash_num_perm": {
      "values": [32, 64, 128, 256],
      "recall_at_5": [0.61, 0.71, 0.78, 0.79],
      "latency_ms": [2.1, 3.4, 4.8, 9.2]
    },
    "lsh_num_bands": {
      "values": [16, 32, 64],
      "recall_at_5": [0.85, 0.78, 0.65],
      "precision_at_5": [0.43, 0.51, 0.58]
    },
    "simhash_hamming_threshold": {
      "values": [5, 8, 10, 12, 15],
      "precision_at_5": [0.61, 0.54, 0.41, 0.33, 0.21],
      "recall_at_5": [0.41, 0.55, 0.65, 0.71, 0.82]
    }
  },
  "scalability": {
    "corpus_multipliers": [1, 2, 4, 8],
    "chunk_counts": [342, 684, 1368, 2736],
    "minhash_latency_ms": [4.8, 5.1, 5.9, 6.4],
    "simhash_latency_ms": [13.2, 26.1, 51.8, 103.4],
    "tfidf_latency_ms": [8.7, 17.2, 34.1, 68.9],
    "minhash_index_build_s": [4.7, 9.1, 18.4, 37.2],
    "tfidf_index_build_s": [1.2, 2.4, 4.8, 9.6]
  }
}
```

**Response 404**: Experiments not yet run. Frontend should show "Run experiments first" message.

---

## Error Response Format
All error responses follow this schema:
```json
{
  "detail": "Human-readable error message",
  "error_code": "INDEX_NOT_BUILT",
  "suggestion": "Please upload a PDF and build the index first."
}
```

Error codes:
- `INDEX_NOT_BUILT` — 503
- `INVALID_PDF` — 400
- `INDEX_EXISTS` — 409
- `EXPERIMENTS_NOT_RUN` — 404
- `LLM_API_ERROR` — 502 (falls back to extractive, still returns 200)
- `INTERNAL_ERROR` — 500