"""Chat orchestration: hybrid retrieval -> grounding -> generation -> persist.

Refusal guardrail: if hybrid search returns zero chunks, the LLM is never
called -- the canned NO_CONTEXT_ANSWER is returned directly. This is a
hard code path, not a prompt instruction the model could ignore.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import time

from app.models import ChatMessage, ChatSession
from app.services.audit import record_event
from app.schemas.chat import SourceRef
from app.services.llm import generate_chat_response
from app.services.retrieval import search_chunks, search_chunks_traced
from app.schemas.chat import ChatTrace

NO_CONTEXT_ANSWER = "I don't have relevant information in your documents to answer that."

SYSTEM_PROMPT = (
    "You are DocSage, an assistant that answers questions using ONLY the "
    "provided document excerpts. If the excerpts don't contain the answer, "
    "say so plainly. Do not use outside knowledge. Cite excerpt numbers "
    "like [1], [2] when relevant."
)


def build_context_prompt(query: str, hits: list) -> str:
    excerpts = "\n\n".join(f"[{i + 1}] ({h.filename}) {h.content}" for i, h in enumerate(hits))
    return f"Document excerpts:\n{excerpts}\n\nQuestion: {query}"


async def get_or_create_session(
    session: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID | None
) -> ChatSession:
    """Reuse an existing session only if it belongs to this user; otherwise
    silently start a new one rather than 404ing mid-conversation."""
    if session_id is not None:
        existing = await session.get(ChatSession, session_id)
        if existing is not None and existing.user_id == user_id:
            return existing

    new_session = ChatSession(user_id=user_id)
    session.add(new_session)
    await session.flush()
    return new_session


async def send_message(
    *, session: AsyncSession, user_id: uuid.UUID, message: str, session_id: uuid.UUID | None
) -> tuple[ChatSession, str, list[SourceRef]]:
    started_at = time.perf_counter()
    chat_session = await get_or_create_session(session, user_id, session_id)
    session.add(ChatMessage(session_id=chat_session.id, role="user", content=message))

    hits = await search_chunks(session=session, user_id=user_id, query=message, top_k=5)

    if not hits:
        answer = NO_CONTEXT_ANSWER
        sources: list[SourceRef] = []
    else:
        prompt = build_context_prompt(message, hits)
        answer = await generate_chat_response(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        sources = [
            SourceRef(chunk_id=h.chunk_id, document_id=h.document_id, filename=h.filename, score=h.score)
            for h in hits
        ]

    session.add(ChatMessage(session_id=chat_session.id, role="assistant", content=answer))
    await record_event(
        session,
        event_type="CHAT_COMPLETED",
        user_id=user_id,
        duration_ms=(time.perf_counter() - started_at) * 1000,
        status="refused" if not hits else "success",
        metadata={"source_count": len(sources)},
    )
    await session.commit()
    await session.refresh(chat_session)
    return chat_session, answer, sources



async def send_message_traced(
    *, session: AsyncSession, user_id: uuid.UUID, message: str, session_id: uuid.UUID | None
) -> tuple[ChatSession, str, list[SourceRef], ChatTrace]:
    """Same as send_message, but uses the traced retrieval pipeline and
    returns per-stage timings for the frontend transparency panel."""
    started_at = time.perf_counter()
    chat_session = await get_or_create_session(session, user_id, session_id)
    session.add(ChatMessage(session_id=chat_session.id, role="user", content=message))

    hits, retrieval_trace = await search_chunks_traced(session=session, user_id=user_id, query=message, top_k=5)

    gen_start = time.perf_counter()
    if not hits:
        answer = NO_CONTEXT_ANSWER
        sources: list[SourceRef] = []
    else:
        prompt = build_context_prompt(message, hits)
        answer = await generate_chat_response(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        sources = [
            SourceRef(chunk_id=h.chunk_id, document_id=h.document_id, filename=h.filename, score=h.score)
            for h in hits
        ]
    generation_ms = (time.perf_counter() - gen_start) * 1000

    session.add(ChatMessage(session_id=chat_session.id, role="assistant", content=answer))
    await record_event(
        session, event_type="CHAT_COMPLETED", user_id=user_id,
        duration_ms=(time.perf_counter() - started_at) * 1000,
        status="refused" if not hits else "success",
        metadata={"source_count": len(sources)},
    )
    await session.commit()
    await session.refresh(chat_session)

    trace = ChatTrace(
        vector_ms=retrieval_trace.vector_ms, bm25_ms=retrieval_trace.bm25_ms,
        fusion_ms=retrieval_trace.fusion_ms, rerank_ms=retrieval_trace.rerank_ms,
        generation_ms=generation_ms, vector_count=retrieval_trace.vector_count,
        bm25_count=retrieval_trace.bm25_count, fused_count=retrieval_trace.fused_count,
    )
    return chat_session, answer, sources, trace
