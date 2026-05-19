"""Tests for POST /assess and GET /assess/{id} under normal conditions."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient, RiskAssessment


async def test_post_assess_returns_200(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    assert response.status_code == 200


async def test_post_assess_response_has_assessment_id(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    assert response.json()["assessment_id"]


async def test_post_assess_echoes_patient_id(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    assert response.json()["patient_external_id"] == sample_payload["patient_external_id"]


async def test_post_assess_has_timestamp(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    assert response.json()["assessment_timestamp_utc"]


async def test_post_assess_has_validated_features(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    assert "validated_features" in response.json()


async def test_post_assess_has_clinical_scores(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    scores = response.json()["clinical_scores"]
    assert "findrisc" in scores
    assert "ada" in scores
    assert "cambridge" in scores


async def test_post_assess_has_ml_prediction(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    prob = response.json()["ml_prediction"]["probability"]
    assert 0.0 <= prob <= 1.0


async def test_post_assess_persists_to_database(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    response = await app_client.post("/assess", json=sample_payload)
    assert response.status_code == 200

    result = await db_session.execute(
        select(RiskAssessment)
        .join(Patient, RiskAssessment.patient_id == Patient.id)
        .where(Patient.external_id == sample_payload["patient_external_id"])
    )
    assessment = result.scalar_one_or_none()
    assert assessment is not None
    assert assessment.probability == pytest.approx(0.34)


async def test_get_assess_returns_persisted_assessment(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
) -> None:
    post_resp = await app_client.post("/assess", json=sample_payload)
    assert post_resp.status_code == 200
    post_body = post_resp.json()
    assessment_id = post_body["assessment_id"]

    get_resp = await app_client.get(f"/assess/{assessment_id}")
    assert get_resp.status_code == 200
    get_body = get_resp.json()

    assert get_body["patient_external_id"] == post_body["patient_external_id"]
    assert get_body["assessment_timestamp_utc"] == post_body["assessment_timestamp_utc"]
    assert get_body["ml_prediction"]["probability"] == pytest.approx(
        post_body["ml_prediction"]["probability"]
    )


async def test_get_assess_patient_deduplication(
    app_client: httpx.AsyncClient,
    mock_rust_service: AsyncMock,
    mock_ml_service: AsyncMock,
    sample_payload: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    await app_client.post("/assess", json=sample_payload)
    await app_client.post("/assess", json=sample_payload)

    result = await db_session.execute(
        select(Patient).where(Patient.external_id == sample_payload["patient_external_id"])
    )
    patients = result.scalars().all()
    assert len(patients) == 1
