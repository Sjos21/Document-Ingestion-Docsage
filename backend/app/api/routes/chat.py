"""Chat endpoints: single response, SSE stream, and session history."""
from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db_session
from app.models import ChatMessage, ChatSession
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatResponse, ChatSessionRead
from app.services.chat import (
    NO_CONTEXT_ANSWER,
    SYSTEM_PROMPT,
    build_context_prompt,
    get_or_create_session,
    send_message,
    send_message_traced,
)
from app.services.rate_limit import enforce_rate_limit
from app.services.llm import stream_chat_response
from app.services.retrieval import search_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    current_user: CurrentUser,
    payload: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatResponse:
    chat_session, answer, sources, trace = await send_message_traced(
        session=session, user_id=current_user.id, message=payload.message, session_id=payload.session_id
    )
    return ChatResponse(session_id=chat_session.id, answer=answer, sources=sources, trace=trace)


@router.post("/stream")
async def chat_stream(
    current_user: CurrentUser,
    payload: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    chat_session = await get_or_create_session(session, current_user.id, payload.session_id)
    session.add(ChatMessage(session_id=chat_session.id, role="user", content=payload.message))
    await session.flush()

    hits = await search_chunks(session=session, user_id=current_user.id, query=payload.message, top_k=5)

    async def event_generator():
        collected = ""
        if not hits:
            collected = NO_CONTEXT_ANSWER
            yield f"data: {json.dumps({'token': collected})}\n\n"
        else:
            prompt = build_context_prompt(payload.message, hits)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
            async for token in stream_chat_response(messages):
                collected += token
                yield f"data: {json.dumps({'token': token})}\n\n"

        session.add(ChatMessage(session_id=chat_session.id, role="assistant", content=collected))
        await session.commit()
        yield f"data: {json.dumps({'session_id': str(chat_session.id), 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions", response_model=list[ChatSessionRead])
async def list_sessions(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ChatSession]:
    result = await session.scalars(
        select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc())
    )
    return list(result)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
async def get_session_messages(
    current_user: CurrentUser,
    session_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ChatMessage]:
    chat_session = await session.get(ChatSession, session_id)
    if chat_session is None or chat_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    result = await session.scalars(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    )
    return list(result)