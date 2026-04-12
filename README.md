# Academic Policy QA System

> A scalable Question-Answering system over university handbooks using Big Data retrieval techniques.
> Built for the Big Data Analytics course — NUST SEECS.

---

## Architecture

- **Backend**: FastAPI (Python) — MinHash+LSH, SimHash, TF-IDF, PageRank, LLM generation
- **Frontend**: React + Vite + TailwindCSS — side-by-side method comparison, analytics dashboard
- **Retrieval**: Three methods compared live on every query
- **Extension**: PageRank section importance scoring

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An Anthropic API key

### Install & Run

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/academic-policy-qa.git
cd academic-policy-qa

# Backend
cd backend
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### Using the Makefile
```bash
make install-backend    # pip install backend deps
make install-frontend   # npm install frontend deps
make dev-backend        # start FastAPI server
make dev-frontend       # start React dev server
make run-experiments    # generate experiment results
```

---

## Usage

1. **Ingest**: Go to the Ingest page, upload the handbook PDF, click Build Index
2. **Query**: Enter a question, select retrieval method (or All), click Search
3. **Compare**: View side-by-side results from MinHash, SimHash, and TF-IDF
4. **Analytics**: Go to the Analytics page to view experiment results

---

## Documentation

| File | Purpose |
|------|---------|
| `docs/INSTRUCTIONS.md` | Deep technical spec for every algorithm |
| `docs/FEATURES.md` | Complete feature specification |
| `docs/TODO.md` | Phased development plan |
| `docs/FOLDER_STRUCTURE.md` | Full project file layout |
| `docs/SYSTEM_DESIGN.md` | Architecture and design decisions |
| `docs/API_REFERENCE.md` | Complete API endpoint specification |
| `docs/GIT_WORKFLOW.md` | Branch and commit strategy |
| `.cursorrules` | Coding conventions for AI-assisted development |

---

## Retrieval Methods

| Method | Type | Similarity Metric | Complexity |
|--------|------|-------------------|-----------|
| MinHash + LSH | Approximate | Jaccard (estimated) | O(1) per query |
| SimHash | Approximate | Hamming distance | O(n) per query |
| TF-IDF | Exact | Cosine similarity | O(V×n) per query |

---

## Project Structure

See `docs/FOLDER_STRUCTURE.md` for the complete layout.

---

## Experiments

Three required experiments:
1. **Method comparison**: Precision@k and Recall@k across all methods on 15 benchmark queries
2. **Parameter sensitivity**: Impact of NUM_PERM, NUM_BANDS, Hamming threshold
3. **Scalability**: Query latency vs corpus size (1x, 2x, 4x, 8x)

Run with: `python scripts/run_experiments.py`
Results saved to `data/results/` and served via `GET /experiments`.

---

## Team
- Abdullah Naeem 
- Abdullah Ejaz