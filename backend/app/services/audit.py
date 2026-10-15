"""Audit event recording: immutable system_events log + structured log line.

record_event() is best-effort by design -- a failure writing the audit row
must never fail the request/job it's describing. On DB error we log the
failure and continue; we do not raise.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SystemEvent

logger = structlog.get_logger(__name__)


def current_request_id() -> str | None:
    """Read request_id from structlog's context-local vars, if bound.

    Populated by RequestIdMiddleware on the API side. On the worker side,
    worker_tasks must bind it explicitly (no middleware runs there) --
    see worker_tasks/ingest.py.
    """
    return structlog.contextvars.get_contextvars().get("request_id")


async def record_event(
    session: AsyncSession,
    *,
    event_type: str,
    user_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    duration_ms: float | None = None,
    status: str = "success",
    metadata: dict | None = None,
) -> None:
    request_id = current_request_id()

    logger.info(
        "system_event",
        event_type=event_type,
        user_id=str(user_id) if user_id else None,
        document_id=str(document_id) if document_id else None,
        duration_ms=duration_ms,
        status=status,
        **(metadata or {}),
    )

    try:
        session.add(
            SystemEvent(
                event_type=event_type,
                user_id=user_id,
                document_id=document_id,
                request_id=request_id,
                duration_ms=duration_ms,
                status=status,
                event_metadata=metadata,
            )
        )
        await session.flush()
    except Exception:  # noqa: BLE001 -- audit failure must never break the caller
        logger.error("audit_event_write_failed", event_type=event_type, exc_info=True)