# 🧠 INSTRUCTIONS.md — Deep Technical Implementation Guide

> This document is the single source of truth for how every component is built.
> Read this entirely before writing any code. Every design decision is justified here.

---

## 1. DATA INGESTION PIPELINE

### 1.1 PDF Parsing (`ingestion/pdf_parser.py`)

**Library**: `pdfplumber` (preferred over PyPDF2 — handles tables, columns, and spacing far better for academic documents)

**What to extract per page**:
```python
{
  "page_number": int,
  "text": str,            # Raw extracted text
  "section_title": str,   # Detected from font size/bold heuristic
  "has_table": bool,      # pdfplumber can detect tables
}
```

**Critical edge cases to handle**:
- Academic handbooks have **headers/footers on every page** (e.g., "NUST SEECS UG Handbook 2024 | Page 12"). These must be stripped or they pollute every chunk with irrelevant tokens.
- **Page numbers** embedded mid-text must be removed.
- **Multi-column layouts** — pdfplumber reads columns left-to-right across the full width, merging them. Use `page.extract_words(x_tolerance=3)` and reconstruct by x-position if needed.
- **Table of Contents pages** — detect by high density of "......." dot leaders and page number patterns. Skip these pages entirely or tag them separately.
- **Ligature characters** — PDF fonts often encode "fi", "fl" as single glyphs. Run a unicode normalization pass: `unicodedata.normalize("NFKD", text)`.
- **Hyphenation at line breaks** — "atten-\ndance" must become "attendance". Regex: `re.sub(r'-\n', '', text)`.
- **Empty pages** — skip pages with fewer than 50 characters after cleaning.

**Section detection heuristic**:
Use pdfplumber's `chars` data — section headings are typically larger font size or bold. Extract font sizes, find the top 2-3 most common (body text), anything larger is likely a heading.

```python
def detect_section(page):
    chars = page.chars
    sizes = [c['size'] for c in chars]
    body_size = statistics.mode(sizes)
    headings = [c for c in chars if c['size'] > body_size + 2]
    return ''.join(c['text'] for c in headings).strip()
```

---

### 1.2 Text Cleaning (`ingestion/cleaner.py`)

Apply in this exact order — order matters:

1. **Fix encoding**: `text.encode('utf-8', errors='ignore').decode('utf-8')`
2. **Normalize unicode**: `unicodedata.normalize("NFKC", text)`
3. **Remove hyphen line-breaks**: `re.sub(r'-\n', '', text)`
4. **Rejoin soft line breaks**: `re.sub(r'(?<!\n)\n(?!\n)', ' ', text)` (single newlines → space, double newlines → paragraph break)
5. **Strip headers/footers**: Match patterns like `r'NUST.*?Handbook.*?\d+'` and remove
6. **Remove page number artifacts**: `re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)`
7. **Collapse whitespace**: `re.sub(r'[ \t]+', ' ', text)`
8. **Strip leading/trailing per paragraph**

**Do NOT**:
- Lowercase at this stage (preserve for TF-IDF vectorizer, not for chunking metadata)
- Remove punctuation (needed for sentence boundary detection)
- Remove numbers (GPA values, section numbers, credit hours are critical)

---

### 1.3 Chunking (`ingestion/chunker.py`)

**Strategy**: Sliding window with sentence-aware boundaries

**Parameters** (configurable in `config.py`):
```python
CHUNK_SIZE_WORDS = 350        # Target words per chunk
CHUNK_OVERLAP_WORDS = 75      # Overlap between consecutive chunks
MIN_CHUNK_WORDS = 100         # Discard chunks shorter than this
```

**Why overlap?**: A question about "GPA requirements for graduation" might span a paragraph boundary. Without overlap, the relevant sentence could be split across two chunks and retrieved poorly.

**Implementation**:
1. Split cleaned text into sentences using `nltk.sent_tokenize()` (install punkt tokenizer)
2. Greedily accumulate sentences until word count exceeds CHUNK_SIZE_WORDS
3. Save chunk, then backtrack CHUNK_OVERLAP_WORDS words for the next chunk's start
4. Never split mid-sentence

**Chunk metadata to store**:
```python
@dataclass
class Chunk:
    id: str                  # "chunk_0042" — zero-padded
    text: str                # The actual chunk text
    page_start: int          # First page this chunk appears on
    page_end: int            # Last page (chunks can span pages)
    section_title: str       # Nearest detected section heading
    word_count: int
    char_count: int
    source_file: str         # "UG_Handbook_2024.pdf"
```

**Store as**: `data/chunks/chunks.json` — list of Chunk dicts. Also keep `data/chunks/chunks_lookup.json` mapping `chunk_id → index` for O(1) retrieval.

