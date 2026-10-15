"""Redis fixed-window rate limiting.

Fixed-window (not sliding/token-bucket): simplest correct approach at this
scale, one INCR + one EXPIRE per request. Edge case: allows up to 2x limit
across a window boundary -- acceptable tradeoff for a single-user-scale app;
revisit with a sliding window only if abuse patterns actually appear.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.config import get_settings

_redis_client: Redis | None = None


def get_rate_limit_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(get_settings().redis_url)
    return _redis_client


async def enforce_rate_limit(*, user_id: uuid.UUID, action: str, limit: int, window_seconds: int) -> None:
    client = get_rate_limit_redis()
    key = f"ratelimit:{action}:{user_id}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {action}: {limit} per {window_seconds}s",
        )