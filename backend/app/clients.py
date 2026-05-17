"""Async HTTP clients for upstream service calls."""

from __future__ import annotations

import functools
from typing import Any

import httpx

from app.config import get_settings


class UpstreamServiceError(Exception):
    """Raised when an upstream service is unreachable or returns a non-2xx response."""

    def __init__(self, service: str, status_code: int, detail: str) -> None:
        self.service = service
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{service} error {status_code}: {detail}")


@functools.lru_cache
def get_http_client() -> httpx.AsyncClient:
    """Return the shared AsyncClient instance with a 10-second timeout."""
    return httpx.AsyncClient(timeout=10.0)


async def call_rust_service(payload: dict[str, Any]) -> dict[str, Any]:
    """POST payload to rust_service /score and return the parsed JSON response."""
    settings = get_settings()
    client = get_http_client()
    url = f"{settings.rust_service_url}/score"
    try:
        response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise UpstreamServiceError(
            service="rust_service",
            status_code=0,
            detail=str(exc),
        ) from exc
    if response.status_code >= 300:
        raise UpstreamServiceError(
            service="rust_service",
            status_code=response.status_code,
            detail=response.text,
        )
    result: dict[str, Any] = response.json()
    return result


async def call_ml_service(payload: dict[str, Any]) -> dict[str, Any]:
    """POST payload to ml_service /predict and return the parsed JSON response."""
    settings = get_settings()
    client = get_http_client()
    url = f"{settings.ml_service_url}/predict"
    try:
        response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise UpstreamServiceError(
            service="ml_service",
            status_code=0,
            detail=str(exc),
        ) from exc
    if response.status_code >= 300:
        raise UpstreamServiceError(
            service="ml_service",
            status_code=response.status_code,
            detail=response.text,
        )
    result: dict[str, Any] = response.json()
    return result
