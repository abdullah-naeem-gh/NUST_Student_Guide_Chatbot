"""Application settings loaded from environment and defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for paths, retrieval parameters, and API keys."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-oss-120b:free"
    ANTHROPIC_API_KEY: str = ""  # Fallback only

    # CORS Settings
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOWED_ORIGIN_REGEX: str | None = None

    # Unstructured semantic chunking parameters
    UNSTRUCTURED_STRATEGY: str = "fast"        # "fast" | "hi_res" | "ocr_only"
    CHUNK_MAX_CHARACTERS: int = 2000           # hard ceiling per chunk
    CHUNK_NEW_AFTER_N_CHARS: int = 1500        # soft target; splits at next title boundary
    MIN_CHUNK_WORDS: int = 50

    # Legacy sliding-window knobs (kept for backward compatibility)
    CHUNK_SIZE_WORDS: int = 350
    CHUNK_OVERLAP_WORDS: int = 75
    MINHASH_NUM_PERM: int = 128
    # Tuned for QA-style short queries: k=1 yields non-empty LSH candidates.
    MINHASH_SHINGLE_K_WORDS: int = 1
    MINHASH_USE_UNIGRAMS_AND_BIGRAMS: bool = True
    # Candidate-control knobs for MinHash reranking (helps latency when LSH is permissive).
    # Hybrid path: trim LSH candidates to top-50 by MinHash Jaccard before SimHash scoring.
    MINHASH_LSH_PRESELECT_TOP_N: int = 50
    MINHASH_EXACT_RERANK_TOP_N: int = 50
    # 128 bands × 1 row → LSH threshold ~0.008 (permissive candidate recall for short QA queries)
    LSH_NUM_BANDS: int = 128
    LSH_ROWS_PER_BAND: int = 1
    SIMHASH_HAMMING_THRESHOLD: int = 10
    TOP_K_DEFAULT: int = 5

    # Hybrid retrieval weights (must sum to 1.0)
    HYBRID_MINHASH_WEIGHT: float = 0.5
    HYBRID_SIMHASH_WEIGHT: float = 0.5

    # Frequent Itemset Mining (query expansion)
    FIM_MIN_SUPPORT: int = 3            # minimum chunk co-occurrence count to keep an itemset
    FIM_MAX_ITEMSET_SIZE: int = 3       # max itemset size (2 = pairs only, 3 = pairs+triples)
    FIM_TOP_N_PER_TERM: int = 3         # co-occurring terms added per query term at runtime
    FIM_MIN_IDF: float = 3.0           # min TF-IDF IDF to accept an expansion term (filters generic terms)
    FIM_ENABLED: bool = False           # disabled: corpus too small (434 chunks) for reliable signal

    # TF-IDF tuning knobs (baseline defaults in INSTRUCTIONS §2.3)
    TFIDF_MAX_FEATURES: int = 20000
    TFIDF_NGRAM_MAX: int = 2
    TFIDF_MIN_DF: int = 2
    TFIDF_MAX_DF: float = 0.85

    # Repository root is parent of backend/; data/ lives at project root
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    RAW_PDF_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "raw"
    CHUNKS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "chunks"
    INDEX_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "index"


settings = Settings()
