"""Application settings loaded from environment and defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for paths, retrieval parameters, and API keys."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-oss-120b:free"

    CHUNK_SIZE_WORDS: int = 350
    CHUNK_OVERLAP_WORDS: int = 75
    MIN_CHUNK_WORDS: int = 100
    MINHASH_NUM_PERM: int = 128
    # Tuned for QA-style short queries: k=1 yields non-empty LSH candidates.
    MINHASH_SHINGLE_K_WORDS: int = 1
    MINHASH_USE_UNIGRAMS_AND_BIGRAMS: bool = False
    # Candidate-control knobs for MinHash reranking (helps latency when LSH is permissive).
    MINHASH_LSH_PRESELECT_TOP_N: int = 200
    MINHASH_EXACT_RERANK_TOP_N: int = 50
    # Tuned LSH params (bands*rows = MINHASH_NUM_PERM)
    # Balance candidate_rate vs latency for reranking.
    LSH_NUM_BANDS: int = 64
    LSH_ROWS_PER_BAND: int = 2
    SIMHASH_HAMMING_THRESHOLD: int = 10
    SIMHASH_MIN_DF: int = 2
    SIMHASH_MAX_DF: float = 0.85
    SIMHASH_SUBLINEAR_TF: bool = True
    TOP_K_DEFAULT: int = 5

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
