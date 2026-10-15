"""Semantic search endpoint. Scoped to the current user's indexed documents."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db_session
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
import time

from app.services.audit import record_event
from app.services.rate_limit import enforce_rate_limit
from app.services.retrieval import search_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    current_user: CurrentUser,
    payload: SearchRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SearchResponse:
    started_at = time.perf_counter()
    hits = await search_chunks(
        session=session,
        user_id=current_user.id,
        query=payload.query,
        top_k=payload.top_k,
    )
    await record_event(
        session,
        event_type="SEARCH_EXECUTED",
        user_id=current_user.id,
        duration_ms=(time.perf_counter() - started_at) * 1000,
        status="zero_results" if not hits else "success",
        metadata={"query_length": len(payload.query), "result_count": len(hits)},
    )
    await session.commit()
    return SearchResponse(
        query=payload.query,
        results=[
            SearchResultItem(
                chunk_id=h.chunk_id,
                document_id=h.document_id,
                filename=h.filename,
                content=h.content,
                score=h.score,
            )
            for h in hits
        ],
    )