**Edge cases**:
- If a page has only a table (no prose), store the table as a single chunk tagged `"has_table": true` — the LLM can still read it
- If section title changes mid-page, attribute the chunk to whichever section covers the majority of its words
- Final chunk of a section is often very short — merge it with the previous chunk if under MIN_CHUNK_WORDS

---

## 2. INDEXING PIPELINE

### 2.1 MinHash + LSH (`indexing/minhash_lsh.py`)

**Library**: `datasketch` — do not implement MinHash from scratch; use the library but understand every parameter.

**Vocabulary preprocessing for MinHash**:
- Lowercase text
- Remove stopwords (`nltk.corpus.stopwords`)
- Stem with `PorterStemmer` (reduces vocabulary collision, improves Jaccard accuracy)
- Create **k-shingles** (k=3 words) — "minimum gpa requirement" → {"minimum gpa", "gpa requirement"} as the set representation
  - Word-level shingles outperform character shingles for semantic similarity in academic text

**MinHash configuration**:
```python
NUM_PERM = 128       # Number of hash functions — more = more accurate, more memory
                     # 128 gives ~1% Jaccard estimation error at reasonable cost
```

**LSH configuration**:
```python
# bands * rows = NUM_PERM
# Probability of candidate pair: 1 - (1 - s^r)^b where s=Jaccard, r=rows, b=bands
# For threshold t ≈ 0.3 (academic text is diverse, don't be too strict):
#   b=32, r=4  →  threshold ≈ (1/b)^(1/r) = (1/32)^(1/4) ≈ 0.42
#   b=64, r=2  →  threshold ≈ (1/64)^(1/2) ≈ 0.125 (too loose)
# Recommended: b=32, r=4 as starting point

LSH_NUM_BANDS = 32
LSH_ROWS_PER_BAND = 4   # NUM_PERM / NUM_BANDS must be integer
```

**Building the index**:
1. For each chunk, compute its shingle set
2. Create `MinHash` object, update with each shingle
3. Insert into `MinHashLSH` with chunk_id as key
4. Serialize with `pickle` to `data/index/minhash.pkl`

**Querying**:
1. Apply same preprocessing to query text
2. Compute query MinHash signature
3. `lsh.query(query_minhash)` → list of candidate chunk_ids
4. Rerank candidates by exact Jaccard similarity (computed from signatures, not sets)
5. Return top-k

**Parameter sensitivity experiment**: Vary NUM_PERM ∈ {32, 64, 128, 256} and NUM_BANDS ∈ {16, 32, 64} — measure recall@10 and latency. This is required for your report.

---

### 2.2 SimHash (`indexing/simhash.py`)

**Do NOT use a library** — implement this yourself. It's straightforward and shows understanding.

**Algorithm**:
```
1. Tokenize chunk text into terms (lowercase, no stopwords)
2. For each term:
   a. Hash the term to a 64-bit integer using mmh3 (MurmurHash3) — pip install mmh3
   b. For each bit position i in 0..63:
      - if bit i of hash is 1: add TF-IDF weight of term to V[i]
      - else: subtract TF-IDF weight from V[i]
3. For each bit position i:
   - fingerprint[i] = 1 if V[i] > 0 else 0
4. Pack into a 64-bit integer
```

**Why TF-IDF weights instead of uniform weights?**:
Common terms like "student", "course" appear everywhere and should not dominate the fingerprint. Weighting by TF-IDF means rare, discriminative terms drive the fingerprint — vastly improving similarity quality.

**Similarity**:
```python
def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count('1')

def simhash_similarity(a: int, b: int) -> float:
    return 1.0 - (hamming_distance(a, b) / 64.0)
```

**Threshold**: Chunks with Hamming distance ≤ 10 are considered similar (out of 64 bits = ~84% similarity). Tune this — too low misses relevant chunks, too high returns noise.

**Index structure**: Simple dict `{chunk_id: fingerprint_int}` stored as JSON. For querying, linear scan is O(n) but fast for < 10k chunks. For scale experiment, discuss that you'd use a lookup table partitioned by bit prefix.

**Edge case**: Two chunks from the same section will have very low Hamming distance. This is correct behavior — they ARE similar. The diversity of your top-k results depends on the query being specific enough.

---

### 2.3 TF-IDF Baseline (`indexing/tfidf_baseline.py`)

**Library**: `sklearn.feature_extraction.text.TfidfVectorizer`

**Configuration**:
```python
TfidfVectorizer(
    max_features=20000,      # Vocabulary cap — prevents memory blowup
    ngram_range=(1, 2),      # Unigrams + bigrams — bigrams catch "minimum GPA", "attendance policy"
    min_df=2,                # Ignore terms appearing in fewer than 2 chunks (likely OCR noise)
    max_df=0.85,             # Ignore terms appearing in >85% of chunks (stopwords missed by filter)
    sublinear_tf=True,       # Replace TF with 1+log(TF) — reduces dominance of high-frequency terms
    strip_accents='unicode',
    analyzer='word',
    token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]*\b'  # Ignore pure numbers as terms
)
```

