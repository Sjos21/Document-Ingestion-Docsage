"""Dependency health checks for /health/ready."""
from __future__ import annotations

import httpx
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings


async def check_postgres(session: AsyncSession) -> tuple[str, str | None]:
    try:
        await session.execute(text("SELECT 1"))
        return "ok", None
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)[:200]


async def check_redis() -> tuple[str, str | None]:
    settings = get_settings()
    try:
        client = Redis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        return "ok", None
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)[:200]


async def check_ollama() -> tuple[str, str | None]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
        return "ok", None
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)[:200]