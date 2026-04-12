# ✅ TODO.md — Phased Development Plan

> Each phase maps to a GitHub milestone. Complete phases in order.
> Do not start Phase N+1 until Phase N is fully working and committed.

---

## PHASE 0 — Project Bootstrap
**Goal**: Both servers running, talking to each other, folder structure in place.
**Git branch**: `main` (initial setup)

- [ ] `git init`, create GitHub repo, push initial commit with all docs
- [ ] Create `backend/` with `requirements.txt`, `main.py`, `config.py`
- [ ] Set up FastAPI with a single `GET /ping` → `{"status": "ok"}`
- [ ] Create `frontend/` with Vite + React + TailwindCSS
- [ ] Add Axios client, confirm frontend can hit backend `/ping`
- [ ] Set up `.env` files for both backend (`ANTHROPIC_API_KEY`) and frontend (`VITE_API_BASE_URL`)
- [ ] Add `.gitignore` (exclude `.env`, `data/`, `__pycache__`, `node_modules`)
- [ ] Add `Makefile` with `make dev-backend` and `make dev-frontend`
- [ ] **Commit**: `chore: project bootstrap — FastAPI + React + Vite running`

---

## PHASE 1 — Data Ingestion Backend
**Goal**: PDF → clean chunks saved to disk.
**Git branch**: `feature/ingestion`

- [ ] Implement `ingestion/pdf_parser.py` — pdfplumber extraction with page metadata
- [ ] Implement `ingestion/cleaner.py` — full cleaning pipeline (8 steps from INSTRUCTIONS.md)
- [ ] Implement `ingestion/models.py` — `Chunk` dataclass with all fields
- [ ] Implement `ingestion/chunker.py` — sliding window with sentence boundaries
- [ ] Write `tests/test_ingestion.py` — test on a small 5-page sample PDF
- [ ] Add `POST /ingest` route in `api/routes/ingest.py`
- [ ] Test: upload handbook, verify `data/chunks/chunks.json` is populated correctly
- [ ] **Commit**: `feat(ingestion): PDF parser, cleaner, and chunker pipeline`
- [ ] Merge to main, tag `v0.1.0`

---

## PHASE 2 — Indexing (All Three Methods)
**Goal**: All three indexes built and serialized to disk.
**Git branch**: `feature/indexing`

- [ ] Implement `indexing/tfidf_baseline.py` — vectorizer + corpus matrix + save
- [ ] Implement `indexing/minhash_lsh.py` — shingles + signatures + LSH index + save
- [ ] Implement `indexing/simhash.py` — weighted SimHash from scratch + save
- [ ] Implement `indexing/index_manager.py` — orchestrate build/load of all three
- [ ] Implement `indexing/pagerank.py` — graph construction + PageRank scores
- [ ] Write `tests/test_indexing.py`
- [ ] Update `POST /ingest` to trigger index building after chunking
- [ ] Test: build all indexes, verify `.pkl` files exist with correct sizes
- [ ] **Commit**: `feat(indexing): MinHash+LSH, SimHash, TF-IDF, PageRank indexes`
- [ ] Merge to main, tag `v0.2.0`

---

## PHASE 3 — Retrieval Pipeline
**Goal**: Unified retriever returns top-k chunks with metadata.
**Git branch**: `feature/retrieval`

- [ ] Implement `retrieval/retriever.py` — unified interface for all methods
- [ ] Implement `retrieval/reranker.py` — PageRank score fusion
- [ ] Implement highlight span detection in retriever
- [ ] Implement `POST /query` route — runs method(s), returns structured response
- [ ] Add latency and memory tracking to all retrieval methods
- [ ] Write `tests/test_retrieval.py`
- [ ] Test with 5 sample queries — verify results are sensible
- [ ] **Commit**: `feat(retrieval): unified retriever with PageRank reranking`
- [ ] Merge to main, tag `v0.3.0`

---

## PHASE 4 — Answer Generation
**Goal**: LLM generates grounded answers from retrieved chunks.
**Git branch**: `feature/generation`

