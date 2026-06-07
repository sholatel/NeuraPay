from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.error_handlers import (
    file_size_exceeded_handler,
    general_exception_handler,
    openai_api_error_handler,
    transcription_error_handler,
    unsupported_file_type_handler,
    validation_exception_handler,
)
from app.core.exceptions import (
    FileSizeExceededError,
    OpenAIAPIError,
    TranscriptionError,
    UnsupportedFileTypeError,
)
from app.agents.base import setup_agents
from app.core.logging import get_logger, setup_logging
from app.middleware.request_id import RequestIDMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    settings = get_settings()

    # Configure the OpenAI Agents SDK (LiteLLM proxy or direct OpenAI).
    # Must run before the first request — Agent objects are lightweight and
    # created at import time, but Runner.run() picks up the global client here.
    setup_agents(settings)

    logger.info(
        "service.startup",
        name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        host=settings.HOST,
        port=settings.PORT,
    )
    yield
    logger.info("service.shutdown", name=settings.APP_NAME)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=(
            "AI Orchestration Layer for the fintech platform. "
            "Handles voice processing, agent orchestration, and MCP tool integration. "
            "Does NOT access banking databases directly — all financial operations "
            "are proxied through the NestJS banking backend."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware (outermost first) ──────────────────────────────────────────
    # CORS must be outermost so preflight OPTIONS requests are handled before
    # any other middleware or route logic runs.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestIDMiddleware)

    # ── Exception handlers ───────────────────────────────────────────────────
    app.add_exception_handler(UnsupportedFileTypeError, unsupported_file_type_handler)  # type: ignore[arg-type]
    app.add_exception_handler(FileSizeExceededError, file_size_exceeded_handler)  # type: ignore[arg-type]
    app.add_exception_handler(TranscriptionError, transcription_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(OpenAIAPIError, openai_api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, general_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)                               # GET /health
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)  # /api/v1/...

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
