# ============================================================
# Phase 2 — Ingestion Pipeline — full build script
# Run from repo root: D:\Projects\docsage
# Idempotent: safe to re-run, overwrites target files.
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location "D:\Projects\docsage"
$be = "backend"

function Write-Utf8NoBom($Path, $Content) {
    $full = Join-Path (Get-Location) $Path
    New-Item -ItemType Directory -Force -Path (Split-Path $full) | Out-Null
    [System.IO.File]::WriteAllText($full, $Content, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[written] $Path" -ForegroundColor Green
}

# ---------------------------------------------------------------
# 1. pyproject.toml — add pymupdf + sentence-transformers + tiktoken-free chunker deps
# ---------------------------------------------------------------
$pyproj = "$be\pyproject.toml"
$raw = Get-Content $pyproj -Raw
if ($raw -notmatch "pymupdf") {
    $raw = $raw -replace '"pgvector>=0.3.0",', "`"pgvector>=0.3.0`",`n    `"pymupdf>=1.24.0`",`n    `"sentence-transformers>=3.0.0`","
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $pyproj), $raw, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[updated] $pyproj (+pymupdf, +sentence-transformers)" -ForegroundColor Green
} else {
    Write-Host "[skip] pyproject.toml already has pymupdf" -ForegroundColor Yellow
}

# ---------------------------------------------------------------
# 2. schemas/documents.py
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\schemas\documents.py" @'
"""Pydantic schemas for document ingestion endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class DocumentRead(BaseModel):
    """Response shape for a single document."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: DocumentStatus
    status_reason: str | None = None
    indexed_at: datetime | None = None
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    total: int


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus = DocumentStatus.uploaded


class DocumentDeleteResponse(BaseModel):
    id: uuid.UUID
    deleted: bool = True
'@

# ---------------------------------------------------------------
# 3. services/extraction.py
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\services\extraction.py" @'
"""PDF text extraction service.

Raises ExtractionError on any failure so callers (worker_tasks/ingest.py)
can catch one exception type and set Document.status=failed with a clear
reason, instead of letting raw PyMuPDF exceptions crash the job.
"""
from __future__ import annotations

import fitz  # PyMuPDF


class ExtractionError(Exception):
    """Raised when a PDF cannot be parsed or yields no extractable text."""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract concatenated text from all pages of a PDF.

    Raises:
        ExtractionError: missing, corrupt, encrypted, zero-page, or
            no extractable text (e.g. scanned image PDF — OCR deferred).
    """
    try:
        doc = fitz.open(file_path)
    except fitz.FileDataError as exc:
        raise ExtractionError(f"corrupt or unreadable PDF: {exc}") from exc
    except FileNotFoundError as exc:
        raise ExtractionError(f"file not found: {exc}") from exc

    try:
        if doc.is_encrypted:
            raise ExtractionError("PDF is encrypted; password-protected files unsupported")
        if doc.page_count == 0:
            raise ExtractionError("PDF has zero pages")
        pages = [page.get_text("text") for page in doc]
    finally:
        doc.close()

    full_text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not full_text:
        raise ExtractionError(
            "no extractable text found -- likely a scanned/image-only PDF "
            "(OCR deferred to a later phase)"
        )
    return full_text
'@

# ---------------------------------------------------------------
# 4. services/chunking.py
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\services\chunking.py" @'
"""Text chunking for embedding ingestion.

Word-count based approximation of token count (no tokenizer dependency
needed for the embedding model in use). ~500 "tokens" per chunk with
~50 overlap, matching architecture.md.
"""
from __future__ import annotations

from dataclasses import dataclass

CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 50


@dataclass(frozen=True)
class TextChunk:
    content: str
    token_count: int  # approximate (word count)


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS,
) -> list[TextChunk]:
    """Split text into overlapping word-count-bounded chunks.

    Raises ValueError if overlap >= chunk_size (would never advance).
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    start = 0
    step = chunk_size - overlap

    while start < len(words):
        end = min(start + chunk_size, len(words))
        piece = words[start:end]
        chunks.append(TextChunk(content=" ".join(piece), token_count=len(piece)))
        if end == len(words):
            break
        start += step

    return chunks
'@

# ---------------------------------------------------------------
# 5. services/embedding.py
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\services\embedding.py" @'
"""Embedding generation via sentence-transformers (local, CPU-only)."""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL_VERSION = EMBEDDING_MODEL_NAME  # stored on each chunk row
EMBEDDING_DIM = 384


@lru_cache
def _get_model() -> SentenceTransformer:
    """Load once per process; sentence-transformers handles thread-safety
    for encode() calls on a shared model instance."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of chunk texts. Returns one 384-dim vector per input."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, batch_size=32, show_progress_bar=False)
    return [v.tolist() for v in vectors]
'@

# ---------------------------------------------------------------
# 6. services/ingestion.py
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\services\ingestion.py" @'
"""Ingestion orchestration: upload registration + async processing pipeline.

upload_document(): called from the API layer. Hashes the file, checks for
an existing (user_id, content_hash) match (idempotency), persists via
StorageBackend, creates the Document row, and returns it. Does NOT extract/
embed — that happens in process_document(), run by the arq worker.

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
    storage_path = await storage.save(storage_key, data)

    document = Document(
        user_id=user_id,
        filename=filename,
        content_hash=content_hash,
        storage_path=storage_path,
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

    document.status = "processing"
    await session.commit()

    try:
        raw_bytes = await storage.load(document.storage_path)
        tmp_path = f"/tmp/{document.id}.pdf"
        with open(tmp_path, "wb") as f:
            f.write(raw_bytes)

        try:
            text = extract_text_from_pdf(tmp_path)
        finally:
            import os

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        pieces = chunk_text(text)
        if not pieces:
            raise ExtractionError("chunking produced zero chunks from extracted text")

        vectors = embed_texts([p.content for p in pieces])

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
    except Exception as exc:  # noqa: BLE001 — must not crash the worker loop
        document.status = "failed"
        document.status_reason = f"unexpected error: {exc}"[:512]
        await session.commit()
'@

# ---------------------------------------------------------------
# 7. api/routes/documents.py
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\api\routes\documents.py" @'
"""Document upload/list/get/delete endpoints. All queries user_id-scoped."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
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
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
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
        await arq_pool.enqueue_job("process_document", str(document.id))

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
    await session.delete(document)
    await session.commit()
    return DocumentDeleteResponse(id=document_id, deleted=True)
'@

# ---------------------------------------------------------------
# 8. api/deps.py — append storage + arq pool dependencies
# ---------------------------------------------------------------
$depsPath = "$be\app\api\deps.py"
$depsRaw = Get-Content $depsPath -Raw
if ($depsRaw -notmatch "get_storage") {
    $append = @'


def get_storage() -> "StorageBackend":
    from app.config import get_settings
    from app.storage.local import LocalStorage

    return LocalStorage(get_settings().storage_path)


async def get_arq_pool():
    from arq import create_pool
    from arq.connections import RedisSettings

    from app.config import get_settings

    settings = get_settings()
    return await create_pool(RedisSettings.from_dsn(settings.redis_url))
'@
    $depsRaw += $append
    # add StorageBackend import at top for typing
    $depsRaw = $depsRaw -replace "from app.services.auth import AuthService", "from app.services.auth import AuthService`nfrom app.storage.base import StorageBackend"
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $depsPath), $depsRaw, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[updated] $depsPath (+get_storage, +get_arq_pool)" -ForegroundColor Green
} else {
    Write-Host "[skip] deps.py already updated" -ForegroundColor Yellow
}

