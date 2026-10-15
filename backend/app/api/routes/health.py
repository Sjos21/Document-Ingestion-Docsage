"""Liveness/readiness endpoints for orchestration and monitoring."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.health import check_ollama, check_postgres, check_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def ready(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    pg_status, pg_err = await check_postgres(session)
    redis_status, redis_err = await check_redis()
    ollama_status, ollama_err = await check_ollama()

    checks = {
        "postgres": {"status": pg_status, "error": pg_err},
        "redis": {"status": redis_status, "error": redis_err},
        "ollama": {"status": ollama_status, "error": ollama_err},
    }
    overall = "ready" if all(c["status"] == "ok" for c in checks.values()) else "not_ready"
    if overall != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": overall, "checks": checks}