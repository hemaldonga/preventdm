"""Pydantic schemas for the PreventDM ML inference service data contract."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field


class ValidatedFeatures(BaseModel):
    """Engineered feature vector forwarded from the rust_service."""

    bmi: float
    age_years: Annotated[int, Field(gt=0)]
    sex_encoded: int
    ethnicity_encoded: int
    hba1c_percent: float
    fasting_glucose_mg_dl: float
    waist_circumference_cm: float
    systolic_bp_mmhg: int
    physical_activity_minutes_per_week: int
    smoking_current: bool
    family_history_diabetes: bool


class PredictRequest(BaseModel):
    """Request body for POST /predict."""

    features: ValidatedFeatures


class ShapValues(BaseModel):
    """Per-feature SHAP attribution values."""

    bmi: float
    age_years: float
    hba1c_percent: float
    fasting_glucose_mg_dl: float
    waist_circumference_cm: float
    systolic_bp_mmhg: float
    physical_activity_minutes_per_week: float
    smoking_current: float
    family_history_diabetes: float
    sex_encoded: float
    ethnicity_encoded: float


class PredictResponse(BaseModel):
    """Response body for POST /predict."""

    probability: Annotated[float, Field(ge=0.0, le=1.0)]
    confidence_lower: Annotated[float, Field(ge=0.0, le=1.0)]
    confidence_upper: Annotated[float, Field(ge=0.0, le=1.0)]
    shap_values: ShapValues
