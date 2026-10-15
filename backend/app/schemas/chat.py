"""Pydantic schemas for chat endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: uuid.UUID | None = None


class SourceRef(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    score: float


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    sources: list[SourceRef]
    trace: ChatTrace | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime

class ChatTrace(BaseModel):
    vector_ms: float
    bm25_ms: float
    fusion_ms: float
    rerank_ms: float
    generation_ms: float
    vector_count: int
    bm25_count: int
    fused_count: int