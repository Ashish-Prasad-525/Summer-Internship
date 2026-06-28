"""
RAG Pipeline - LangChain 0.3+ + Ollama compatible.
"""

import logging
from typing import AsyncIterator, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.core.vectorstore import VectorStoreManager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intelligent document assistant. Answer questions based EXCLUSIVELY on the provided document context.

STRICT RULES:
1. Answer ONLY using information from the provided context
2. If the answer is not in the context, say: "I couldn't find this information in the uploaded documents."
3. Always cite sources using [Document: filename, Page: X] format
4. Never hallucinate or make up information
5. Provide concise, accurate, helpful responses

CONTEXT:
{context}

CHAT HISTORY:
{chat_history}
"""


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )


def _load_llm(streaming: bool = False):
    """Load LLM with multiple fallback import paths for Ollama."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=streaming,
        )

    elif provider == "ollama":
        # Try langchain-ollama package first (recommended for LangChain 0.3+)
        try:
            from langchain_ollama import ChatOllama
            logger.info("Using langchain_ollama.ChatOllama")
            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
            )
        except ImportError:
            pass

        # Fallback: langchain_community
        try:
            from langchain_community.chat_models import ChatOllama
            logger.info("Using langchain_community ChatOllama")
            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
            )
        except ImportError:
            pass

        # Last fallback: direct ollama package
        try:
            from langchain_community.llms import Ollama
            logger.info("Using langchain_community Ollama LLM")
            return Ollama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
            )
        except ImportError:
            raise ImportError(
                "No Ollama LangChain package found. Run:\n"
                "  pip install langchain-ollama"
            )

    raise ValueError(f"Unknown LLM provider: {provider}")


class RAGPipeline:
    def __init__(self):
        self.vectorstore = VectorStoreManager()
        self.vectorstore.initialize()
        self.splitter = get_text_splitter()
        self._llm = None
        self._llm_streaming = None

    def _get_llm(self, streaming: bool = False):
        if streaming and self._llm_streaming:
            return self._llm_streaming
        if not streaming and self._llm:
            return self._llm

        llm = _load_llm(streaming=streaming)
        logger.info(f"✅ LLM loaded: {settings.LLM_PROVIDER} (streaming={streaming})")

        if streaming:
            self._llm_streaming = llm
        else:
            self._llm = llm
        return llm

    def index_documents(self, docs: List[Document]) -> int:
        if not docs:
            return 0
        chunks = self.splitter.split_documents(docs)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_count"] = len(chunks)
        count = self.vectorstore.add_documents(chunks)
        self.vectorstore.save()
        return count

    def retrieve_sources(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        results = self.vectorstore.similarity_search(
            query=question,
            top_k=top_k,
            doc_ids=document_ids,
            score_threshold=settings.SIMILARITY_THRESHOLD,
        )
        sources = []
        for doc, score in results:
            if doc.metadata.get("doc_id") == "__init__":
                continue
            sources.append({
                "document_id":     doc.metadata.get("doc_id", ""),
                "filename":        doc.metadata.get("filename", ""),
                "page":            doc.metadata.get("page"),
                "chunk_index":     doc.metadata.get("chunk_index", 0),
                "relevance_score": round(float(score), 4),
                "excerpt":         doc.page_content[:500],
                "full_content":    doc.page_content,
            })
        return sources

    def query(
        self,
        question: str,
        chat_history: Optional[List[Dict]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict:
        sources = self.retrieve_sources(question, document_ids, top_k)

        if not sources:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents.",
                "sources": [],
                "tokens_used": 0,
            }

        context = self._build_context(sources)
        history_str = self._format_history(chat_history or [])
        prompt = SYSTEM_PROMPT.format(context=context, chat_history=history_str)

        llm = self._get_llm(streaming=False)

        # Ollama works better with a single combined message
        try:
            messages = [SystemMessage(content=prompt), HumanMessage(content=question)]
            response = llm.invoke(messages)
        except Exception:
            # Fallback: combine into one HumanMessage (some Ollama versions need this)
            combined = f"{prompt}\n\nQuestion: {question}"
            response = llm.invoke([HumanMessage(content=combined)])

        answer = response.content if hasattr(response, "content") else str(response)
        tokens = getattr(response, "usage_metadata", {}) or {}

        return {
            "answer":      answer,
            "sources":     sources,
            "tokens_used": tokens.get("total_tokens", 0),
        }

    async def stream_answer(
        self,
        question: str,
        sources: List[Dict],
        chat_history: Optional[List[Dict]] = None,
    ) -> AsyncIterator[str]:
        if not sources:
            yield "I couldn't find any relevant information in the uploaded documents."
            return

        context = self._build_context(sources)
        history_str = self._format_history(chat_history or [])
        prompt = SYSTEM_PROMPT.format(context=context, chat_history=history_str)

        llm = self._get_llm(streaming=True)

        try:
            messages = [SystemMessage(content=prompt), HumanMessage(content=question)]
            async for chunk in llm.astream(messages):
                token = chunk.content if hasattr(chunk, "content") else str(chunk)
                if token:
                    yield token
        except Exception as e:
            logger.warning(f"Streaming failed ({e}), falling back to non-streaming")
            # Graceful fallback for Ollama models that don't support astream well
            result = self.query(question, chat_history, None, 5)
            yield result["answer"]

    def summarize(self, document_id: str, style: str = "concise") -> str:
        chunks = self.vectorstore.get_chunks_by_doc_id(document_id, page=1, per_page=20)
        if not chunks:
            return "Document not found or not yet indexed."

        combined = "\n\n".join(c["content"] for c in chunks)
        style_map = {
            "concise":       "Provide a 2-3 sentence executive summary.",
            "detailed":      "Provide a comprehensive summary covering all main topics.",
            "bullet_points": "Provide a bullet-point summary of key points.",
        }
        instruction = style_map.get(style, style_map["concise"])
        prompt = (
            f"Summarize the following document.\n\nStyle: {instruction}\n\n"
            f"CONTENT:\n{combined[:12000]}\n\n"
            "Base your summary ONLY on the provided content."
        )
        llm = self._get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content if hasattr(response, "content") else str(response)

    def _build_context(self, sources: List[Dict]) -> str:
        parts = []
        for i, src in enumerate(sources, 1):
            parts.append(
                f"[{i}] Document: {src['filename']}, Page: {src.get('page', 'N/A')}\n"
                f"{src['full_content']}\n"
            )
        return "\n---\n".join(parts)

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for turn in history[-6:]:
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")[:300]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)