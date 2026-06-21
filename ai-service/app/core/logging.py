import logging
import sys
from pathlib import Path
from typing import Any

import structlog

from app.core.config import get_settings

# ai-service/server.log — always written regardless of terminal behavior
_LOG_FILE = Path(__file__).resolve().parents[2] / "server.log"


def setup_logging() -> None:
    """Configure structlog with two handlers: colored stderr + clean JSON file."""
    settings = get_settings()

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ExtraAdder(),
    ]

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Terminal handler — pretty colored output in debug, JSON in production
    if settings.DEBUG:
        console_renderer = structlog.dev.ConsoleRenderer()
    else:
        console_renderer = structlog.processors.JSONRenderer()  # type: ignore[assignment]

    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=console_renderer,
        foreign_pre_chain=shared_processors,
    )
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(console_formatter)

    # File handler — always clean JSON (no ANSI escape codes)
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(file_formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root.handlers.clear()
    root.addHandler(stderr_handler)
    root.addHandler(file_handler)

    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
