"""Tests for error conditions on POST /assess and GET /assess/{id}."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx

from app.clients import UpstreamServiceError


async def test_post_assess_empty_body_returns_422(app_client: httpx.AsyncClient) -> None:
    response = await app_client.post("/assess", json={})
    assert response.status_code == 422


async def test_post_assess_missing_demographics_returns_422(
    app_client: httpx.AsyncClient,
    sample_payload: dict[str, Any],
) -> None:
    payload = deepcopy(sample_payload)
    del payload["demographics"]
    response = await app_client.post("/assess", json=payload)
    assert response.status_code == 422


async def test_post_assess_negative_age_returns_422(
    app_client: httpx.AsyncClient,
    sample_payload: dict[str, Any],
) -> None:
    payload = deepcopy(sample_payload)
    payload["demographics"]["age_years"] = -1
    response = await app_client.post("/assess", json=payload)
    assert response.status_code == 422


async def test_post_assess_invalid_sex_returns_422(
    app_client: httpx.AsyncClient,
    sample_payload: dict[str, Any],
) -> None:
    payload = deepcopy(sample_payload)
    payload["demographics"]["sex"] = "unknown"
    response = await app_client.post("/assess", json=payload)
    assert response.status_code == 422


async def test_post_assess_upstream_error_returns_502(
    app_client: httpx.AsyncClient,
    sample_payload: dict[str, Any],
) -> None:
    err = UpstreamServiceError("rust_service", 0, "connection refused")
    with patch(
        "app.routers.assess.call_rust_service",
        new=AsyncMock(side_effect=err),
    ):
        response = await app_client.post("/assess", json=sample_payload)
    assert response.status_code == 502


async def test_get_assess_nil_uuid_returns_404(app_client: httpx.AsyncClient) -> None:
    response = await app_client.get("/assess/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_get_assess_malformed_uuid_returns_422(app_client: httpx.AsyncClient) -> None:
    response = await app_client.get("/assess/not-a-uuid")
    assert response.status_code == 422
