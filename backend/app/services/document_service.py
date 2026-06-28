"""
Document Service - manages document metadata (status, chunks, file info).
Uses a JSON file as a lightweight persistent store (swap for PostgreSQL in production).
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

METADATA_FILE = "./data/documents.json"
_lock = threading.Lock()


class DocumentService:
    """
    Thread-safe document metadata store backed by a JSON file.
    In production, replace with SQLAlchemy + PostgreSQL.
    """

    def __init__(self):
        self._path = Path(METADATA_FILE)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict:
        if not self._path.exists():
            return {}
        with open(self._path, "r") as f:
            return json.load(f)

    def _save(self, data: Dict):
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def register(
        self,
        doc_id: str,
        filename: str,
        file_path: str,
        file_size_kb: float,
        file_hash: str,
    ):
        with _lock:
            data = self._load()
            data[doc_id] = {
                "doc_id":        doc_id,
                "filename":      filename,
                "file_path":     file_path,
                "file_size_kb":  round(file_size_kb, 2),
                "file_hash":     file_hash,
                "status":        "pending",
                "chunks_created": 0,
                "created_at":    datetime.utcnow().isoformat(),
                "updated_at":    datetime.utcnow().isoformat(),
            }
            self._save(data)

    def update_status(self, doc_id: str, status: str, chunks_created: int = 0):
        with _lock:
            data = self._load()
            if doc_id in data:
                data[doc_id]["status"] = status
                data[doc_id]["chunks_created"] = chunks_created
                data[doc_id]["updated_at"] = datetime.utcnow().isoformat()
                self._save(data)

    def get(self, doc_id: str) -> Optional[Dict]:
        data = self._load()
        return data.get(doc_id)

    def list_all(self) -> List[Dict]:
        data = self._load()
        return sorted(data.values(), key=lambda d: d["created_at"], reverse=True)

    def delete(self, doc_id: str):
        with _lock:
            data = self._load()
            data.pop(doc_id, None)
            self._save(data)