- [ ] Implement `generation/prompt_templates.py` — system + user prompts
- [ ] Implement `generation/llm.py` — Claude API call with error handling
- [ ] Implement extractive fallback (highest query-term overlap sentence)
- [ ] Wire into `POST /query` when `generate_answer: true`
- [ ] Write `tests/test_generation.py` (mock the API call)
- [ ] Test: run 3 queries end-to-end, verify answers reference correct sections
- [ ] **Commit**: `feat(generation): LLM answer generation with extractive fallback`
- [ ] Merge to main, tag `v0.4.0`

---

## PHASE 5 — Evaluation & Experiments
**Goal**: All required experiments run and results saved as JSON.
**Git branch**: `feature/evaluation`

- [ ] Create `evaluation/benchmark_queries.py` — 15 queries with ground truth chunk IDs
  - Fill ground truth chunk IDs by running TF-IDF and manually verifying top results
- [ ] Implement `evaluation/metrics.py` — P@k, R@k, MAP, latency, memory
- [ ] Implement `evaluation/experiments.py` — runs all 3 experiments
  - Experiment 1: method comparison across all benchmark queries
  - Experiment 2: parameter sensitivity (NUM_PERM, NUM_BANDS, Hamming threshold)
  - Experiment 3: scalability (2x, 4x, 8x corpus duplication)
- [ ] Save all results to `data/results/` as JSON
- [ ] Add `GET /experiments` route
- [ ] **Commit**: `feat(evaluation): benchmark queries, metrics, and experiments`
- [ ] Merge to main, tag `v0.5.0`

---

## PHASE 6 — Frontend Core
**Goal**: Working React UI connected to all API endpoints.
**Git branch**: `feature/frontend-core`

- [ ] Set up routing: QueryPage, AnalyticsPage, IngestPage
- [ ] Implement Navbar with index status indicator + dark mode toggle
- [ ] Implement IngestPage: FileDropzone + IngestProgress + IndexStatusCard
- [ ] Implement SearchBar with method toggle, k selector, PageRank toggle
- [ ] Implement AnswerCard — display LLM answer + cited chunks
- [ ] Implement ChunkCard — text with highlights, metadata badges
- [ ] Implement ChunkList — three-column layout for "all" method comparison
- [ ] Implement LatencyBadge per method
- [ ] Hook up all components to Zustand store
- [ ] **Commit**: `feat(frontend): core query interface with method comparison`
- [ ] Merge to main, tag `v0.6.0`

---

## PHASE 7 — Analytics Dashboard
**Goal**: Beautiful charts displaying all experiment results.
**Git branch**: `feature/frontend-analytics`

- [ ] Implement PrecisionChart — Recharts LineChart, P@k for all methods
- [ ] Implement LatencyChart — Recharts BarChart, grouped by method
- [ ] Implement ScalabilityChart — LineChart, latency vs corpus size
- [ ] Implement ParameterSensitivity — table or heatmap, NUM_PERM vs recall
- [ ] Implement MetricsSummaryTable — all metrics in one table
- [ ] Polish: consistent colors, tooltips, legends, axis labels
- [ ] **Commit**: `feat(analytics): experiment charts and metrics dashboard`
- [ ] Merge to main, tag `v0.7.0`

---

## PHASE 8 — Polish & Demo Prep
**Goal**: System is demo-ready, handles edge cases gracefully.
**Git branch**: `feature/polish`

- [ ] Add all error states (F-15 from FEATURES.md)
- [ ] Add example query chips on empty state
- [ ] Add query history (localStorage, last 10)
- [ ] Add export to JSON button for query results
- [ ] Add copy-to-clipboard for answer
- [ ] Test with actual NUST handbook — verify section detection works
- [ ] Fix any layout issues at 1080p (target demo resolution)
- [ ] Run all 15 benchmark queries — record results for report
- [ ] **Commit**: `polish: error states, empty states, export, query history`
- [ ] Merge to main, tag `v1.0.0`

---

## PHASE 9 — Report & Documentation
**Goal**: Report written, README complete, code documented.

- [ ] Write README.md with setup instructions and architecture diagram
- [ ] Add docstrings to all Python modules
- [ ] Export charts from AnalyticsPage as PNG for report
- [ ] Write 6-8 page report following grading criteria
- [ ] Record 5-7 minute demo video
- [ ] Final review of all code — remove debug prints, dead code
- [ ] **Commit**: `docs: final README, docstrings, and report prep`
- [ ] Tag `v1.0.0-final`