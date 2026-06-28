"""Chat API — uses global pipeline singleton."""

import json
import logging
import uuid
from typing import AsyncIterator, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.pipeline_singleton import get_pipeline
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4096)
    session_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    stream: bool = True
    top_k: int = Field(default=5, ge=1, le=20)
    include_sources: bool = True


class Source(BaseModel):
    document_id: str
    filename: str
    page: Optional[int] = None
    chunk_index: int
    relevance_score: float
    excerpt: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[Source] = []
    tokens_used: int = 0


class SummaryRequest(BaseModel):
    document_id: str
    style: str = "concise"


@router.post("/")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    session_service = SessionService()
    pipeline = get_pipeline()          # ← same singleton
    history = session_service.get_history(session_id)

    if request.stream:
        return StreamingResponse(
            _stream_response(pipeline, session_service, request, session_id, history),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    result = pipeline.query(
        question=request.question,
        chat_history=history,
        document_ids=request.document_ids,
        top_k=request.top_k,
    )
    session_service.add_turn(session_id, request.question, result["answer"])
    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        sources=[Source(**s) for s in result.get("sources", [])],
        tokens_used=result.get("tokens_used", 0),
    )


async def _stream_response(pipeline, session_service, request, session_id, history) -> AsyncIterator[str]:
    full_answer = ""
    try:
        sources_data = pipeline.retrieve_sources(
            question=request.question,
            document_ids=request.document_ids,
            top_k=request.top_k,
        )

        yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id, 'sources': sources_data if request.include_sources else []})}\n\n"

        async for token in pipeline.stream_answer(
            question=request.question,
            sources=sources_data,
            chat_history=history,
        ):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'full_answer': full_answer})}\n\n"
        session_service.add_turn(session_id, request.question, full_answer)

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    history = SessionService().get_history(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": history}


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    SessionService().clear(session_id)
    return {"message": f"Session {session_id} cleared"}


@router.post("/summarize")
async def summarize_document(request: SummaryRequest):
    summary = get_pipeline().summarize(document_id=request.document_id, style=request.style)
    return {"document_id": request.document_id, "summary": summary}


@router.post("/search")
async def semantic_search(query: str, top_k: int = 5, document_ids: Optional[List[str]] = None):
    results = get_pipeline().retrieve_sources(question=query, document_ids=document_ids, top_k=top_k)
    return {"query": query, "results": results}