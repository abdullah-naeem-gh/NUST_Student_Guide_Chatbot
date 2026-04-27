# Copilot Instructions for NUST Student Guide QA

## Build, test, and lint commands

```bash
# Backend setup + dev server
cd backend
python3 -m venv .venv
./.venv/bin/pip install -U pip
./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn main:app --reload --port 8000

# Backend tests
cd backend
pytest tests/

# Run a single backend test
cd backend
pytest tests/test_retrieval.py::test_retrieve_all_methods_returns_chunks_and_highlights -q

# Backend formatting/lint
cd backend
python -m black .
python -m ruff check .

# Frontend setup + dev server
cd frontend
npm install
npm run dev

# Frontend build/lint
cd frontend
npm run build
npm run lint
```

Makefile shortcuts used in this repo:

```bash
make install-backend
make install-frontend
make dev-backend
make dev-frontend
make run-experiments
```

## High-level architecture

- The system is a retrieval-first QA pipeline over handbook PDFs. Ingestion is handled by `backend/api/routes/ingest.py`, which calls `ingestion/chunker.py` to run **Unstructured semantic chunking** and writes `data/chunks/chunks.json` plus `chunks_lookup.json`.
- `indexing/index_manager.py` then builds and persists all retrieval artifacts in `data/index/`: `minhash.pkl`, `simhash.json`, `tfidf.pkl`, `pagerank.json`, and `fim.json`.
- At API startup (`backend/main.py` lifespan), existing artifacts are loaded once into memory through `IndexManager` and a long-lived `Retriever` instance is attached to app state.
- Query execution (`backend/api/routes/query.py`) routes through `retrieval/retriever.py`. For `method="all"`, hybrid/tfidf/minhash/simhash run concurrently via `asyncio.gather` + `asyncio.to_thread`.
- **Hybrid is the primary retrieval path**: MinHash+LSH candidate generation followed by combined scoring with MinHash Jaccard + SimHash similarity (`indexing/hybrid.py`, weights in `config.py`).
- Final chunk ranking fuses retrieval score with normalized PageRank (`retrieval/reranker.py`). The answer generator consumes top chunks (prefer hybrid, then tfidf fallback) and returns cited chunk IDs.
- Frontend is a React/Vite client: API access is centralized under `frontend/src/api/` and shared UI/query state is in Zustand (`frontend/src/store/appStore.js`).

## Key conventions specific to this codebase

- Keep tunable behavior in `backend/config.py` (`BaseSettings`); avoid hardcoded paths/thresholds in module code.
- Primary comparison focus is **hybrid vs tfidf**; minhash/simhash remain available for diagnostics and parameter-sensitivity experiments.
- Logging pattern is module logger (`logging.getLogger(__name__)`), not `print()`.
- Index lifecycle convention: build once to disk, then load at FastAPI startup (not lazily on first query).
- Ingestion/output conventions:
  - canonical chunks file: `data/chunks/chunks.json`
  - canonical lookup map: `data/chunks/chunks_lookup.json`
  - multi-PDF ingestion rewrites chunk IDs to globally unique `chunk_000000`-style IDs.
- Query API response shape is stable: results always include `hybrid`, `tfidf`, `minhash`, `simhash` keys (empty models for non-requested methods in single-method mode).
- Frontend components should not call Axios directly; route all HTTP calls through `frontend/src/api/*`.
- Project emphasis is retrieval quality and experiments (method comparison, parameter sensitivity, scalability). Keep experiment paths and outputs (`scripts/run_experiments.py`, `data/results/`) intact when changing retrieval code.
