"""arq task wrapper for document processing.

request_id is passed explicitly from the API layer at enqueue time (see
api/routes/documents.py) and re-bound into structlog's contextvars here,
since arq workers run outside any request/middleware context. This is what
lets a single request_id correlate API log lines with worker log lines for
the same upload -- e.g. filtering logs by request_id shows the full
upload -> enqueue -> extract -> chunk -> embed -> indexed lifecycle.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

from app.config import get_settings
from app.db.session import async_session_factory
from app.services.audit import record_event
from app.services.ingestion import process_document
from app.storage.local import LocalStorage

logger = structlog.get_logger(__name__)


async def process_document_task(
    ctx: dict[str, Any], document_id: str, request_id: str | None = None
) -> None:
    structlog.contextvars.clear_contextvars()
    if request_id:
        structlog.contextvars.bind_contextvars(request_id=request_id)

    storage = LocalStorage(get_settings().storage_path)
    doc_uuid = uuid.UUID(document_id)
    started_at = time.perf_counter()

    async with async_session_factory() as session:
        await record_event(session, event_type="INDEXING_STARTED", document_id=doc_uuid)
        await session.commit()

        await process_document(session=session, storage=storage, document_id=doc_uuid)

        document = await session.get(__import__("app.models", fromlist=["Document"]).Document, doc_uuid)
        duration_ms = (time.perf_counter() - started_at) * 1000
        await record_event(
            session,
            event_type="INDEXING_COMPLETED",
            document_id=doc_uuid,
            user_id=document.user_id if document else None,
            duration_ms=duration_ms,
            status=document.status if document else "unknown",
            metadata={"status_reason": document.status_reason} if document and document.status_reason else None,
        )
        await session.commit()