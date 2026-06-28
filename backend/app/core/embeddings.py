"""
Embeddings module - abstract interface with OpenAI and HuggingFace backends.
Compatible with LangChain 0.3+ and Python 3.13.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_embeddings(self):
        ...

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        ...

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        from langchain_openai import OpenAIEmbeddings
        self._embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        logger.info(f"✅ OpenAI embeddings: {settings.OPENAI_EMBEDDING_MODEL}")

    def get_embeddings(self):
        return self._embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embeddings.embed_documents(texts)


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self):
        try:
            # LangChain 0.3+ - try langchain-huggingface first
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            # Fallback to langchain-community
            from langchain_community.embeddings import HuggingFaceEmbeddings

        self._embeddings = HuggingFaceEmbeddings(
            model_name=settings.HF_EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"✅ HuggingFace embeddings: {settings.HF_EMBEDDING_MODEL}")

    def get_embeddings(self):
        return self._embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embeddings.embed_documents(texts)


_embedding_instance: BaseEmbeddingProvider | None = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openai":
        _embedding_instance = OpenAIEmbeddingProvider()
    elif provider == "huggingface":
        _embedding_instance = HuggingFaceEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: '{provider}'")

    return _embedding_instance


def get_langchain_embeddings():
    return get_embedding_provider().get_embeddings()