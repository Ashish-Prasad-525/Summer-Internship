"""
AI Document Intelligence System - FastAPI entry point.
Uses global pipeline singleton — no separate VectorStoreManager in lifespan.
"""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import router
from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting AI Document Intelligence System...")

    # Import singleton — this initializes it once for the entire process
    from app.core.pipeline_singleton import get_pipeline
    pipeline = get_pipeline()

    logger.info(f"✅ Pipeline ready — {pipeline.vectorstore.get_total_chunks()} chunks in index")
    logger.info(f"✅ Server running on {settings.HOST}:{settings.PORT}")

    yield

    # Save on shutdown
    pipeline.vectorstore.save()
    logger.info("✅ Vector store saved. Goodbye.")


app = FastAPI(
    title="AI Document Intelligence System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response


app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "AI Document Intelligence System", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    from app.core.pipeline_singleton import get_pipeline
    pipeline = get_pipeline()
    return {
        "status": "healthy",
        "chunks_in_index": pipeline.vectorstore.get_total_chunks(),
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})