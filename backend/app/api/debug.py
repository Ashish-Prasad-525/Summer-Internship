"""
Debug API - inspect internal state of pipeline and vector store.
Remove in production.
"""

import os
from pathlib import Path
from fastapi import APIRouter
from app.api.upload import get_pipeline
from app.config import settings

router = APIRouter()

@router.get("/state")
async def debug_state():
    pipeline = get_pipeline()
    vs = pipeline.vectorstore
    total = vs.get_total_chunks()

    faiss_path = Path(settings.FAISS_INDEX_PATH)
    index_file = faiss_path / "index.faiss"

    return {
        "vectorstore_initialized": vs._initialized,
        "vectorstore_store_is_none": vs._store is None,
        "total_chunks_in_index": total,
        "doc_chunk_map": vs._doc_chunk_map,
        "faiss_index_file_exists": index_file.exists(),
        "faiss_index_file_size_bytes": index_file.stat().st_size if index_file.exists() else 0,
        "upload_dir": settings.UPLOAD_DIR,
        "uploaded_files": [f for f in os.listdir(settings.UPLOAD_DIR)] if Path(settings.UPLOAD_DIR).exists() else [],
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
    }

@router.get("/search")
async def debug_search(q: str = "test"):
    pipeline = get_pipeline()
    results = pipeline.vectorstore.similarity_search(q, top_k=5, score_threshold=0.0)
    return {
        "query": q,
        "total_chunks": pipeline.vectorstore.get_total_chunks(),
        "results_found": len(results),
        "results": [
            {
                "doc_id": doc.metadata.get("doc_id"),
                "filename": doc.metadata.get("filename"),
                "score": round(float(score), 4),
                "excerpt": doc.page_content[:200],
            }
            for doc, score in results
        ]
    }