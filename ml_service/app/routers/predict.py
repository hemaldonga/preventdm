"""Prediction router — returns hardcoded mock ML inference results."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import PredictRequest, PredictResponse, ShapValues

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Accept a feature vector and return a hardcoded mock diabetes risk prediction."""
    # Input is validated against PredictRequest; real inference deferred to a later phase.
    _ = request
    return PredictResponse(
        probability=0.34,
        confidence_lower=0.28,
        confidence_upper=0.41,
        shap_values=ShapValues(
            bmi=0.08,
            age_years=0.05,
            hba1c_percent=0.12,
            fasting_glucose_mg_dl=0.09,
            waist_circumference_cm=0.04,
            systolic_bp_mmhg=0.02,
            physical_activity_minutes_per_week=-0.03,
            smoking_current=0.00,
            family_history_diabetes=0.07,
            sex_encoded=-0.01,
            ethnicity_encoded=0.01,
        ),
    )
