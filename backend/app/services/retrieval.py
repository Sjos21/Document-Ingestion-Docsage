"""Hybrid semantic search: vector + BM25 fused via RRF, then cross-encoder
reranked, over a user's indexed document chunks.

Pipeline (see architecture.md):
    vector candidates (pgvector cosine) ─┐
    BM25 candidates (Postgres FTS)       ─┼─> RRF fusion -> top ~20-30
                                                  -> cross-encoder rerank -> top_k

Requires real Postgres+pgvector; cannot run against the SQLite test DB
(see tests/test_retrieval.py for the dedicated Postgres-backed fixture).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Document
from app.services.embedding import embed_texts
from app.services.fusion import reciprocal_rank_fusion, top_n_by_score
from app.services.reranking import rerank

FUSION_CANDIDATE_COUNT = 25


@dataclass
class SearchHit:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    content: str
    score: float


async def _vector_candidates(
    session: AsyncSession, user_id: uuid.UUID, query_vector: list[float], limit: int
) -> list[uuid.UUID]:
    distance = Chunk.embedding.cosine_distance(query_vector)
    stmt = (
        select(Chunk.id)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.user_id == user_id, Document.status == "indexed")
        .order_by(distance)
        .limit(limit)
    )
    return list((await session.scalars(stmt)).all())


async def _bm25_candidates(
    session: AsyncSession, user_id: uuid.UUID, query: str, limit: int
) -> list[uuid.UUID]:
    stmt = (
        select(Chunk.id)
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.user_id == user_id,
            Document.status == "indexed",
            Chunk.tsv.op("@@")(func.plainto_tsquery("english", query)),
        )
        .order_by(func.ts_rank(Chunk.tsv, func.plainto_tsquery("english", query)).desc())
        .limit(limit)
    )
    return list((await session.scalars(stmt)).all())


async def search_chunks(
    *, session: AsyncSession, user_id: uuid.UUID, query: str, top_k: int = 5
) -> list[SearchHit]:
    """Hybrid search: vector + BM25 -> RRF fusion -> cross-encoder rerank -> top_k."""
    query_vector = embed_texts([query])[0]

    vector_ids = await _vector_candidates(session, user_id, query_vector, FUSION_CANDIDATE_COUNT)
    bm25_ids = await _bm25_candidates(session, user_id, query, FUSION_CANDIDATE_COUNT)

    if not vector_ids and not bm25_ids:
        return []

    fused_scores = reciprocal_rank_fusion([vector_ids, bm25_ids])
    fused_ids = top_n_by_score(fused_scores, FUSION_CANDIDATE_COUNT)

    rows = (
        await session.execute(
            select(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .where(Chunk.id.in_(fused_ids))
        )
    ).all()
    by_id = {chunk.id: (chunk, filename) for chunk, filename in rows}
    ordered = [by_id[cid] for cid in fused_ids if cid in by_id]

    if not ordered:
        return []

    rerank_scores = rerank(query, [chunk.content for chunk, _ in ordered])
    scored = list(zip(ordered, rerank_scores, strict=True))
    scored.sort(key=lambda item: item[1], reverse=True)

    return [
        SearchHit(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=filename,
            content=chunk.content,
            score=score,
        )
        for (chunk, filename), score in scored[:top_k]
    ]

@dataclass
class SearchTrace:
    vector_ms: float
    bm25_ms: float
    fusion_ms: float
    rerank_ms: float
    vector_count: int
    bm25_count: int
    fused_count: int


async def search_chunks_traced(
    *, session: AsyncSession, user_id: uuid.UUID, query: str, top_k: int = 5
) -> tuple[list[SearchHit], SearchTrace]:
    """Same pipeline as search_chunks, with per-stage timings for the
    frontend transparency panel."""
    import time

    t0 = time.perf_counter()
    query_vector = embed_texts([query])[0]
    vector_ids = await _vector_candidates(session, user_id, query_vector, FUSION_CANDIDATE_COUNT)
    t1 = time.perf_counter()

    bm25_ids = await _bm25_candidates(session, user_id, query, FUSION_CANDIDATE_COUNT)
    t2 = time.perf_counter()

    if not vector_ids and not bm25_ids:
        return [], SearchTrace((t1 - t0) * 1000, (t2 - t1) * 1000, 0, 0, len(vector_ids), len(bm25_ids), 0)

    fused_scores = reciprocal_rank_fusion([vector_ids, bm25_ids])
    fused_ids = top_n_by_score(fused_scores, FUSION_CANDIDATE_COUNT)
    t3 = time.perf_counter()

    rows = (
        await session.execute(
            select(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .where(Chunk.id.in_(fused_ids))
        )
    ).all()
    by_id = {chunk.id: (chunk, filename) for chunk, filename in rows}
    ordered = [by_id[cid] for cid in fused_ids if cid in by_id]

    if not ordered:
        return [], SearchTrace((t1-t0)*1000, (t2-t1)*1000, (t3-t2)*1000, 0, len(vector_ids), len(bm25_ids), 0)

    rerank_scores = rerank(query, [chunk.content for chunk, _ in ordered])
    t4 = time.perf_counter()
    scored = list(zip(ordered, rerank_scores, strict=True))
    scored.sort(key=lambda item: item[1], reverse=True)

    hits = [
        SearchHit(chunk_id=c.id, document_id=c.document_id, filename=f, content=c.content, score=s)
        for (c, f), s in scored[:top_k]
    ]
    trace = SearchTrace(
        vector_ms=(t1-t0)*1000, bm25_ms=(t2-t1)*1000, fusion_ms=(t3-t2)*1000, rerank_ms=(t4-t3)*1000,
        vector_count=len(vector_ids), bm25_count=len(bm25_ids), fused_count=len(ordered),
    )
    return hits, trace
