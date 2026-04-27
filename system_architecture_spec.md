# system_architecture_spec.md

This specification provides a detailed, modular, and flow-oriented breakdown of the **NUST Student Guide Big Data Retrieval System**. It is designed for consumption by AI diagramming tools to generate high-fidelity architecture diagrams, sequence flows, and component maps.

---

## 1. High-Level System Overview
The system is a multi-stage **Retrieval-Augmented Generation (RAG)** pipeline optimized for Big Data retrieval using **Locality Sensitive Hashing (LSH)**. It separates the heavy lifting of PDF ingestion and indexing from the high-speed query and generation phase.

### Core Modules:
1.  **Module A: Ingestion Pipeline** (PDF to Structured Chunks)
2.  **Module B: Indexing Engine** (Multimodal Approximate Retrieval Indexes)
3.  **Module C: Retrieval & Ranking Layer** (Parallel LSH/SimHash/TF-IDF)
4.  **Module D: Generation Layer** (LLM Contextual Synthesis)
5.  **Module E: Analytics & Monitoring** (Experimentation & Metrics)

---

## 2. Detailed Component Architecture

### Module A: Ingestion Pipeline
*   **A1: Parser (`pdf_parser.py`)**: Uses `pdfplumber` to extract raw text and metadata (page numbers, font-based section headers).
*   **A2: Cleaner (`cleaner.py`)**: A multi-stage text normalization engine (Unicode stripping, footer removal, sentence joining).
*   **A3: Chunker (`chunker.py`)**: Semantic partitioning using a 350-word sliding window with a 75-word overlap to maintain contextual continuity.
*   **Data Output**: `chunks.json` (Structured JSON storage).

### Module B: Indexing Engine (Offline/Startup)
Generates and persists retrieval artifacts for O(1) or O(log N) lookup:
*   **B1: MinHash+LSH (`minhash_lsh.py`)**: Creates 128-permutation signatures and bands them for LSH bucket lookup.
*   **B2: SimHash (`simhash.py`)**: Generates 64-bit fingerprints using weighted term features (IDF-based).
*   **B3: TF-IDF (`tfidf_baseline.py`)**: Sparse matrix vectorization for the exact comparison baseline.
*   **B4: PageRank (`pagerank.py`)**: Precomputes importance scores by building a chunk similarity graph.

### Module C: Retrieval & Ranking Layer (Online/Query-time)
*   **C1: The Multi-Method Controller (`retriever.py`)**: Orchestrates four retrieval paths in parallel using `asyncio.gather`:
    1.  **Hybrid Path**: MinHash LSH (for candidate filtering) + SimHash Hamming (for scoring).
    2.  **SimHash Path**: Full corpus linear scan via Hamming distance.
    3.  **MinHash Path**: LSH lookup with Jaccard reranking.
    4.  **TF-IDF Path**: Cosine similarity exact baseline.
*   **C2: Reranker (`reranker.py`)**: Implements **Linear Score Fusion**. Combines retrieval similarity (70%) with PageRank importance (30%).

### Module D: Generation Layer
*   **D1: Context Reconstructor**: Aggregates the top-k chunks from the winning retrieval method.
*   **D2: LLM Interface (`llm.py`)**: Formulates a grounding-focused prompt for Claude/GPT-4, ensuring the response cites specific chunk IDs as evidence.

---

## 3. Operations & Data Flow Patterns

### Flow 1: Data Ingestion & Indexing (Step-by-Step)
1. `User` uploads PDF → `FastAPI`.
2. `Parser` extracts text → `Cleaner` normalizes it.
3. `Chunker` creates semantic units.
4. `IndexManager` triggers all indexing modules (B1-B4).
5. All artifacts (`.pkl`, `.json`) are persisted to `data/index/`.

### Flow 2: Adaptive Query Execution
1. `User Query` → `FastAPI /query` endpoint.
2. `Retriever` starts 4 parallel threads:
   - **Thread 1 (Hybrid)**: Query → LSH Lookup → Candidates → Combined Scoring.
   - **Thread 2 (TF-IDF)**: Query → Matrix Multiply → Scores.
   - **Threads 3&4**: Independent diagnostic paths.
3. Scores are normalized and fused with **PageRank**.
4. The highest-ranked chunks are passed to the **LLM**.
5. `Response`: {Answer, Sources, Latency, Memory Usage}.

---

## 4. Technical Stack Summary
*   **Frontend**: React + Vite (Centralized API client, Zustand state).
*   **Backend**: FastAPI (Python 3.14).
*   **NLP**: NLTK (Sentence tokenization, Porter stemming).
*   **Vectorization**: Scikit-learn (Tfidf), Custom LSH implementation.
*   **LLM**: Anthropic Claude API.

---

## 5. Diagram Generation Prompts (Recommended)
> - *"Generate a component diagram with 4 main horizontal layers: Presentation, API/Controller, Logic/Retrieval, and Data/Storage."*
> - *"Generate a sequence diagram showing how a query flows through the synchronous retrieval engine and asynchronous LLM call."*
> - *"Generate a data flow diagram highlighting the transition from 'Unstructured PDF' to 'Weighted Index Artifacts'."*
