"""Document upload/list/get/delete endpoints. All queries user_id-scoped."""
from __future__ import annotations

import uuid
from typing import Annotated

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_arq_pool, get_storage
from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.models import Document
from app.schemas.documents import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentRead,
    DocumentUploadResponse,
)
from app.services.rate_limit import enforce_rate_limit
from app.services.audit import current_request_id, record_event
from app.services.ingestion import upload_document
from app.storage.base import StorageBackend

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload(
    current_user: CurrentUser,
    file: UploadFile,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    arq_pool=Depends(get_arq_pool),
) -> DocumentUploadResponse:
    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_mb}MB limit",
        )

    document, is_new = await upload_document(
        session=session,
        storage=storage,
        user_id=current_user.id,
        filename=file.filename or "unnamed.pdf",
        data=data,
    )

    if is_new:
        await arq_pool.enqueue_job("process_document_task", str(document.id), current_request_id())

    await record_event(
        session,
        event_type="UPLOAD_COMPLETED",
        user_id=current_user.id,
        document_id=document.id,
        status="duplicate" if not is_new else "new",
        metadata={"filename": document.filename},
    )
    await session.commit()

    return DocumentUploadResponse(id=document.id, filename=document.filename, status=document.status)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentListResponse:
    result = await session.scalars(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())
    )
    items = list(result)
    return DocumentListResponse(items=items, total=len(items))  # type: ignore[arg-type]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    current_user: CurrentUser,
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Document:
    document = await session.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    current_user: CurrentUser,
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> DocumentDeleteResponse:
    document = await session.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await storage.delete(document.storage_path)
    await record_event(
        session, event_type="DOCUMENT_DELETED", user_id=current_user.id, document_id=document.id,
        metadata={"filename": document.filename},
    )
    await session.delete(document)
    await session.commit()
    return DocumentDeleteResponse(id=document_id, deleted=True)



@router.get("/{document_id}/status/stream")
async def stream_status(
    current_user: CurrentUser,
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    """SSE stream of pipeline status until terminal (indexed/failed).
    Polls DB every 500ms -- simple, avoids adding LISTEN/NOTIFY infra."""
    TERMINAL = {"indexed", "failed"}

    async def events():
        last_status = None
        for _ in range(120):  # ~60s max, avoids an infinite hang if row vanishes
            doc = await session.scalar(
                select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
            )
            if doc is None:
                yield f"data: {json.dumps({'error': 'not found'})}\n\n"
                return
            if doc.status != last_status:
                yield f"data: {json.dumps({'status': doc.status})}\n\n"
                last_status = doc.status
            if doc.status in TERMINAL:
                return
            await asyncio.sleep(0.5)

    return StreamingResponse(events(), media_type="text/event-stream")