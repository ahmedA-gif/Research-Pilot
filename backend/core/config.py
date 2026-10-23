"""Application configuration using Pydantic Settings.
Reads environment variables with sensible defaults and path resolution.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # NVIDIA NIM API Settings
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_API_BASE: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_LLM_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    NVIDIA_EMBED_MODEL: str = "nvidia/nemotron-3.5-embed-1b"
    EMBEDDING_DIMENSION: int = 2048

    # Database
    DATABASE_URL: str = "sqlite:///./researchpilot.db"

    # API & Telemetry
    API_BASE_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Data paths
    DATA_DIR: Path = BASE_DIR / "data"
    SEED_PAPERS_PATH: Path = BASE_DIR / "data" / "seed_papers_25.json"
    GOLD_QA_PATH: Path = BASE_DIR / "data" / "gold_qa_10.json"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
