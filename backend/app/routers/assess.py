"""Assessment orchestration router — coordinates rust_service and ml_service."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import UpstreamServiceError, call_ml_service, call_rust_service
from app.database import get_db
from app.repositories import AssessmentRepository
from app.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    ClinicalScoreResult,
    ClinicalScores,
    GetAssessmentResponse,
    MLPrediction,
    ShapValues,
    ValidatedFeatures,
)

router = APIRouter()


@router.post("/assess", response_model=AssessmentResponse)
async def assess(
    request: AssessmentRequest,
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """Orchestrate a full risk assessment via rust_service and ml_service, then persist it."""
    payload: dict[str, Any] = request.model_dump()

    try:
        score_result = await call_rust_service(payload)
    except UpstreamServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"rust_service error ({exc.status_code}): {exc.detail}",
        ) from exc

    validated_features = ValidatedFeatures.model_validate(score_result["validated_features"])
    clinical_scores = ClinicalScores.model_validate(score_result["clinical_scores"])

    predict_payload: dict[str, Any] = {"features": score_result["validated_features"]}

    try:
        predict_result = await call_ml_service(predict_payload)
    except UpstreamServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ml_service error ({exc.status_code}): {exc.detail}",
        ) from exc

    ml_prediction = MLPrediction.model_validate(predict_result)

    repo = AssessmentRepository()
    assessment = await repo.create_assessment_with_scores(
        db,
        patient_external_id=request.patient_external_id,
        request=request,
        validated_features=dict(score_result["validated_features"]),
        clinical_scores=dict(score_result["clinical_scores"]),
        ml_prediction=predict_result,
    )

    return AssessmentResponse(
        assessment_id=assessment.id,
        patient_external_id=request.patient_external_id,
        assessment_timestamp_utc=assessment.assessment_timestamp_utc.isoformat(),
        validated_features=validated_features,
        clinical_scores=clinical_scores,
        ml_prediction=ml_prediction,
    )


@router.get("/assess/{assessment_id}", response_model=GetAssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> GetAssessmentResponse:
    """Return a persisted assessment by ID; 404 if not found."""
    repo = AssessmentRepository()
    assessment = await repo.get_assessment_by_id(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    cs_map = {s.score_type: s for s in assessment.clinical_scores}
    return GetAssessmentResponse(
        assessment_id=assessment.id,
        patient_external_id=assessment.patient.external_id,
        assessment_timestamp_utc=assessment.assessment_timestamp_utc.isoformat(),
        validated_features=ValidatedFeatures.model_validate(assessment.features),
        clinical_scores=ClinicalScores(
            findrisc=ClinicalScoreResult(
                score=cs_map["findrisc"].score_value,
                risk_category=cs_map["findrisc"].risk_category,
            ),
            ada=ClinicalScoreResult(
                score=cs_map["ada"].score_value,
                risk_category=cs_map["ada"].risk_category,
            ),
            cambridge=ClinicalScoreResult(
                score=cs_map["cambridge"].score_value,
                risk_category=cs_map["cambridge"].risk_category,
            ),
        ),
        ml_prediction=MLPrediction(
            probability=assessment.probability,
            confidence_lower=assessment.confidence_lower,
            confidence_upper=assessment.confidence_upper,
            shap_values=ShapValues.model_validate(assessment.shap_values),
        ),
    )
