"""Ingestion orchestration: upload registration + async processing pipeline.

upload_document(): called from the API layer. Hashes the file, checks for
an existing (user_id, content_hash) match (idempotency), persists via
StorageBackend, creates the Document row, and returns it. Does NOT extract/
embed â€” that happens in process_document(), run by the arq worker.

process_document(): called from worker_tasks/ingest.py. Extracts, chunks,
embeds, and stores Chunk rows. Sets status=indexed on success or
status=failed with a reason on any handled failure. Never raises past this
function for expected failure modes -- the worker task loop must not die
because one document is corrupt.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Document
from app.services.chunking import chunk_text
from app.services.embedding import EMBEDDING_MODEL_VERSION, embed_texts
from app.services.extraction import ExtractionError, extract_text_from_pdf
from app.storage.base import StorageBackend


async def upload_document(
    *,
    session: AsyncSession,
    storage: StorageBackend,
    user_id: uuid.UUID,
    filename: str,
    data: bytes,
) -> tuple[Document, bool]:
    """Register an uploaded file. Returns (document, is_new).

    is_new=False means this exact file was already uploaded by this user;
    the existing Document is returned unchanged and nothing is re-processed.
    """
    content_hash = hashlib.sha256(data).hexdigest()

    existing = await session.scalar(
        select(Document).where(
            Document.user_id == user_id, Document.content_hash == content_hash
        )
    )
    if existing is not None:
        return existing, False

    storage_key = f"{user_id}/{content_hash}_{filename}"
    await storage.save(storage_key, data)

    document = Document(
        user_id=user_id,
        filename=filename,
        content_hash=content_hash,
        storage_path=storage_key,
        status="uploaded",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document, True


async def process_document(
    *,
    session: AsyncSession,
    storage: StorageBackend,
    document_id: uuid.UUID,
) -> None:
    """Extract -> chunk -> embed -> store. Sets terminal status on the row.

    Idempotent at the chunk level is not required here: this only runs once
    per new document (upload_document already dedupes at the file level).
    """
    document = await session.get(Document, document_id)
    if document is None:
        return  # deleted before the job ran; nothing to do

    document.status = "extracting"
    await session.commit()

    try:
        import tempfile

        raw_bytes = await storage.load(document.storage_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        try:
            text = extract_text_from_pdf(tmp_path)
        finally:
            import os

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        document.status = "chunking"
        await session.commit()

        pieces = chunk_text(text)
        if not pieces:
            raise ExtractionError("chunking produced zero chunks from extracted text")

        document.status = "embedding"
        await session.commit()

        vectors = embed_texts([p.content for p in pieces])

        document.status = "indexing"
        await session.commit()

        for piece, vector in zip(pieces, vectors, strict=True):
            session.add(
                Chunk(
                    document_id=document.id,
                    content=piece.content,
                    embedding=vector,
                    token_count=piece.token_count,
                    embedding_model_version=EMBEDDING_MODEL_VERSION,
                )
            )

        document.status = "indexed"
        document.status_reason = None
        document.indexed_at = datetime.now(UTC)
        await session.commit()

    except ExtractionError as exc:
        document.status = "failed"
        document.status_reason = str(exc)[:512]
        await session.commit()
    except Exception as exc:  # noqa: BLE001 â€” must not crash the worker loop
        document.status = "failed"
        document.status_reason = f"unexpected error: {exc}"[:512]
        await session.commit()