# ---------------------------------------------------------------
# 9. main.py — register documents router
# ---------------------------------------------------------------
$mainPath = "$be\app\main.py"
$mainRaw = Get-Content $mainPath -Raw
if ($mainRaw -notmatch "documents as document_routes") {
    $mainRaw = $mainRaw -replace "from app.api.routes import auth as auth_routes", "from app.api.routes import auth as auth_routes`nfrom app.api.routes import documents as document_routes"
    $mainRaw = $mainRaw -replace 'app.include_router\(auth_routes.router, prefix=settings.api_prefix\)', "app.include_router(auth_routes.router, prefix=settings.api_prefix)`n    app.include_router(document_routes.router, prefix=settings.api_prefix)"
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $mainPath), $mainRaw, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[updated] $mainPath (+documents router)" -ForegroundColor Green
} else {
    Write-Host "[skip] main.py already updated" -ForegroundColor Yellow
}

# ---------------------------------------------------------------
# 10. worker.py — register process_document task
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\app\worker_tasks\ingest.py" @'
"""arq task wrapper for document processing."""
from __future__ import annotations

import uuid
from typing import Any

from app.db.session import async_session_factory
from app.services.ingestion import process_document
from app.storage.local import LocalStorage
from app.config import get_settings


async def process_document_task(ctx: dict[str, Any], document_id: str) -> None:
    storage = LocalStorage(get_settings().storage_path)
    async with async_session_factory() as session:
        await process_document(
            session=session, storage=storage, document_id=uuid.UUID(document_id)
        )
