"""Persistence layer for the assessment domain."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.clinical_score import ClinicalScore
from app.models.patient import Patient
from app.models.risk_assessment import RiskAssessment
from app.schemas import AssessmentRequest


class AssessmentRepository:
    async def create_assessment_with_scores(
        self,
        db: AsyncSession,
        *,
        patient_external_id: str,
        request: AssessmentRequest,
        validated_features: dict[str, Any],
        clinical_scores: dict[str, Any],
        ml_prediction: dict[str, Any],
    ) -> RiskAssessment:
        """Persist a complete assessment in a single transaction.

        Looks up the patient by external_id and creates one if not found.
        Creates one RiskAssessment row and three ClinicalScore rows.
        Rolls back the entire transaction if any insert fails.
        """
        try:
            result = await db.execute(
                select(Patient).where(Patient.external_id == patient_external_id)
            )
            patient: Patient | None = result.scalar_one_or_none()

            if patient is None:
                patient = Patient(
                    external_id=patient_external_id,
                    dob=_compute_dob(request.demographics.age_years),
                    sex=request.demographics.sex,
                    ethnicity=request.demographics.ethnicity,
                    postal_code=None,
                )
                db.add(patient)
                await db.flush()

            assessment = RiskAssessment(
                patient_id=patient.id,
                assessment_timestamp_utc=datetime.now(UTC),
                features=validated_features,
                probability=float(ml_prediction["probability"]),
                confidence_lower=float(ml_prediction["confidence_lower"]),
                confidence_upper=float(ml_prediction["confidence_upper"]),
                shap_values=ml_prediction["shap_values"],
            )
            db.add(assessment)
            await db.flush()

            for score_type in ("findrisc", "ada", "cambridge"):
                score_data: dict[str, Any] = clinical_scores[score_type]
                db.add(
                    ClinicalScore(
                        assessment_id=assessment.id,
                        score_type=score_type,
                        score_value=float(score_data["score"]),
                        risk_category=str(score_data["risk_category"]),
                    )
                )

            assessment_id = assessment.id
            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return await self._load_with_relationships(db, assessment_id)

    async def get_assessment_by_id(
        self, db: AsyncSession, assessment_id: uuid.UUID
    ) -> RiskAssessment | None:
        """Return a RiskAssessment with patient and clinical_scores eagerly loaded."""
        result = await db.execute(
            select(RiskAssessment)
            .options(
                selectinload(RiskAssessment.patient),
                selectinload(RiskAssessment.clinical_scores),
            )
            .where(RiskAssessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def _load_with_relationships(
        self, db: AsyncSession, assessment_id: uuid.UUID
    ) -> RiskAssessment:
        result = await db.execute(
            select(RiskAssessment)
            .options(
                selectinload(RiskAssessment.patient),
                selectinload(RiskAssessment.clinical_scores),
            )
            .where(RiskAssessment.id == assessment_id)
        )
        return result.scalar_one()


def _compute_dob(age_years: int) -> date:
    """Derive a placeholder DOB from age in years.

    This is an approximation used until the API receives actual DOBs (a later phase).
    The date is set to today's month/day in the birth year, with Feb-29 clamped to Feb-28.
    """
    today = date.today()
    try:
        return today.replace(year=today.year - age_years)
    except ValueError:
        return today.replace(year=today.year - age_years, day=today.day - 1)
