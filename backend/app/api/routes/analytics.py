"""Analytics dashboard backend. Internal-only, reuses CurrentUser (no admin role yet)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db_session
from app.services.analytics import (
    daily_event_counts,
    failure_breakdown,
    top_users_by_uploads,
    zero_result_queries,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/uploads/daily")
async def uploads_daily(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(default=7, ge=1, le=90),
) -> list[dict]:
    return await daily_event_counts(session, "UPLOAD_COMPLETED", days)


@router.get("/searches/daily")
async def searches_daily(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(default=7, ge=1, le=90),
) -> list[dict]:
    return await daily_event_counts(session, "SEARCH_EXECUTED", days)


@router.get("/chats/daily")
async def chats_daily(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(default=7, ge=1, le=90),
) -> list[dict]:
    return await daily_event_counts(session, "CHAT_COMPLETED", days)


@router.get("/top-uploaders")
async def top_uploaders(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(default=30, ge=1, le=365),
) -> list[dict]:
    return await top_users_by_uploads(session, days)


@router.get("/failures")
async def failures(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(default=7, ge=1, le=90),
) -> list[dict]:
    return await failure_breakdown(session, days)


@router.get("/zero-result-queries")
async def zero_results(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(default=7, ge=1, le=90),
) -> list[dict]:
    return await zero_result_queries(session, days)