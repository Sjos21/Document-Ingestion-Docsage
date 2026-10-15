"""Analytics queries over system_events for dashboard rendering."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SystemEvent


async def daily_event_counts(session: AsyncSession, event_type: str, days: int = 7) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=days)
    day_col = func.date(SystemEvent.created_at)
    stmt = (
        select(day_col.label("day"), func.count().label("count"))
        .where(SystemEvent.event_type == event_type, SystemEvent.created_at >= since)
        .group_by(day_col)
        .order_by(day_col)
    )
    rows = (await session.execute(stmt)).all()
    return [{"day": str(r.day), "count": r.count} for r in rows]


async def top_users_by_uploads(session: AsyncSession, days: int = 30, limit: int = 10) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        select(SystemEvent.user_id, func.count().label("count"))
        .where(SystemEvent.event_type == "UPLOAD_COMPLETED", SystemEvent.created_at >= since)
        .group_by(SystemEvent.user_id)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [{"user_id": str(r.user_id), "upload_count": r.count} for r in rows if r.user_id]


async def failure_breakdown(session: AsyncSession, days: int = 7) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        select(SystemEvent.event_type, SystemEvent.status, func.count().label("count"))
        .where(SystemEvent.status.in_(["failed", "error"]), SystemEvent.created_at >= since)
        .group_by(SystemEvent.event_type, SystemEvent.status)
        .order_by(func.count().desc())
    )
    rows = (await session.execute(stmt)).all()
    return [{"event_type": r.event_type, "status": r.status, "count": r.count} for r in rows]


async def zero_result_queries(session: AsyncSession, days: int = 7, limit: int = 20) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        select(SystemEvent.created_at, SystemEvent.event_metadata)
        .where(
            SystemEvent.event_type == "SEARCH_EXECUTED",
            SystemEvent.status == "zero_results",
            SystemEvent.created_at >= since,
        )
        .order_by(SystemEvent.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [{"created_at": r.created_at.isoformat(), "metadata": r.event_metadata} for r in rows]