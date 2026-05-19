"""Tests for GET /health."""

from __future__ import annotations

import httpx

from app.config import get_settings


async def test_health_returns_200(app_client: httpx.AsyncClient) -> None:
    response = await app_client.get("/health")
    assert response.status_code == 200


async def test_health_response_schema(app_client: httpx.AsyncClient) -> None:
    settings = get_settings()
    response = await app_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == settings.app_name
    assert body["environment"] == settings.app_env
    assert body["version"]
