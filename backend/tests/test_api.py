"""
Test suite for AI Document Intelligence System.
Run with: pytest tests/ -v
"""

import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment before importing app
os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("VECTOR_STORE_TYPE", "faiss")
os.environ.setdefault("FAISS_INDEX_PATH", "/tmp/test_faiss_index")
os.environ.setdefault("UPLOAD_DIR", "/tmp/test_uploads")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/test_app.db")

from app.main import app  # noqa: E402

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"


# ── Documents API ─────────────────────────────────────────────────────────────

def test_list_documents_empty():
    r = client.get("/api/v1/documents/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_nonexistent_document():
    r = client.get("/api/v1/documents/nonexistent-id")
    assert r.status_code == 404


def test_delete_nonexistent_document():
    r = client.delete("/api/v1/documents/nonexistent-id")
    assert r.status_code == 404


def test_stats_overview():
    r = client.get("/api/v1/documents/stats/overview")
    assert r.status_code == 200
    data = r.json()
    assert "total_documents" in data
    assert "total_chunks" in data


# ── Upload API ────────────────────────────────────────────────────────────────

def test_upload_txt_file():
    content = b"This is a test document.\nIt has multiple lines.\nUsed for testing the RAG pipeline."
    r = client.post(
        "/api/v1/upload/",
        files={"file": ("test_document.txt", content, "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test_document.txt"
    assert "document_id" in data
    assert data["status"] in ("processing", "pending")
    return data["document_id"]


def test_upload_invalid_extension():
    r = client.post(
        "/api/v1/upload/",
        files={"file": ("malware.exe", b"binary", "application/octet-stream")},
    )
    assert r.status_code == 400
    assert "not supported" in r.json()["detail"].lower()


def test_upload_status_after_upload():
    content = b"Status test document content."
    r = client.post(
        "/api/v1/upload/",
        files={"file": ("status_test.txt", content, "text/plain")},
    )
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    r2 = client.get(f"/api/v1/upload/status/{doc_id}")
    assert r2.status_code == 200
    assert r2.json()["doc_id"] == doc_id


# ── Chat API ──────────────────────────────────────────────────────────────────

def test_chat_session_history_missing():
    r = client.get("/api/v1/chat/sessions/nonexistent-session/history")
    # Should return 404 since session doesn't exist
    assert r.status_code == 404


def test_clear_session():
    r = client.delete("/api/v1/chat/sessions/test-session-123")
    assert r.status_code == 200


# ── Document Loader Unit Test ──────────────────────────────────────────────────

def test_document_loader_txt():
    from app.core.document_loader import DocumentLoader
    loader = DocumentLoader()

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Hello world.\nThis is a test.\n\nSecond paragraph.")
        tmp_path = f.name

    try:
        docs = loader.load(tmp_path, doc_id="test-001", filename="test.txt")
        assert len(docs) >= 1
        assert "Hello world" in docs[0].page_content
        assert docs[0].metadata["doc_id"] == "test-001"
        assert docs[0].metadata["filename"] == "test.txt"
    finally:
        os.unlink(tmp_path)


def test_document_loader_unsupported():
    from app.core.document_loader import DocumentLoader
    loader = DocumentLoader()
    with pytest.raises(ValueError, match="Unsupported"):
        loader.load("/tmp/file.xyz", doc_id="x", filename="file.xyz")


# ── Text Splitter Unit Test ────────────────────────────────────────────────────

def test_chunking():
    from app.core.rag_pipeline import get_text_splitter
    from langchain.schema import Document

    splitter = get_text_splitter()
    long_text = "This is sentence number {}. " * 200
    doc = Document(page_content=long_text, metadata={"doc_id": "x"})
    chunks = splitter.split_documents([doc])
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.page_content) <= 1200  # chunk_size + small buffer


# ── File Utils Unit Test ───────────────────────────────────────────────────────

def test_file_hash_deterministic():
    from app.utils.file_utils import compute_file_hash
    data = b"test content for hashing"
    h1 = compute_file_hash(data)
    h2 = compute_file_hash(data)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_validate_file_bad_ext():
    from app.utils.file_utils import validate_file
    err = validate_file("file.xyz", b"content", 50)
    assert err is not None
    assert "not allowed" in err.lower()


def test_validate_file_too_large():
    from app.utils.file_utils import validate_file
    big = b"x" * (60 * 1024 * 1024)  # 60 MB
    err = validate_file("file.pdf", big, 50)
    assert err is not None
    assert "exceeds" in err.lower()


def test_validate_file_ok():
    from app.utils.file_utils import validate_file
    err = validate_file("document.pdf", b"small content", 50)
    assert err is None


# ── Session Service Unit Test ──────────────────────────────────────────────────

def test_session_add_and_retrieve():
    from app.services.session_service import SessionService
    svc = SessionService()
    sid = "test-session-xyz-9999"
    svc.clear(sid)  # ensure clean

    svc.add_turn(sid, "Hello?", "Hi there!")
    history = svc.get_history(sid)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello?"
    assert history[1]["role"] == "assistant"

    svc.clear(sid)
    assert svc.get_history(sid) == []
