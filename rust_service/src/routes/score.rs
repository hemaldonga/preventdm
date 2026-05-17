//! Score endpoint — accepts an assessment request and returns hardcoded mock scores.

use axum::{routing::post, Json, Router};
use serde::{Deserialize, Serialize};

use crate::config::Config;

// ---------------------------------------------------------------------------
// Request types (Deserialize only — fields are validated by serde on ingress)
//
// All fields are intentionally unread: the handler returns hardcoded mock data.
// Real scoring logic (which will read these fields) is deferred to a later phase.
// ---------------------------------------------------------------------------

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct Demographics {
    age_years: u32,
    sex: String,
    ethnicity: String,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct Anthropometrics {
    height_cm: f64,
    weight_kg: f64,
    waist_circumference_cm: f64,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct ClinicalMeasurements {
    hba1c_percent: f64,
    fasting_glucose_mg_dl: f64,
    systolic_bp_mmhg: i32,
    diastolic_bp_mmhg: i32,
    total_cholesterol_mg_dl: f64,
    hdl_cholesterol_mg_dl: f64,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct Lifestyle {
    physical_activity_minutes_per_week: i32,
    smoking_status: String,
    family_history_diabetes: bool,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct AssessmentRequest {
    patient_external_id: String,
    demographics: Demographics,
    anthropometrics: Anthropometrics,
    clinical: ClinicalMeasurements,
    lifestyle: Lifestyle,
}

// ---------------------------------------------------------------------------
// Response types (Serialize only)
// ---------------------------------------------------------------------------

#[derive(Debug, Serialize)]
struct ValidatedFeatures {
    bmi: f64,
    age_years: i32,
    sex_encoded: i32,
    ethnicity_encoded: i32,
    hba1c_percent: f64,
    fasting_glucose_mg_dl: f64,
    waist_circumference_cm: f64,
    systolic_bp_mmhg: i32,
    physical_activity_minutes_per_week: i32,
    smoking_current: bool,
    family_history_diabetes: bool,
}

/// Score result where the score value is an integer (findrisc, ada).
#[derive(Debug, Serialize)]
struct IntScoreResult {
    score: i32,
    risk_category: String,
}

/// Score result where the score value is a float (cambridge).
#[derive(Debug, Serialize)]
struct FloatScoreResult {
    score: f64,
    risk_category: String,
}

#[derive(Debug, Serialize)]
struct ClinicalScores {
    findrisc: IntScoreResult,
    ada: IntScoreResult,
    cambridge: FloatScoreResult,
}

#[derive(Debug, Serialize)]
struct ScoreResponse {
    validated_features: ValidatedFeatures,
    clinical_scores: ClinicalScores,
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

/// Build the score router, registering `POST /score`.
pub fn router() -> Router<Config> {
    Router::<Config>::new().route("/score", post(score_handler))
}

async fn score_handler(Json(_payload): Json<AssessmentRequest>) -> Json<ScoreResponse> {
    // Input is deserialized and validated by serde; real scoring deferred to a later phase.
    Json(ScoreResponse {
        validated_features: ValidatedFeatures {
            bmi: 28.4,
            age_years: 52,
            sex_encoded: 0,
            ethnicity_encoded: 0,
            hba1c_percent: 6.1,
            fasting_glucose_mg_dl: 115.0,
            waist_circumference_cm: 102.0,
            systolic_bp_mmhg: 138,
            physical_activity_minutes_per_week: 90,
            smoking_current: false,
            family_history_diabetes: true,
        },
        clinical_scores: ClinicalScores {
            findrisc: IntScoreResult {
                score: 14,
                risk_category: "moderate".to_owned(),
            },
            ada: IntScoreResult {
                score: 6,
                risk_category: "high".to_owned(),
            },
            cambridge: FloatScoreResult {
                score: 0.27,
                risk_category: "moderate".to_owned(),
            },
        },
    })
}
