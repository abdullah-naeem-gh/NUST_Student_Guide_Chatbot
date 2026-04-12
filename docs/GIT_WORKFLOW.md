# 🌿 GIT_WORKFLOW.md — GitHub Commit Strategy

## Setup

```bash
# Initialize
git init
git remote add origin https://github.com/YOUR_USERNAME/academic-policy-qa.git

# Initial commit — docs only
git add .
git commit -m "chore: initialize project with full documentation"
git push -u origin main
git tag v0.0.0
git push origin v0.0.0
```

---

## Branch Strategy

```
main (always stable, tagged at each phase)
  └── feature/phase-0-bootstrap
  └── feature/ingestion
  └── feature/indexing
  └── feature/retrieval
  └── feature/generation
  └── feature/evaluation
  └── feature/frontend-core
  └── feature/frontend-analytics
  └── feature/polish
```

### Creating a branch:
```bash
git checkout -b feature/ingestion
```

### Merging a phase:
```bash
git checkout main
git merge feature/ingestion --no-ff -m "feat: merge ingestion pipeline"
git tag v0.1.0
git push origin main --tags
```

---

## Commit Checklist (before every commit)

- [ ] Code runs without errors
- [ ] No `.env` files staged (`git status` check)
- [ ] No `.pkl` files staged
- [ ] No `node_modules/` staged
- [ ] Docstrings added to new functions
- [ ] No `print()` statements (use logger)
- [ ] Commit message follows convention

---

## Commit Map (exact messages to use)

### Phase 0
```
chore: initialize project with full documentation
chore: scaffold backend FastAPI with /ping endpoint
chore: scaffold frontend React + Vite + Tailwind
chore: add Makefile and root configuration
chore: configure CORS and environment variables
```

### Phase 1 — Ingestion
```
feat(ingestion): add PDF parser with pdfplumber and section detection
feat(ingestion): add 8-step text cleaning pipeline
feat(ingestion): add sliding window chunker with sentence boundaries
feat(ingestion): add Chunk dataclass and ingestion models
feat(api): add POST /ingest endpoint with progress tracking
test(ingestion): add unit tests for parser, cleaner, and chunker
```

### Phase 2 — Indexing
```
feat(indexing): add TF-IDF baseline vectorizer with bigrams
feat(indexing): add MinHash LSH index with 128 perms 32 bands
feat(indexing): add SimHash fingerprint from scratch with mmh3
feat(indexing): add PageRank section importance graph
feat(indexing): add IndexManager to orchestrate build and load
feat(api): add GET /status endpoint for index state
test(indexing): add unit tests for all three index methods
```

### Phase 3 — Retrieval
```
feat(retrieval): add unified retriever interface for all methods
feat(retrieval): add latency and memory tracking to all retrievers
feat(retrieval): add highlight span detection for query terms
feat(retrieval): add PageRank score fusion reranker
feat(api): add POST /query with parallel async retrieval
test(retrieval): add retrieval integration tests with sample queries
```

### Phase 4 — Generation
```
feat(generation): add Claude API integration with grounded prompts
feat(generation): add extractive fallback for API failures
feat(generation): add prompt templates with citation enforcement
feat(api): wire generate_answer flag into POST /query
test(generation): add generation tests with mocked API
```

### Phase 5 — Evaluation
```
feat(evaluation): add 15 benchmark queries with ground truth
feat(evaluation): add precision_at_k, recall_at_k, MAP metrics
feat(evaluation): add method comparison experiment
feat(evaluation): add parameter sensitivity experiment
feat(evaluation): add scalability experiment with corpus duplication
feat(api): add GET /experiments endpoint
data: add experiment results JSON files
```

### Phase 6 — Frontend Core
```
feat(frontend): add Zustand store with global state
feat(frontend): add Axios API client with interceptors
feat(frontend): add Navbar with index status and dark mode toggle
feat(frontend): add IngestPage with FileDropzone and progress steps
feat(frontend): add QueryPage with SearchBar and method selector
feat(frontend): add AnswerCard with cited chunks display
feat(frontend): add ChunkCard with query term highlighting
feat(frontend): add three-column side-by-side method comparison
feat(frontend): add LatencyBadge and memory indicator per method
```

### Phase 7 — Analytics
```
feat(analytics): add PrecisionChart with per-method comparison
feat(analytics): add LatencyChart grouped bar comparison
feat(analytics): add ScalabilityChart corpus size vs latency
feat(analytics): add ParameterSensitivity charts
feat(analytics): add MetricsSummaryTable
feat(analytics): wire AnalyticsPage to GET /experiments
```

### Phase 8 — Polish
```
polish: add error states for all failure scenarios
polish: add example query chips on empty state
polish: add query history with localStorage persistence
polish: add copy-to-clipboard on answer card
polish: fix responsive layout for 1440x900 demo screen
refactor: remove debug logs and clean up comments
docs: add setup instructions to README
docs: add architecture diagram to README
```

---

## GitHub Release Notes Template (for v1.0.0)

```markdown
## Academic Policy QA System v1.0.0

### Features
- PDF ingestion pipeline with section-aware chunking
- Three retrieval methods: MinHash+LSH, SimHash, TF-IDF
- PageRank section importance scoring
- Side-by-side method comparison with latency metrics
- LLM-powered answer generation grounded in handbook text
- Analytics dashboard with experiment results

### Experiments Included
- Method comparison: Precision@k and Recall@k for all methods
- Parameter sensitivity: NUM_PERM, NUM_BANDS, Hamming threshold
- Scalability: Query latency vs corpus size (1x–8x)

### Setup
See README.md for installation and running instructions.
```