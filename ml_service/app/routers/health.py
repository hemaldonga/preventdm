"""Health check router for liveness verification."""

from __future__ import annotations

import importlib.metadata
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Response schema for the /health endpoint."""

    status: Literal["ok"]
    service: str
    environment: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return a liveness signal with service identity and runtime metadata."""
    settings = get_settings()
    try:
        pkg_version = importlib.metadata.version("preventdm-ml-service")
    except importlib.metadata.PackageNotFoundError:
        pkg_version = "0.0.0"
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=pkg_version,
    )
