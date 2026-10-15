"""Operational metrics derived from system_events + live tables.

Internal-only: no auth changes yet, reuses CurrentUser (any authenticated
user can view). Restrict to an admin role in a later phase if needed.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db_session
from app.models import ChatMessage, Document, SystemEvent

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def metrics(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    since_24h = datetime.now(UTC) - timedelta(hours=24)

    uploads_24h = await session.scalar(
        select(func.count()).select_from(SystemEvent).where(
            SystemEvent.event_type == "UPLOAD_COMPLETED", SystemEvent.created_at >= since_24h
        )
    )
    failed_indexing_24h = await session.scalar(
        select(func.count()).select_from(SystemEvent).where(
            SystemEvent.event_type == "INDEXING_COMPLETED",
            SystemEvent.status == "failed",
            SystemEvent.created_at >= since_24h,
        )
    )
    searches_24h = await session.scalar(
        select(func.count()).select_from(SystemEvent).where(
            SystemEvent.event_type == "SEARCH_EXECUTED", SystemEvent.created_at >= since_24h
        )
    )
    zero_result_searches_24h = await session.scalar(
        select(func.count()).select_from(SystemEvent).where(
            SystemEvent.event_type == "SEARCH_EXECUTED",
            SystemEvent.status == "zero_results",
            SystemEvent.created_at >= since_24h,
        )
    )
    avg_search_latency_ms = await session.scalar(
        select(func.avg(SystemEvent.duration_ms)).where(
            SystemEvent.event_type == "SEARCH_EXECUTED", SystemEvent.created_at >= since_24h
        )
    )
    chats_24h = await session.scalar(
        select(func.count()).select_from(SystemEvent).where(
            SystemEvent.event_type == "CHAT_COMPLETED", SystemEvent.created_at >= since_24h
        )
    )
    refused_chats_24h = await session.scalar(
        select(func.count()).select_from(SystemEvent).where(
            SystemEvent.event_type == "CHAT_COMPLETED",
            SystemEvent.status == "refused",
            SystemEvent.created_at >= since_24h,
        )
    )
    total_documents = await session.scalar(select(func.count()).select_from(Document))
    total_indexed = await session.scalar(select(func.count()).select_from(Document).where(Document.status == "indexed"))
    total_chat_messages = await session.scalar(select(func.count()).select_from(ChatMessage))

    return {
        "window": "24h",
        "uploads": uploads_24h or 0,
        "failed_indexing": failed_indexing_24h or 0,
        "searches": searches_24h or 0,
        "zero_result_searches": zero_result_searches_24h or 0,
        "avg_search_latency_ms": round(avg_search_latency_ms, 2) if avg_search_latency_ms else None,
        "chats": chats_24h or 0,
        "refused_chats": refused_chats_24h or 0,
        "totals": {
            "documents": total_documents or 0,
            "indexed_documents": total_indexed or 0,
            "chat_messages": total_chat_messages or 0,
        },
    }