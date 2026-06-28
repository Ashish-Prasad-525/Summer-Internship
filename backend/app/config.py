"""
Application configuration using Pydantic Settings.
All values can be overridden via environment variables or .env file.
"""

from functools import lru_cache
from typing import List, Literal, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-secrets"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── LLM ───────────────────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["openai", "ollama"] = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048
    STREAMING_ENABLED: bool = True

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_PROVIDER: Literal["openai", "huggingface"] = "huggingface"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384  # 384 for MiniLM, 1536 for OpenAI small

    # ── Vector Store ──────────────────────────────────────────────────────────
    VECTOR_STORE_TYPE: Literal["faiss", "chroma"] = "faiss"
    FAISS_INDEX_PATH: str = "./vectorstore/faiss_index"
    CHROMA_PERSIST_DIR: str = "./vectorstore/chroma_db"
    CHROMA_COLLECTION: str = "documents"

    # ── RAG Pipeline ──────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_THRESHOLD: float = 0.3
    MAX_CONTEXT_TOKENS: int = 4096

    # ── Storage ───────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/app.db"  # Default SQLite; swap for PostgreSQL

    # ── JWT Auth ──────────────────────────────────────────────────────────────
    JWT_SECRET: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