'@

$workerPath = "$be\app\worker.py"
$workerRaw = Get-Content $workerPath -Raw
if ($workerRaw -notmatch "process_document_task") {
    $workerRaw = $workerRaw -replace "from app.config import get_settings", "from app.config import get_settings`nfrom app.worker_tasks.ingest import process_document_task"
    $workerRaw = $workerRaw -replace "functions = \[ping\]", "functions = [ping, process_document_task]"
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $workerPath), $workerRaw, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[updated] $workerPath (+process_document_task)" -ForegroundColor Green
} else {
    Write-Host "[skip] worker.py already updated" -ForegroundColor Yellow
}

# ---------------------------------------------------------------
# 11. Generate a real tiny PDF fixture (no manual sourcing needed)
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\tests\fixtures\generate_sample_pdf.py" @'
"""Run once to (re)generate tests/fixtures/sample.pdf using PyMuPDF."""
import fitz

doc = fitz.open()
page = doc.new_page()
page.insert_text(
    (72, 72),
    "DocSage test fixture.\n\n"
    "This is a small sample PDF used by the ingestion test suite. "
    "It contains enough text to produce at least one chunk after "
    "chunking and embedding, so the round-trip upload -> extract -> "
    "chunk -> embed -> indexed pipeline can be exercised end to end.",
)
doc.save("tests/fixtures/sample.pdf")
doc.close()
print("wrote tests/fixtures/sample.pdf")
'@

# ---------------------------------------------------------------
# 12. Tests
# ---------------------------------------------------------------
Write-Utf8NoBom "$be\tests\test_chunking.py" @'
from app.services.chunking import chunk_text


def test_chunk_text_empty_returns_empty_list() -> None:
    assert chunk_text("") == []


def test_chunk_text_single_chunk_when_short() -> None:
    text = " ".join(["word"] * 100)
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].token_count == 100


def test_chunk_text_overlap_boundaries() -> None:
    words = [f"w{i}" for i in range(1200)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert len(chunks) == 3
    assert chunks[0].token_count == 500
    # second chunk starts 450 words in (step = 500 - 50)
    assert chunks[1].content.split()[0] == "w450"


def test_chunk_text_rejects_invalid_overlap() -> None:
    import pytest

    with pytest.raises(ValueError):
        chunk_text("a b c", chunk_size=10, overlap=10)
'@

Write-Utf8NoBom "$be\tests\test_extraction.py" @'
import os

import pytest

from app.services.extraction import ExtractionError, extract_text_from_pdf

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")


def test_extract_text_from_valid_pdf() -> None:
    text = extract_text_from_pdf(FIXTURE)
    assert "DocSage test fixture" in text


def test_extract_text_missing_file_raises() -> None:
    with pytest.raises(ExtractionError):
        extract_text_from_pdf("/nonexistent/path.pdf")


def test_extract_text_corrupt_file_raises(tmp_path) -> None:
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"not a real pdf")
    with pytest.raises(ExtractionError):
        extract_text_from_pdf(str(bad))
