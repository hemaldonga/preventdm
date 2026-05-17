"""Pydantic schemas for the PreventDM assessment pipeline data contract."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Demographics(BaseModel):
    """Patient demographic information."""

    age_years: Annotated[int, Field(gt=0)]
    sex: Literal["male", "female", "other"]
    ethnicity: Literal["white", "black", "asian", "hispanic", "indigenous", "other"]


class Anthropometrics(BaseModel):
    """Patient anthropometric measurements."""

    height_cm: Annotated[float, Field(gt=0)]
    weight_kg: Annotated[float, Field(gt=0)]
    waist_circumference_cm: Annotated[float, Field(gt=0)]


class ClinicalMeasurements(BaseModel):
    """Patient clinical lab and vital measurements."""

    hba1c_percent: Annotated[float, Field(gt=0)]
    fasting_glucose_mg_dl: Annotated[float, Field(gt=0)]
    systolic_bp_mmhg: Annotated[int, Field(gt=0)]
    diastolic_bp_mmhg: Annotated[int, Field(gt=0)]
    total_cholesterol_mg_dl: Annotated[float, Field(gt=0)]
    hdl_cholesterol_mg_dl: Annotated[float, Field(gt=0)]


class Lifestyle(BaseModel):
    """Patient lifestyle factors."""

    physical_activity_minutes_per_week: Annotated[int, Field(ge=0)]
    smoking_status: Literal["never", "former", "current"]
    family_history_diabetes: bool


class AssessmentRequest(BaseModel):
    """Full patient assessment request submitted by the client to POST /assess."""

    patient_external_id: str
    demographics: Demographics
    anthropometrics: Anthropometrics
    clinical: ClinicalMeasurements
    lifestyle: Lifestyle


class ValidatedFeatures(BaseModel):
    """Engineered feature vector returned by the rust_service /score endpoint."""

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


class ClinicalScoreResult(BaseModel):
    """A single clinical risk score with its risk category label."""

    # int | float preserves the original JSON numeric type:
    # integer scores (findrisc, ada) stay as int; float scores (cambridge) stay as float.
    score: int | float
    risk_category: str


class ClinicalScores(BaseModel):
    """All three clinical screening scores returned by the rust_service."""

    findrisc: ClinicalScoreResult
    ada: ClinicalScoreResult
    cambridge: ClinicalScoreResult


class ShapValues(BaseModel):
    """Per-feature SHAP attribution values from the ml_service."""

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


class MLPrediction(BaseModel):
    """ML model output returned by the ml_service /predict endpoint."""

    probability: Annotated[float, Field(ge=0.0, le=1.0)]
    confidence_lower: Annotated[float, Field(ge=0.0, le=1.0)]
    confidence_upper: Annotated[float, Field(ge=0.0, le=1.0)]
    shap_values: ShapValues


class AssessmentResponse(BaseModel):
    """Assembled assessment result returned by the backend to the client."""

    patient_external_id: str
    assessment_timestamp_utc: str
    validated_features: ValidatedFeatures
    clinical_scores: ClinicalScores
    ml_prediction: MLPrediction
