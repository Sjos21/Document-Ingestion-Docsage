"""Pydantic schemas for document ingestion endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    extracting = "extracting"
    chunking = "chunking"
    embedding = "embedding"
    indexing = "indexing"
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