"""Minimal arq worker entrypoint (Phase 0 scaffold)."""

from typing import Any

from arq.connections import RedisSettings

from app.config import get_settings
from app.worker_tasks.ingest import process_document_task


async def startup(ctx: dict[str, Any]) -> None:
    ctx["settings"] = get_settings()


async def shutdown(ctx: dict[str, Any]) -> None:
    pass


async def ping(ctx: dict[str, Any]) -> str:
    return "pong"


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    functions = [ping, process_document_task]
    cron_jobs: list[Any] = []
