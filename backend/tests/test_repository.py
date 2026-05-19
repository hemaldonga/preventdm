"""Tests for AssessmentRepository in isolation (no HTTP layer)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClinicalScore, Patient, RiskAssessment
from app.repositories import AssessmentRepository
from app.schemas import AssessmentRequest

_PATIENT_ID = "TEST-REPO-001"

_VALIDATED_FEATURES: dict[str, Any] = {
    "bmi": 28.4,
    "age_years": 45,
    "sex_encoded": 0,
    "ethnicity_encoded": 0,
    "hba1c_percent": 5.9,
    "fasting_glucose_mg_dl": 102.0,
    "waist_circumference_cm": 92.0,
    "systolic_bp_mmhg": 128,
    "physical_activity_minutes_per_week": 90,
    "smoking_current": False,
    "family_history_diabetes": True,
}

_CLINICAL_SCORES: dict[str, Any] = {
    "findrisc": {"score": 14, "risk_category": "moderate"},
    "ada": {"score": 6, "risk_category": "high"},
    "cambridge": {"score": 0.27, "risk_category": "moderate"},
}

_ML_PREDICTION: dict[str, Any] = {
    "probability": 0.34,
    "confidence_lower": 0.28,
    "confidence_upper": 0.41,
    "shap_values": {
        "bmi": 0.12,
        "age_years": 0.08,
        "hba1c_percent": 0.15,
        "fasting_glucose_mg_dl": 0.10,
        "waist_circumference_cm": 0.06,
        "systolic_bp_mmhg": 0.04,
        "physical_activity_minutes_per_week": -0.05,
        "smoking_current": 0.01,
        "family_history_diabetes": 0.09,
        "sex_encoded": -0.02,
        "ethnicity_encoded": 0.00,
    },
}


def _make_request(patient_id: str = _PATIENT_ID) -> AssessmentRequest:
    return AssessmentRequest(
        patient_external_id=patient_id,
        demographics={"age_years": 45, "sex": "male", "ethnicity": "white"},  # type: ignore[arg-type]
        anthropometrics={"height_cm": 175.0, "weight_kg": 87.0, "waist_circumference_cm": 92.0},  # type: ignore[arg-type]
        clinical={  # type: ignore[arg-type]
            "hba1c_percent": 5.9,
            "fasting_glucose_mg_dl": 102.0,
            "systolic_bp_mmhg": 128,
            "diastolic_bp_mmhg": 82,
            "total_cholesterol_mg_dl": 195.0,
            "hdl_cholesterol_mg_dl": 52.0,
        },
        lifestyle={  # type: ignore[arg-type]
            "physical_activity_minutes_per_week": 90,
            "smoking_status": "former",
            "family_history_diabetes": True,
        },
    )


async def _create(db: AsyncSession, patient_id: str = _PATIENT_ID) -> RiskAssessment:
    repo = AssessmentRepository()
    return await repo.create_assessment_with_scores(
        db,
        patient_external_id=patient_id,
        request=_make_request(patient_id),
        validated_features=_VALIDATED_FEATURES,
        clinical_scores=_CLINICAL_SCORES,
        ml_prediction=_ML_PREDICTION,
    )


async def test_create_assessment_creates_patient(db_session: AsyncSession) -> None:
    await _create(db_session)
    result = await db_session.execute(select(Patient).where(Patient.external_id == _PATIENT_ID))
    assert result.scalar_one_or_none() is not None


async def test_create_assessment_creates_risk_assessment(db_session: AsyncSession) -> None:
    assessment = await _create(db_session)
    result = await db_session.execute(
        select(RiskAssessment).where(RiskAssessment.id == assessment.id)
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.probability == pytest.approx(0.34)


async def test_create_assessment_creates_three_clinical_scores(db_session: AsyncSession) -> None:
    assessment = await _create(db_session)
    result = await db_session.execute(
        select(ClinicalScore).where(ClinicalScore.assessment_id == assessment.id)
    )
    scores = result.scalars().all()
    score_types = {s.score_type for s in scores}
    assert len(scores) == 3
    assert score_types == {"findrisc", "ada", "cambridge"}


async def test_create_assessment_patient_deduplication(db_session: AsyncSession) -> None:
    await _create(db_session)
    await _create(db_session)
    result = await db_session.execute(
        select(func.count()).select_from(Patient).where(Patient.external_id == _PATIENT_ID)
    )
    count = result.scalar_one()
    assert count == 1


async def test_get_assessment_by_id_returns_correct_assessment(db_session: AsyncSession) -> None:
    created = await _create(db_session)
    repo = AssessmentRepository()
    fetched = await repo.get_assessment_by_id(db_session, created.id)
    assert fetched is not None
    assert fetched.patient.external_id == _PATIENT_ID
    assert fetched.probability == pytest.approx(0.34)


async def test_get_assessment_by_id_returns_none_for_missing(db_session: AsyncSession) -> None:
    repo = AssessmentRepository()
    result = await repo.get_assessment_by_id(db_session, uuid.uuid4())
    assert result is None
