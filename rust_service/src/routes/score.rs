//! Score endpoint — accepts an assessment request and returns computed clinical risk scores.

use axum::{routing::post, Json, Router};
use serde::{Deserialize, Serialize};

use crate::config::Config;
use crate::scoring::{self, ScoringFeatures};

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
struct Demographics {
    age_years: u32,
    sex: String,
    ethnicity: String,
}

#[derive(Debug, Deserialize)]
struct Anthropometrics {
    height_cm: f64,
    weight_kg: f64,
    waist_circumference_cm: f64,
}

#[derive(Debug, Deserialize)]
struct ClinicalMeasurements {
    hba1c_percent: f64,
    fasting_glucose_mg_dl: f64,
    systolic_bp_mmhg: i32,
    diastolic_bp_mmhg: i32,
    total_cholesterol_mg_dl: f64,
    hdl_cholesterol_mg_dl: f64,
}

#[derive(Debug, Deserialize)]
struct Lifestyle {
    physical_activity_minutes_per_week: i32,
    smoking_status: String,
    family_history_diabetes: bool,
}

#[derive(Debug, Deserialize)]
struct AssessmentRequest {
    patient_external_id: String,
    demographics: Demographics,
    anthropometrics: Anthropometrics,
    clinical: ClinicalMeasurements,
    lifestyle: Lifestyle,
}

// ---------------------------------------------------------------------------
// Response types
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

async fn score_handler(Json(payload): Json<AssessmentRequest>) -> Json<ScoreResponse> {
    // Log fields not consumed by scoring algorithms so every request field is observed.
    tracing::debug!(
        patient_id = %payload.patient_external_id,
        diastolic_bp = payload.clinical.diastolic_bp_mmhg,
        total_cholesterol = payload.clinical.total_cholesterol_mg_dl,
        hdl_cholesterol = payload.clinical.hdl_cholesterol_mg_dl,
        "scoring assessment"
    );

    let bmi =
        payload.anthropometrics.weight_kg / (payload.anthropometrics.height_cm / 100.0).powi(2);

    let sex_is_female = payload.demographics.sex == "female";
    let smoking_current = payload.lifestyle.smoking_status == "current";

    let features = ScoringFeatures {
        age_years: payload.demographics.age_years,
        sex_is_female,
        bmi,
        waist_circumference_cm: payload.anthropometrics.waist_circumference_cm,
        physical_activity_minutes_per_week: payload.lifestyle.physical_activity_minutes_per_week,
        family_history_diabetes: payload.lifestyle.family_history_diabetes,
        smoking_current,
        systolic_bp_mmhg: payload.clinical.systolic_bp_mmhg,
        hba1c_percent: payload.clinical.hba1c_percent,
        fasting_glucose_mg_dl: payload.clinical.fasting_glucose_mg_dl,
    };

    let (findrisc_score, findrisc_category) = scoring::compute_findrisc(&features);
    let (ada_score, ada_category) = scoring::compute_ada(&features);
    let cambridge_probability = scoring::compute_cambridge(&features);

    let sex_encoded = match payload.demographics.sex.as_str() {
        "male" => 0,
        "female" => 1,
        _ => 2,
    };

    let ethnicity_encoded = match payload.demographics.ethnicity.as_str() {
        "white" => 0,
        "black" => 1,
        "asian" => 2,
        "hispanic" => 3,
        "indigenous" => 4,
        _ => 5,
    };

    let cambridge_category = if cambridge_probability < 0.17 {
        "low"
    } else if cambridge_probability <= 0.30 {
        "moderate"
    } else {
        "high"
    };

    Json(ScoreResponse {
        validated_features: ValidatedFeatures {
            bmi,
            age_years: payload.demographics.age_years as i32,
            sex_encoded,
            ethnicity_encoded,
            hba1c_percent: payload.clinical.hba1c_percent,
            fasting_glucose_mg_dl: payload.clinical.fasting_glucose_mg_dl,
            waist_circumference_cm: payload.anthropometrics.waist_circumference_cm,
            systolic_bp_mmhg: payload.clinical.systolic_bp_mmhg,
            physical_activity_minutes_per_week: payload
                .lifestyle
                .physical_activity_minutes_per_week,
            smoking_current,
            family_history_diabetes: payload.lifestyle.family_history_diabetes,
        },
        clinical_scores: ClinicalScores {
            findrisc: IntScoreResult {
                score: findrisc_score,
                risk_category: findrisc_category.to_owned(),
            },
            ada: IntScoreResult {
                score: ada_score,
                risk_category: ada_category.to_owned(),
            },
            cambridge: FloatScoreResult {
                score: cambridge_probability,
                risk_category: cambridge_category.to_owned(),
            },
        },
    })
}
