# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Context

**Course**: Big Data Analytics (BDA), NUST SEECS  
**Deadline**: 27 April 2025 (already passed — project is in polish/submission phase)  
**Goal**: Scalable QA system over NUST UG/PG Handbooks using LSH-based retrieval. This is **not a chatbot project** — the examiner cares about the retrieval system. LSH implementation is 30% of the grade.

### Grading Breakdown
| Component | Weight |
|-----------|--------|
| Retrieval Implementation via LSH | 30% |
| Experimental Analysis | 20% |
| System Design | 20% |
| Demo (live + recorded) | 20% |
| Report (6–8 pages) | 10% |

### Deliverables Checklist
- [ ] Clean, reproducible code
- [ ] 6–8 page report: system design, algorithm explanation, experimental results, tradeoff analysis
- [ ] Demo video (5–7 min): live system, example queries, explanation of results
- [ ] Required experiments: (1) Exact vs Approximate, (2) Parameter Sensitivity, (3) Scalability

---

## Architecture

```
PDF → Unstructured (semantic chunks) → chunks.json
                                           ↓
              ┌────────────────────────────┤
              ▼                            ▼
     [Hybrid: MinHash+SimHash]      [Baseline: TF-IDF]
     combined_score = α·minhash_jaccard + β·simhash_sim
              ↓                            ↓
         top-k chunks               top-k chunks
              └──────────┬────────────────┘
                         ▼
               PageRank reranking (0.7/0.3)
                         ▼
               LLM answer generation (Anthropic)
                         ▼
                  React frontend
```

**Two retrieval paths, not three:**
- **Hybrid** (`method="hybrid"`): MinHash+LSH + SimHash combined score → top-k. This satisfies the "hybrid LSH-based method" requirement.
- **Baseline** (`method="tfidf"`): TF-IDF + cosine similarity (exact, non-approximate).

The old separate `minhash` and `simhash` methods can remain for parameter sensitivity experiments but the primary retrieval method shown in demo must be the hybrid.

---

## What Needs to Be Built / Fixed

### 1. Chunking — Replace sliding window with Unstructured semantic chunking
**Current state**: `backend/ingestion/chunker.py` uses a 350-word sliding window. This ignores semantic structure (sections, tables, lists).  
**Required**: Replace with [`unstructured`](https://github.com/Unstructured-IO/unstructured) library which detects element types (NarrativeText, Title, Table, ListItem) and groups them into semantically coherent chunks.

```python
# Target API shape
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

elements = partition_pdf(filename=pdf_path, strategy="hi_res")
chunks = chunk_by_title(elements, max_characters=2000, new_after_n_chars=1500)
```

### 2. Hybrid Retriever — Combine MinHash + SimHash into one combined score
**Current state**: `minhash_lsh.py` and `simhash.py` are separate methods with separate retrieve paths.  
**Required**: A single `HybridRetriever` that:
1. Runs MinHash+LSH to get candidate set (fast approximate filter)
2. Scores each candidate with SimHash similarity (Hamming-based)
3. Also scores with MinHash Jaccard
4. `combined_score = 0.5 * minhash_jaccard + 0.5 * simhash_sim` (weights tunable in `config.py`)
5. Returns top-k by combined score

This goes in `backend/indexing/hybrid.py` and is wired as `method="hybrid"` in the retriever.

### 3. TF-IDF remains the standalone baseline (no changes needed)

---

## Commands

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build        # production build
npm run lint         # ESLint check
```

### Makefile shortcuts
```bash
make dev-backend     # uvicorn --reload port 8000
make dev-frontend    # vite dev server
make run-experiments # python scripts/run_experiments.py
```

### Tests & Linting
```bash
cd backend
pytest tests/
python -m black .
python -m ruff check .
```

### CLI ingest
```bash
python scripts/ingest_cli.py --pdf data/raw/ug_handbook.pdf
```

### Run experiments
```bash
python scripts/run_experiments.py   # writes to data/results/
```

---

## Conventions

### Git commits — **commit on every meaningful change**
Format: `type(scope): description`

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `polish`  
Scopes: `ingestion`, `indexing`, `retrieval`, `generation`, `evaluation`, `frontend`, `api`, `config`

```
feat(indexing): add hybrid MinHash+SimHash combined scorer
feat(ingestion): replace sliding window with unstructured semantic chunking
fix(retrieval): handle empty LSH candidates in hybrid path
refactor(indexing): extract combined_score to config-driven weights
```

Commit after each completed function, each experiment run, each bug fix — this maintains the audit trail needed for the report.

### Backend patterns
- All config values in `config.py` (Pydantic `BaseSettings`) — never hardcode paths or thresholds
- All logging via `logging.getLogger(__name__)` — never `print()`
- Each module: `__init__.py` + `models.py` + implementation file
- Indexes loaded at startup via FastAPI lifespan, not on first request
- Check `if not index_path.exists(): build()` before building any index

### Frontend patterns
- All API calls go through `src/api/` (never directly from components)
- Zustand store in `src/store/appStore.js` for shared state
- Tailwind utilities only; CSS variables in `index.css` for tokens
- Components > 150 lines must be split

---

## Key Files

| File | Role |
|------|------|
| `backend/main.py` | FastAPI app entry, lifespan startup |
| `backend/config.py` | All tunable parameters (thresholds, weights, paths) |
| `backend/ingestion/chunker.py` | **Replace with Unstructured** |
| `backend/indexing/minhash_lsh.py` | MinHash+LSH index (keep, feeds hybrid) |
| `backend/indexing/simhash.py` | SimHash index (keep, feeds hybrid) |
| `backend/indexing/hybrid.py` | **Create this** — combined scorer |
| `backend/indexing/tfidf_baseline.py` | TF-IDF baseline (no changes) |
| `backend/retrieval/retriever.py` | Unified retrieve interface, wire in hybrid |
| `backend/evaluation/experiments.py` | 3-experiment framework |
| `backend/evaluation/benchmark_queries.py` | 15 benchmark queries with ground truth |
| `docs/INSTRUCTIONS.md` | Deep algorithm specs — read before implementing |

---

## Experiment Infrastructure (already built)

`backend/evaluation/experiments.py` has three experiments ready to run:
1. **Method Comparison** — P@1/3/5, Recall@5, MAP@5, latency, memory on 15 queries → **update to use `hybrid` method**
2. **Parameter Sensitivity** — sweeps NUM_PERM, NUM_BANDS, Hamming threshold
3. **Scalability** — corpus duplication 2×/4×/8×, measures build + query time

Ground-truth labels are in `benchmark_queries.py`. After rebuilding the hybrid index, rerun experiments and regenerate the report (`backend/evaluation/report.py`).

---

## Demo-Critical Features (extra care)
1. Three-column comparison UI (Hybrid vs TF-IDF vs individual methods) — what examiner sees first
2. Latency badges must reflect real measurements, never hardcoded
3. Analytics charts: properly labeled axes, legends, correct experiment data
4. Answer card must visibly cite handbook chunks
5. Chunk text highlighting of query terms

---

## Required Experiments Output for Report

The report must show:
- Table: Precision@k and Recall@k for Hybrid LSH vs TF-IDF baseline
- Charts: parameter sensitivity (NUM_PERM, NUM_BANDS, Hamming threshold) vs P@5
- Chart: query latency vs corpus scale (1×, 2×, 4×, 8×)
- 10–15 qualitative query evaluations (use `qualitative_scoring.py`)
- Memory usage comparison (already tracked via tracemalloc in retriever)
