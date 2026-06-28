"""
Global singleton for RAGPipeline — imported everywhere.
This guarantees one instance across upload, chat, documents, and lifespan.
"""
from __future__ import annotations
from app.core.rag_pipeline import RAGPipeline

_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline