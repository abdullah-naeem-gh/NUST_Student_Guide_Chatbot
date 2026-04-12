# ✨ FEATURES.md — Complete Feature Specification

## CORE FEATURES (Required for submission)

### F-01: PDF Ingestion & Chunking
- Upload UG/PG handbook PDF via drag-and-drop interface
- Automatic text extraction with page metadata preserved
- Sentence-aware sliding window chunking (350 words, 75-word overlap)
- Section title detection from PDF font metadata
- Real-time ingestion progress shown step by step (Parse → Clean → Chunk → Index)
- Results: chunk count, page count, processing time displayed on completion

### F-02: MinHash + LSH Retrieval
- 3-word shingle set representation per chunk
- 128 permutation MinHash signatures
- LSH with 32 bands × 4 rows (threshold ≈ 0.42 Jaccard)
- Configurable NUM_PERM and NUM_BANDS via config.py
- Returns top-k chunks with similarity scores and latency measurement

### F-03: SimHash Retrieval
- 64-bit SimHash fingerprint per chunk using MurmurHash3
- TF-IDF weighted term contributions to fingerprint
- Hamming distance similarity (configurable threshold)
- Linear scan query (O(n)) — acceptable for handbook scale
- Returns top-k chunks with Hamming distance and latency

### F-04: TF-IDF Baseline Retrieval
- sklearn TF-IDF vectorizer (unigrams + bigrams)
- Cosine similarity against corpus matrix
- Exact retrieval (no approximation)
- Used as ground truth comparison against LSH methods

### F-05: Side-by-Side Method Comparison
- Single query runs through all three methods simultaneously (parallel)
- Three-column result display: MinHash | SimHash | TF-IDF
- Each column shows: top-k chunks, similarity scores, latency badge, memory usage
- Allows visual comparison of which chunks each method retrieves
- Overlap indicator: shows which chunks appear in multiple methods

### F-06: LLM Answer Generation
- Grounded answer using Claude API (claude-sonnet-4-20250514)
- Answer generated from top-3 retrieved chunks only — no hallucination
- System prompt enforces "answer from context only" constraint
- Cited sources shown below answer (highlighted chunk cards)
- Graceful fallback to extractive answer if API unavailable

### F-07: Chunk Display with Highlights
- Each retrieved chunk shown as a card
- Query terms highlighted in yellow within chunk text
- Section title and page range shown as metadata
- Similarity score and PageRank score shown as badges
- Expand/collapse long chunks

### F-08: Query Interface
- Clean search bar with method selector (All / MinHash / SimHash / TF-IDF)
- k selector (1, 3, 5, 10)
- PageRank toggle (on/off)
- Query history (last 10 queries, click to re-run)
- Example queries shown as clickable chips on empty state

### F-09: Analytics Dashboard
- Precision@k curves (P@1, P@3, P@5, P@10) for all methods
- Latency comparison bar chart
- Memory usage comparison
- Scalability chart (corpus size vs query latency)
- Parameter sensitivity heatmap (MinHash: NUM_PERM vs recall)
- All charts built with Recharts

### F-10: Index Status & Management
- Status indicator in navbar (Indexed / Not Indexed)
- Index metadata: chunk count, source file, build timestamp, index sizes
- Rebuild index button (with confirmation dialog)
- Per-method index status shown

---

## EXTENSION FEATURE (Competitive Edge)

### F-11: PageRank Section Importance
- Directed graph built from cross-references between handbook sections
- Additional edges from near-duplicate chunks (Hamming < 5)
- PageRank computed with α=0.85
- PageRank scores fused with retrieval scores (70/30 split)
- Top-ranked sections shown in sidebar as "Important Sections"
- Toggleable — user can turn PageRank off to see raw retrieval scores

---

## QUALITY-OF-LIFE FEATURES

### F-12: Dark/Light Mode
- System preference detected on load
- Toggle in navbar
- All charts and cards adapt to theme

### F-13: Export Results
- Export current query results as JSON
- Export experiment charts as PNG (for report)
- Copy answer to clipboard with one click

### F-14: Responsive Layout
- Works on laptop (primary target for demo)
- Gracefully degrades on smaller screens

### F-15: Error States
- PDF parse error: clear message with likely cause
- No results found: suggest rephrasing
- API timeout: show extractive fallback with notice
- Index not built: redirect to ingest page

---

## OUT OF SCOPE (Do not implement)
- User authentication
- Multi-user support
- Persistent query history in database
- Support for non-PDF formats
- Real-time streaming of LLM answer (keep it simple for demo)
- Mobile app