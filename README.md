# NUST Student Guide AI QA System

An intelligent, retrieval-first QA system powered by **Locality Sensitive Hashing (LSH)** and **Hybrid Retrieval** over the NUST Undergraduate and Postgraduate Student Handbooks.

This project was developed for the Big Data Analytics (BDA) course at NUST SEECS. It focuses on scalable, efficient retrieval of academic policies using MinHash, SimHash, and PageRank.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **OpenRouter API Key** (for free/low-cost LLM answer generation)

### 2. Environment Setup
Create a `.env` file in the `backend/` directory:
```bash
OPENROUTER_API_KEY=your_key_here
```

### 3. Installation & Run (Standalone Commands)

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use \`.venv\Scripts\activate\`
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
The application will be available at [http://localhost:5173](http://localhost:5173).

---

## 🛠 Project Structure

- `backend/`: FastAPI application handling ingestion, indexing, and retrieval.
- `frontend/`: React + Vite + Tailwind UI for query and analytics visualization.
- `data/`:
    - `raw/`: Source PDFs (UG/PG Handbooks).
    - `chunks/`: Processed semantic text chunks.
    - `index/`: Precomputed MinHash, SimHash, and TF-IDF artifacts.
    - `results/`: Experimental evaluation data and reports.
- `scripts/`: Utilities for running experiments and mass ingestion.

---

## 📖 Ingestion & Indexing Guide

The project comes with pre-computed indices, but if you wish to add new documents or re-index:

1. **Place PDFs**: Put your PDF files in `data/raw/`.
2. **Ingest via UI**: Navigate to the **Ingest** page in the dashboard and click "Start Ingestion".
3. **CLI Ingestion**:
   ```bash
   python scripts/run_experiments.py # Runs indexing as part of the pipeline
   ```

---

## 📊 Experiments & Evaluation

The system includes a robust evaluation framework measuring Precision@k, Recall@k, Latency, and Scalability.

To run the experiments:
```bash
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
python ../scripts/run_experiments.py
```
View the results in the **Analytics** tab of the web dashboard.

---

## 🧠 Core Architecture

- **Ingestion**: Semantic chunking using `Unstructured` (or custom sliding window).
- **Retrieval**: 
    - **Hybrid**: MinHash+LSH (fast filtering) combined with SimHash (Hamming distance scoring).
    - **Baseline**: TF-IDF exact vector similarity.
- **Reranking**: PageRank importance scores fused with retrieval similarity.
- **Generation**: Context-grounded response generation using OpenRouter (e.g., Qwen/GPT-4 Free).

---

## 📝 License
This project is for academic purposes as part of the NUST BDA course.