**Querying**:
1. `vectorizer.transform([query_text])` → sparse query vector
2. `cosine_similarity(query_vec, corpus_matrix)` → scores array
3. `np.argsort(scores)[::-1][:k]` → top-k indices
4. Map indices to chunk_ids

**Serialize**: Save vectorizer + corpus matrix together with `joblib.dump` — faster than pickle for numpy arrays.

---

### 2.4 PageRank Extension (`indexing/pagerank.py`)

**Concept**: Academic handbook sections reference each other ("see Section 3.2 for details"). We build a directed graph where nodes are chunks and edges represent cross-references. PageRank gives each chunk an "importance" score independent of any query.

**Graph construction**:
1. For each chunk, scan text for patterns: `r'[Ss]ection\s+\d+[\.\d]*'`, `r'[Aa]rticle\s+\d+'`, `r'[Cc]lause\s+\d+'`
2. Resolve the referenced section to a chunk_id (by matching section_title metadata)
3. Add directed edge: current_chunk → referenced_chunk

**Also add edges based on SimHash similarity < 5 Hamming distance** — these are near-duplicate chunks that reinforce each other.

**Compute**:
```python
import networkx as nx
G = nx.DiGraph()
# add nodes and edges
scores = nx.pagerank(G, alpha=0.85, max_iter=100)
# scores: {chunk_id: float}
```

**Usage at retrieval time**:
```python
# Combine retrieval score (0-1) with PageRank score (0-1, normalized)
final_score = 0.7 * retrieval_score + 0.3 * pagerank_score
```

This is your competitive edge — you're ranking not just by query relevance but by document-level importance.

---

## 3. RETRIEVAL PIPELINE

### 3.1 Unified Retriever (`retrieval/retriever.py`)

**Interface**:
```python
def retrieve(
    query: str,
    method: Literal["minhash", "simhash", "tfidf", "all"],
    k: int = 5,
    use_pagerank: bool = True
) -> RetrievalResult:
    ...
```

**RetrievalResult**:
```python
@dataclass
class RetrievalResult:
    method: str
    chunks: List[RetrievedChunk]
    latency_ms: float
    memory_delta_mb: float
    query: str
```

**RetrievedChunk**:
```python
@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float              # Similarity score from retrieval method
    pagerank_score: float     # PageRank importance
    final_score: float        # Weighted combination
    page_start: int
    page_end: int
    section_title: str
    highlight_spans: List[Tuple[int,int]]  # Character offsets of query terms in text
```

**Measuring latency**:
```python
import time, tracemalloc
tracemalloc.start()
t0 = time.perf_counter()
# ... retrieval ...
latency = (time.perf_counter() - t0) * 1000  # ms
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
memory_mb = peak / 1024 / 1024
```

**Highlight span generation**:
After retrieval, find query term positions in chunk text for frontend highlighting:
```python
def find_highlight_spans(text: str, query: str) -> List[Tuple[int,int]]:
    terms = query.lower().split()
    spans = []
    text_lower = text.lower()
    for term in terms:
        start = 0
        while True:
            idx = text_lower.find(term, start)
            if idx == -1: break
            spans.append((idx, idx + len(term)))
            start = idx + 1
    return spans
```

---

## 4. ANSWER GENERATION

### 4.1 LLM Integration (`generation/llm.py`)

**Use Anthropic Claude API** (claude-sonnet-4-20250514)

**System prompt**:
```
You are an academic policy assistant for NUST SEECS. 
You answer student questions STRICTLY based on the provided handbook excerpts.
- Never answer from general knowledge
- Always cite which section your answer comes from
- If the excerpts don't contain enough information, say so explicitly
- Be concise and precise — students need actionable answers
- Format policy rules as numbered lists when there are multiple conditions
```

**User prompt template**:
```
Student Question: {query}

Relevant Handbook Excerpts:
{for i, chunk in enumerate(top_chunks)}
[Excerpt {i+1} — {chunk.section_title}, Page {chunk.page_start}]
{chunk.text}
{endfor}

Based ONLY on the above excerpts, answer the student's question.
At the end, cite which excerpt(s) you used.
```

**Response parsing**: Extract the answer text and the cited excerpt indices. Map cited indices back to chunk_ids for frontend display.

**Fallback**: If API call fails, fall back to extractive method — return the sentence from the top chunk that has highest overlap with query terms.

---

## 5. EVALUATION

### 5.1 Ground Truth (`evaluation/benchmark_queries.py`)

