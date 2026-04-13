"""Application settings loaded from environment and defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for paths, retrieval parameters, and API keys."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    ANTHROPIC_API_KEY: str = ""

    CHUNK_SIZE_WORDS: int = 350
    CHUNK_OVERLAP_WORDS: int = 75
    MIN_CHUNK_WORDS: int = 100
    MINHASH_NUM_PERM: int = 128
    LSH_NUM_BANDS: int = 32
    LSH_ROWS_PER_BAND: int = 4
    SIMHASH_HAMMING_THRESHOLD: int = 10
    TOP_K_DEFAULT: int = 5

    # Repository root is parent of backend/; data/ lives at project root
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    RAW_PDF_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "raw"
    CHUNKS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "chunks"
    INDEX_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "index"


settings = Settings()
