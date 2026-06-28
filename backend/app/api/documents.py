"""Documents API — uses global pipeline singleton."""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.document_service import DocumentService
from app.core.pipeline_singleton import get_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


class DocumentMeta(BaseModel):
    doc_id: str
    filename: str
    status: str
    chunks_created: int
    file_size_kb: float
    created_at: str
    file_hash: Optional[str] = None


@router.get("/", response_model=List[DocumentMeta])
async def list_documents():
    return DocumentService().list_all()


@router.get("/{document_id}", response_model=DocumentMeta)
async def get_document(document_id: str):
    doc = DocumentService().get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    service = DocumentService()
    doc = service.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    get_pipeline().vectorstore.delete_by_doc_id(document_id)
    service.delete(document_id)
    return {"message": f"'{doc['filename']}' deleted"}


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str, page: int = 1, per_page: int = 10):
    chunks = get_pipeline().vectorstore.get_chunks_by_doc_id(document_id, page=page, per_page=per_page)
    return {"document_id": document_id, "page": page, "chunks": chunks}


@router.get("/stats/overview")
async def get_stats():
    service = DocumentService()
    vs = get_pipeline().vectorstore
    docs = service.list_all()
    return {
        "total_documents": len(docs),
        "indexed_documents": len([d for d in docs if d["status"] == "indexed"]),
        "total_chunks": vs.get_total_chunks(),
        "vector_store_type": vs.store_type,
    }