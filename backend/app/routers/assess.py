"""Assessment orchestration router — coordinates rust_service and ml_service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.clients import UpstreamServiceError, call_ml_service, call_rust_service
from app.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    ClinicalScores,
    MLPrediction,
    ValidatedFeatures,
)

router = APIRouter()


@router.post("/assess", response_model=AssessmentResponse)
async def assess(request: AssessmentRequest) -> AssessmentResponse:
    """Orchestrate a full risk assessment via rust_service and ml_service."""
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
    timestamp = datetime.now(UTC).isoformat()

    return AssessmentResponse(
        patient_external_id=request.patient_external_id,
        assessment_timestamp_utc=timestamp,
        validated_features=validated_features,
        clinical_scores=clinical_scores,
        ml_prediction=ml_prediction,
    )
