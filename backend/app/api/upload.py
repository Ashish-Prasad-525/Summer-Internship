"""Upload API — uses global pipeline singleton."""

import uuid
import logging
import aiofiles
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import settings
from app.core.document_loader import DocumentLoader
from app.core.pipeline_singleton import get_pipeline
from app.services.document_service import DocumentService
from app.utils.file_utils import compute_file_hash

logger = logging.getLogger(__name__)
router = APIRouter()


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
    chunks_created: int = 0
    file_size_kb: float = 0


class BatchUploadResponse(BaseModel):
    total: int
    successful: int
    failed: int
    documents: List[UploadResponse]


@router.post("/", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported.")

    content = await file.read()
    file_size_kb = len(content) / 1024
    if file_size_kb > settings.MAX_FILE_SIZE_MB * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB")

    doc_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{doc_id}_{Path(file.filename).name}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logger.info(f"📄 Saved '{file.filename}' ({file_size_kb:.1f} KB)")

    doc_service = DocumentService()
    doc_service.register(
        doc_id=doc_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size_kb=file_size_kb,
        file_hash=compute_file_hash(content),
    )

    original_filename = file.filename

    async def index_document():
        try:
            logger.info(f"⚙️  Indexing '{original_filename}'...")
            pipeline = get_pipeline()          # ← same singleton
            loader = DocumentLoader()
            docs = loader.load(str(file_path), doc_id=doc_id, filename=original_filename)
            chunks = pipeline.index_documents(docs)
            doc_service.update_status(doc_id, "indexed", chunks_created=chunks)
            logger.info(f"✅ Indexed '{original_filename}' → {chunks} chunks | Total: {pipeline.vectorstore.get_total_chunks()}")
        except Exception as e:
            logger.error(f"❌ Indexing failed: {e}", exc_info=True)
            doc_service.update_status(doc_id, "failed")

    background_tasks.add_task(index_document)

    return UploadResponse(
        document_id=doc_id,
        filename=file.filename,
        status="processing",
        message="Uploaded. Indexing in background.",
        file_size_kb=round(file_size_kb, 2),
    )


@router.post("/batch", response_model=BatchUploadResponse)
async def upload_batch(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    results, successful, failed = [], 0, 0
    for file in files:
        try:
            result = await upload_document(background_tasks, file)
            results.append(result)
            successful += 1
        except HTTPException as e:
            results.append(UploadResponse(document_id="", filename=file.filename, status="failed", message=e.detail))
            failed += 1
    return BatchUploadResponse(total=len(files), successful=successful, failed=failed, documents=results)


@router.get("/status/{document_id}")
async def get_upload_status(document_id: str):
    doc = DocumentService().get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc