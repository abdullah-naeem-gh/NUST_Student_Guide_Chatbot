# 📁 FOLDER STRUCTURE — Academic Policy QA System

## Root
```
academic-policy-qa/
├── backend/
├── frontend/
├── data/
├── notebooks/
├── scripts/
├── docs/
├── .cursorrules
├── .gitignore
├── README.md
├── docker-compose.yml          # Optional: spin up both services
└── Makefile                    # Shortcut commands
```

---

## Backend (FastAPI + Python)
```
backend/
├── main.py                         # FastAPI app factory, CORS, router registration
├── config.py                       # Pydantic Settings: paths, thresholds, API keys
├── requirements.txt
├── requirements-dev.txt            # pytest, httpx, black, ruff
├── Makefile                        # make dev, make test, make ingest
│
├── ingestion/
│   ├── __init__.py
│   ├── pdf_parser.py               # pdfplumber → raw text per page with metadata
│   ├── cleaner.py                  # Regex pipeline: remove headers/footers/noise
│   ├── chunker.py                  # Sliding window chunker with overlap
│   └── models.py                   # Pydantic: Chunk, PageMeta, IngestResult
│
├── indexing/
│   ├── __init__.py
│   ├── minhash_lsh.py              # MinHash signatures + band/row LSH index
│   ├── simhash.py                  # 64-bit SimHash + Hamming lookup table
│   ├── tfidf_baseline.py           # sklearn TF-IDF vectorizer + cosine
│   ├── pagerank.py                 # Section graph builder + nx.pagerank scores
│   ├── index_manager.py            # Orchestrates build/save/load of all indexes
│   └── models.py                   # Pydantic: IndexStatus, IndexConfig
│
├── retrieval/
│   ├── __init__.py
│   ├── retriever.py                # Unified retrieve(query, method, k) interface
│   ├── reranker.py                 # PageRank score fusion with retrieval scores
│   └── models.py                   # Pydantic: RetrievedChunk, RetrievalResult
│
├── generation/
│   ├── __init__.py
│   ├── llm.py                      # Anthropic/OpenAI call, prompt builder
│   ├── prompt_templates.py         # System + user prompt strings
│   └── models.py                   # Pydantic: GenerationRequest, GenerationResult
│
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                  # precision_at_k, recall_at_k, latency, memory
│   ├── experiments.py              # Runs all comparisons, dumps JSON results
│   ├── benchmark_queries.py        # 15 hand-crafted ground truth query pairs
│   └── models.py                   # Pydantic: ExperimentResult, MetricSummary
│
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── ingest.py               # POST /ingest
│   │   ├── query.py                # POST /query
│   │   ├── experiments.py          # GET /experiments
│   │   └── status.py               # GET /status
│   └── middleware.py               # Request timing, error handling
│
├── data/
│   ├── raw/                        # Drop PDFs here
│   ├── chunks/                     # chunks.json (auto-generated)
│   └── index/
│       ├── minhash.pkl
│       ├── simhash.pkl
│       ├── tfidf.pkl
│       └── pagerank_scores.json
│
└── tests/
    ├── test_ingestion.py
    ├── test_indexing.py
    ├── test_retrieval.py
    ├── test_generation.py
    └── test_api.py
```

---

## Frontend (React + Vite + TailwindCSS)
```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── .env                            # VITE_API_BASE_URL=http://localhost:8000
│
└── src/
    ├── main.jsx
    ├── App.jsx                     # Router setup
    │
    ├── api/
    │   ├── client.js               # Axios instance with base URL + interceptors
    │   ├── ingest.js               # ingestPDF(), getStatus()
    │   ├── query.js                # runQuery(), runAllMethods()
    │   └── experiments.js          # getExperiments()
    │
    ├── pages/
    │   ├── QueryPage.jsx           # Main QA interface
    │   ├── AnalyticsPage.jsx       # Charts, experiment results
    │   └── IngestPage.jsx          # PDF upload + index build UI
    │
    ├── components/
    │   ├── layout/
    │   │   ├── Navbar.jsx
    │   │   ├── Sidebar.jsx
    │   │   └── PageWrapper.jsx
    │   │
    │   ├── query/
    │   │   ├── SearchBar.jsx           # Query input with method selector
    │   │   ├── MethodToggle.jsx        # MinHash / SimHash / TF-IDF / All
    │   │   ├── AnswerCard.jsx          # LLM answer with confidence
    │   │   ├── ChunkCard.jsx           # Single retrieved chunk with highlights
    │   │   ├── ChunkList.jsx           # Top-k chunks grid
    │   │   └── LatencyBadge.jsx        # ms badge per method
    │   │
    │   ├── analytics/
    │   │   ├── PrecisionChart.jsx      # Recharts: Precision@k curve
    │   │   ├── LatencyChart.jsx        # Bar chart: latency per method
    │   │   ├── ScalabilityChart.jsx    # Line chart: perf vs corpus size
    │   │   ├── ParameterSensitivity.jsx # Heatmap: bands vs hash functions
    │   │   └── MetricsSummaryTable.jsx
    │   │
    │   ├── ingest/
    │   │   ├── FileDropzone.jsx        # Drag-and-drop PDF upload
    │   │   ├── IngestProgress.jsx      # Step-by-step progress indicator
    │   │   └── IndexStatusCard.jsx     # Shows chunk count, index status
    │   │
    │   └── shared/
    │       ├── Spinner.jsx
    │       ├── Badge.jsx
    │       ├── Tooltip.jsx
    │       └── ErrorAlert.jsx
    │
    ├── hooks/
    │   ├── useQuery.js              # Query state + loading + error
    │   ├── useIngest.js             # Ingest polling + progress
    │   └── useExperiments.js        # Fetch + cache experiment data
    │
    ├── store/
    │   └── appStore.js             # Zustand: global state (index status, results)
    │
    └── styles/
        ├── index.css               # Tailwind base + custom CSS variables
        └── theme.js                # Design tokens
```

---

## Supporting Directories
```
notebooks/
├── 01_pdf_exploration.ipynb        # Explore handbook structure
├── 02_chunking_experiments.ipynb   # Test different chunk sizes
├── 03_lsh_parameter_tuning.ipynb   # Band/row sensitivity analysis
└── 04_evaluation_results.ipynb     # Final experiment charts

scripts/
├── ingest_cli.py                   # Run ingestion from terminal
├── run_experiments.py              # Generate all experiment JSON
└── export_charts.py               # Export charts as PNG for report

docs/
├── INSTRUCTIONS.md
├── FEATURES.md
├── TODO.md
├── FOLDER_STRUCTURE.md             # This file
├── SYSTEM_DESIGN.md
└── API_REFERENCE.md
```