Create 15 queries with manually identified relevant chunk_ids:
```python
BENCHMARK = [
    {
        "query": "What is the minimum GPA requirement to avoid probation?",
        "relevant_chunk_ids": ["chunk_0023", "chunk_0024"],  # You fill these in after ingestion
        "category": "academic_standing"
    },
    # ... 14 more
]
```

Categories to cover: GPA, attendance, course repetition, graduation requirements, fee structure, disciplinary policy, thesis/FYP, grading scale, leave policy, examination rules.

### 5.2 Metrics (`evaluation/metrics.py`)

```python
def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    retrieved_k = retrieved[:k]
    return len(set(retrieved_k) & relevant) / k

def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    retrieved_k = retrieved[:k]
    return len(set(retrieved_k) & relevant) / len(relevant)

def mean_average_precision(results_per_query) -> float:
    # Standard MAP implementation
    ...
```

### 5.3 Experiments to run (`evaluation/experiments.py`)

**Experiment 1 — Method Comparison**:
Run all 15 benchmark queries through MinHash, SimHash, TF-IDF. Compute P@1, P@3, P@5, R@5, latency, memory for each. Export as `results/method_comparison.json`.

**Experiment 2 — Parameter Sensitivity**:
- MinHash: vary NUM_PERM ∈ {32, 64, 128, 256}, measure recall@5 and latency
- LSH: vary NUM_BANDS ∈ {16, 32, 64}, measure recall@5
- SimHash: vary Hamming threshold ∈ {5, 8, 10, 12, 15}, measure precision@5

**Experiment 3 — Scalability**:
- Duplicate corpus 2x, 4x, 8x (just repeat chunks with modified IDs)
- Measure index build time and query latency at each scale
- Plot as line chart

---

## 6. API DESIGN

### Endpoints

**POST /ingest**
```json
Request: { "force_rebuild": false }
Response: {
  "status": "success",
  "chunk_count": 342,
  "index_build_time_s": 12.4,
  "methods_indexed": ["minhash", "simhash", "tfidf", "pagerank"]
}
```

**POST /query**
```json
Request: {
  "query": "What is the minimum GPA?",
  "method": "all",     // "minhash" | "simhash" | "tfidf" | "all"
  "k": 5,
  "use_pagerank": true,
  "generate_answer": true
}
Response: {
  "query": "...",
  "answer": "...",
  "cited_chunks": ["chunk_0023"],
  "results": {
    "minhash": { "chunks": [...], "latency_ms": 4.2, "memory_mb": 0.3 },
    "simhash": { "chunks": [...], "latency_ms": 12.1, "memory_mb": 0.1 },
    "tfidf":   { "chunks": [...], "latency_ms": 8.7, "memory_mb": 1.2 }
  }
}
```

**GET /experiments**
```json
Response: {
  "method_comparison": { ... },
  "parameter_sensitivity": { ... },
  "scalability": { ... },
  "generated_at": "2025-04-12T10:00:00Z"
}
```

**GET /status**
```json
Response: {
  "indexed": true,
  "chunk_count": 342,
  "source_file": "UG_Handbook_2024.pdf",
  "index_sizes": {
    "minhash_mb": 4.2,
    "simhash_mb": 0.1,
    "tfidf_mb": 8.7
  }
}
```

---

## 7. FRONTEND ARCHITECTURE

### State Management (Zustand)
```javascript
{
  indexStatus: { indexed: bool, chunkCount: int, ... },
  queryResults: { minhash: {...}, simhash: {...}, tfidf: {...} },
  answer: { text: str, citedChunks: [...] },
  activeMethod: "all" | "minhash" | "simhash" | "tfidf",
  isLoading: bool,
  experiments: { ... }
}
```

### Key UX decisions:
- When method = "all", show three columns side by side — one per method — each with their chunks and a latency badge. This is the killer demo feature.
- Chunks display with highlighted query terms (use the `highlight_spans` from API)
- Each chunk card shows: section title, page number, similarity score, PageRank score
- Analytics page loads experiment data once and caches it

---

## 8. EDGE CASES SUMMARY

| Edge Case | Location | Solution |
|-----------|----------|----------|
| PDF with scanned images (no text layer) | pdf_parser.py | Detect empty pages, warn user, skip |
| Chunk with only numbers/tables | chunker.py | Tag as table chunk, still index but lower weight |
| Query with no results from LSH | retriever.py | Fall back to TF-IDF automatically, flag in response |
| API key missing | generation/llm.py | Return top chunk text as extractive answer |
| Index not built yet | api/routes/query.py | Return 503 with "Index not ready" message |
| Duplicate chunks after corpus scaling | indexing/ | Deduplicate by content hash before indexing |
| Very short query (1-2 words) | retriever.py | Expand query using top TF-IDF terms for that word |
| Unicode/Arabic characters in PDF | cleaner.py | Normalize then strip non-latin if causing issues |