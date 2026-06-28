"""
Vector Store - FAISS backend.
Fixed: use similarity_search (not relevance scores) since HuggingFace+FAISS
returns negative L2-distance scores which break threshold filtering.
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from app.config import settings
from app.core.embeddings import get_langchain_embeddings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    def __init__(self):
        self.store_type = settings.VECTOR_STORE_TYPE
        self._store = None
        self._initialized = False
        self._doc_chunk_map: Dict[str, List[str]] = {}

    def initialize(self):
        if self._initialized:
            return
        if self.store_type == "faiss":
            self._init_faiss()
        elif self.store_type == "chroma":
            self._init_chroma()
        else:
            raise ValueError(f"Unknown vector store: {self.store_type}")
        self._initialized = True

    def _init_faiss(self):
        from langchain_community.vectorstores import FAISS
        index_path = Path(settings.FAISS_INDEX_PATH)
        embeddings = get_langchain_embeddings()

        index_file = index_path / "index.faiss"
        if index_file.exists() and index_file.stat().st_size > 0:
            logger.info(f"📦 Loading existing FAISS index from {index_path}")
            try:
                self._store = FAISS.load_local(
                    str(index_path), embeddings, allow_dangerous_deserialization=True
                )
                self._load_chunk_map()
                logger.info(f"✅ FAISS loaded: {self._store.index.ntotal} vectors")
                return
            except Exception as e:
                logger.warning(f"⚠️  Failed to load index ({e}), starting fresh")

        logger.info("🆕 Starting with empty FAISS store")
        self._store = None

    def _init_chroma(self):
        from langchain_community.vectorstores import Chroma
        embeddings = get_langchain_embeddings()
        persist_dir = settings.CHROMA_PERSIST_DIR
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._store = Chroma(
            collection_name=settings.CHROMA_COLLECTION,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )

    def add_documents(self, docs: List[Document]) -> int:
        if not docs:
            return 0
        embeddings = get_langchain_embeddings()

        if self.store_type == "faiss":
            from langchain_community.vectorstores import FAISS
            if self._store is None:
                logger.info(f"🆕 Creating FAISS index with {len(docs)} chunks")
                self._store = FAISS.from_documents(docs, embeddings)
                ids = list(self._store.docstore._dict.keys())
            else:
                ids = self._store.add_documents(docs)
        else:
            ids = self._store.add_documents(docs)

        for doc, chunk_id in zip(docs, ids):
            doc_id = doc.metadata.get("doc_id", "unknown")
            self._doc_chunk_map.setdefault(doc_id, []).append(chunk_id)

        logger.info(f"📥 Added {len(docs)} chunks. Total: {self.get_total_chunks()}")
        return len(docs)

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        doc_ids: Optional[List[str]] = None,
        score_threshold: float = 0.0,  # kept for API compat, ignored now
    ) -> List[Tuple[Document, float]]:
        if self._store is None:
            logger.warning("⚠️  Vector store is empty")
            return []

        total = self.get_total_chunks()
        if total == 0:
            logger.warning("⚠️  FAISS index has 0 vectors")
            return []

        # Use plain similarity_search — avoids the broken negative-score issue
        # with HuggingFace embeddings + FAISS L2 distance
        fetch_k = min(top_k * 3 if doc_ids else top_k * 2, total)

        try:
            docs = self._store.similarity_search(query, k=fetch_k)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

        # Pair with a dummy score of 1.0 (we don't use scores for filtering anymore)
        results: List[Tuple[Document, float]] = [(doc, 1.0) for doc in docs]

        # Filter by doc_id if requested
        if doc_ids:
            results = [
                (doc, score) for doc, score in results
                if doc.metadata.get("doc_id") in doc_ids
            ]

        # Skip the internal __init__ dummy doc
        results = [
            (doc, score) for doc, score in results
            if doc.metadata.get("doc_id") != "__init__"
        ][:top_k]

        logger.info(f"🔍 Query returned {len(results)} results")
        return results

    def delete_by_doc_id(self, doc_id: str):
        if self._store is None:
            return
        chunk_ids = self._doc_chunk_map.pop(doc_id, [])
        if self.store_type == "faiss":
            self._rebuild_faiss_without(doc_id)
        elif self.store_type == "chroma":
            self._store.delete(ids=chunk_ids)
        logger.info(f"🗑️  Removed chunks for doc_id={doc_id}")

    def _rebuild_faiss_without(self, exclude_doc_id: str):
        from langchain_community.vectorstores import FAISS
        embeddings = get_langchain_embeddings()
        all_docs = [
            doc for doc in self._store.docstore._dict.values()
            if doc.metadata.get("doc_id") != exclude_doc_id
        ]
        self._store = FAISS.from_documents(all_docs, embeddings) if all_docs else None

    def get_chunks_by_doc_id(self, doc_id: str, page: int = 1, per_page: int = 10):
        if self._store is None:
            return []
        chunks = [
            {"content": doc.page_content[:300], "metadata": doc.metadata}
            for doc in self._store.docstore._dict.values()
            if doc.metadata.get("doc_id") == doc_id
        ]
        start = (page - 1) * per_page
        return chunks[start: start + per_page]

    def get_total_chunks(self) -> int:
        if self._store is None:
            return 0
        if self.store_type == "faiss":
            # subtract the __init__ dummy doc if present
            total = self._store.index.ntotal
            has_dummy = any(
                doc.metadata.get("doc_id") == "__init__"
                for doc in self._store.docstore._dict.values()
            )
            return max(0, total - (1 if has_dummy else 0))
        return 0

    def save(self):
        if self._store is None:
            return
        if self.store_type == "faiss":
            path = settings.FAISS_INDEX_PATH
            Path(path).mkdir(parents=True, exist_ok=True)
            self._store.save_local(path)
            self._save_chunk_map()
            logger.info(f"💾 FAISS saved: {self.get_total_chunks()} vectors → {path}")

    def _save_chunk_map(self):
        path = Path(settings.FAISS_INDEX_PATH) / "chunk_map.pkl"
        with open(path, "wb") as f:
            pickle.dump(self._doc_chunk_map, f)

    def _load_chunk_map(self):
        path = Path(settings.FAISS_INDEX_PATH) / "chunk_map.pkl"
        if path.exists():
            with open(path, "rb") as f:
                self._doc_chunk_map = pickle.load(f)