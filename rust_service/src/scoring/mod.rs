//! Clinical diabetes risk scoring algorithms.
//!
//! Implements three validated tools: FINDRISC, the ADA Risk Test, and the Cambridge Risk Score.
//! All three share the same [`ScoringFeatures`] input struct extracted from the assessment request.

pub mod ada;
pub mod cambridge;
pub mod findrisc;

pub use ada::compute_ada;
pub use cambridge::compute_cambridge;
pub use findrisc::compute_findrisc;

/// Normalised, algorithm-ready features extracted from a patient assessment request.
///
/// BMI is pre-computed from height and weight. Sex and smoking status are represented as booleans.
/// All other values are taken directly from the corresponding request fields.
pub struct ScoringFeatures {
    pub age_years: u32,
    pub sex_is_female: bool,
    pub bmi: f64,
    pub waist_circumference_cm: f64,
    pub physical_activity_minutes_per_week: i32,
    pub family_history_diabetes: bool,
    pub smoking_current: bool,
    pub systolic_bp_mmhg: i32,
    pub hba1c_percent: f64,
    pub fasting_glucose_mg_dl: f64,
}
