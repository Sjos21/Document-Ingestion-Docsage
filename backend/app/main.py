from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth as auth_routes
from app.api.routes import documents as document_routes
from app.api.routes import search as search_routes
from app.api.routes import chat as chat_routes
from app.api.routes import health as health_routes
from app.api.routes import metrics as metrics_routes
from app.api.routes import analytics as analytics_routes
from app.config import get_settings
from app.logging import configure_logging, get_logger
from app.middleware import RequestIdMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(json_output=settings.log_json, log_level=settings.log_level)
    logger.info("application_starting", app_name=settings.app_name)
    yield
    logger.info("application_stopping")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_routes.router, prefix=settings.api_prefix)
    app.include_router(document_routes.router, prefix=settings.api_prefix)
    app.include_router(search_routes.router, prefix=settings.api_prefix)
    app.include_router(chat_routes.router, prefix=settings.api_prefix)
    app.include_router(health_routes.router, prefix=settings.api_prefix)
    app.include_router(metrics_routes.router, prefix=settings.api_prefix)
    app.include_router(analytics_routes.router, prefix=settings.api_prefix)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(f"{settings.api_prefix}/health")
    async def api_health() -> dict[str, str]:
        return {"status": "ok", "service": "api"}

    return app


app = create_app()
