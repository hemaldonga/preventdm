"""FastAPI application factory for the PreventDM ML inference service."""

from __future__ import annotations

import importlib.metadata
import json
import logging
import sys

import fastapi

from app.config import get_settings
from app.routers import health, predict

_LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class _JsonFormatter(logging.Formatter):
    """Serialize log records as single-line JSON for structured stdout output."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON string representing the log record."""
        payload: dict[str, object] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        return json.dumps(payload)


def _configure_logging(log_level: str) -> None:
    """Attach a JSON stream handler to the root logger at the specified level."""
    handler: logging.Handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.setLevel(_LOG_LEVELS.get(log_level.upper(), logging.INFO))
    root.handlers = [handler]


def create_app() -> fastapi.FastAPI:
    """Construct the FastAPI application with all routers registered."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    try:
        pkg_version = importlib.metadata.version("preventdm-ml-service")
    except importlib.metadata.PackageNotFoundError:
        pkg_version = "0.0.0"

    application = fastapi.FastAPI(
        title=settings.app_name,
        version=pkg_version,
    )
    application.include_router(health.router)
    application.include_router(predict.router)

    return application


app = create_app()