'@

Write-Utf8NoBom "$be\tests\test_ingestion.py" @'
import os
import uuid

import pytest
from sqlalchemy import select

from app.models import Chunk, Document, User
from app.services.ingestion import process_document, upload_document
from app.storage.local import LocalStorage

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")


@pytest.fixture
async def test_user(db_session):
    user = User(email="ingest@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path)


@pytest.mark.asyncio
async def test_upload_is_idempotent_on_same_content(db_session, test_user, storage) -> None:
    data = open(FIXTURE, "rb").read()

    doc1, is_new1 = await upload_document(
        session=db_session, storage=storage, user_id=test_user.id, filename="a.pdf", data=data
    )
    doc2, is_new2 = await upload_document(
        session=db_session, storage=storage, user_id=test_user.id, filename="a-renamed.pdf", data=data
    )

    assert is_new1 is True
    assert is_new2 is False
    assert doc1.id == doc2.id


@pytest.mark.asyncio
async def test_process_document_full_roundtrip(db_session, test_user, storage) -> None:
    data = open(FIXTURE, "rb").read()
    document, _ = await upload_document(
        session=db_session, storage=storage, user_id=test_user.id, filename="a.pdf", data=data
    )

    await process_document(session=db_session, storage=storage, document_id=document.id)

    refreshed = await db_session.get(Document, document.id)
    assert refreshed.status == "indexed"
    assert refreshed.indexed_at is not None

    chunks = (
        await db_session.scalars(select(Chunk).where(Chunk.document_id == document.id))
    ).all()
    assert len(chunks) > 0
    assert all(len(c.embedding) == 384 for c in chunks)


@pytest.mark.asyncio
async def test_process_document_corrupt_file_sets_failed(db_session, test_user, storage) -> None:
    document = Document(
        user_id=test_user.id,
        filename="bad.pdf",
        content_hash="deadbeef",
        storage_path=await storage.save(f"{test_user.id}/bad.pdf", b"not a pdf"),
        status="uploaded",
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    await process_document(session=db_session, storage=storage, document_id=document.id)

    refreshed = await db_session.get(Document, document.id)
    assert refreshed.status == "failed"
    assert refreshed.status_reason is not None


@pytest.mark.asyncio
async def test_document_isolation_between_users(db_session, storage) -> None:
    user_a = User(email="a@example.com", hashed_password="x")
    user_b = User(email="b@example.com", hashed_password="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    data = open(FIXTURE, "rb").read()
    doc_a, _ = await upload_document(
        session=db_session, storage=storage, user_id=user_a.id, filename="a.pdf", data=data
    )

    result = await db_session.scalars(select(Document).where(Document.user_id == user_b.id))
    assert list(result) == []

    result_a = await db_session.scalars(select(Document).where(Document.user_id == user_a.id))
    assert [d.id for d in result_a] == [doc_a.id]
'@

# ---------------------------------------------------------------
# 13. Install deps, generate fixture, run tests
# ---------------------------------------------------------------
Set-Location $be
Write-Host "`n[installing dependencies]" -ForegroundColor Cyan
pip install -e ".[dev]"

Write-Host "`n[generating PDF fixture]" -ForegroundColor Cyan
python tests\fixtures\generate_sample_pdf.py

Write-Host "`n[running Phase 2 tests]" -ForegroundColor Cyan
pytest tests\test_chunking.py tests\test_extraction.py tests\test_ingestion.py -v

Set-Location ..
Write-Host "`n[done] Review test output above. If green: git add . && git commit." -ForegroundColor Cyan
