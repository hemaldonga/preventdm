//! ADA (American Diabetes Association) Type 2 Diabetes Risk Test implementation.

use crate::scoring::ScoringFeatures;

/// Compute the ADA Type 2 Diabetes Risk Test score for a patient.
///
/// Reference: American Diabetes Association. Type 2 Diabetes Risk Test.
///
/// Returns the integer total score and a static risk-category label:
/// `"low"`, `"moderate"`, or `"high"`.
///
/// Approximations for fields absent from the request schema:
/// - **High blood pressure / antihypertensive medication**: proxied by `systolic_bp_mmhg >= 140`
///   (1 point), consistent with the FINDRISC approximation.
pub fn compute_ada(features: &ScoringFeatures) -> (i32, &'static str) {
    let age_points = match features.age_years {
        0..=39 => 0,
        40..=49 => 1,
        50..=59 => 2,
        _ => 3,
    };

    let sex_points = if features.sex_is_female { 0 } else { 1 };

    let family_points = if features.family_history_diabetes {
        1
    } else {
        0
    };

    // Antihypertensive medication: not captured in schema; proxied by systolic BP >= 140 mmHg.
    let hypertension_points = if features.systolic_bp_mmhg >= 140 {
        1
    } else {
        0
    };

    let activity_points = if features.physical_activity_minutes_per_week < 150 {
        2
    } else {
        0
    };

    let bmi_points = if features.bmi < 25.0 {
        0
    } else if features.bmi < 30.0 {
        1
    } else {
        2
    };

    let total = age_points
        + sex_points
        + family_points
        + hypertension_points
        + activity_points
        + bmi_points;

    let category = match total {
        0..=4 => "low",
        5..=6 => "moderate",
        _ => "high",
    };

    (total, category)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scoring::ScoringFeatures;

    fn make_features(
        age_years: u32,
        sex_is_female: bool,
        bmi: f64,
        physical_activity_minutes_per_week: i32,
        family_history_diabetes: bool,
        systolic_bp_mmhg: i32,
    ) -> ScoringFeatures {
        ScoringFeatures {
            age_years,
            sex_is_female,
            bmi,
            waist_circumference_cm: 80.0,
            physical_activity_minutes_per_week,
            family_history_diabetes,
            smoking_current: false,
            systolic_bp_mmhg,
            hba1c_percent: 5.0,
            fasting_glucose_mg_dl: 85.0,
        }
    }

    #[test]
    fn test_ada_reference_case() {
        // age 52 (50-59) = 2, male = 1, family history = 1, systolic 138 < 140 = 0,
        // activity 90 < 150 = 2, BMI 28.4 (25-29.9) = 1. Total = 7, category "high".
        let f = make_features(52, false, 28.4, 90, true, 138);
        let (score, category) = compute_ada(&f);
        assert_eq!(score, 7);
        assert_eq!(category, "high");
    }

    #[test]
    fn test_ada_low_risk() {
        // age 30 (<40) = 0, female = 0, family history false = 0, systolic 110 < 140 = 0,
        // activity 200 >= 150 = 0, BMI 22.0 (<25) = 0. Total = 0, category "low".
        let f = make_features(30, true, 22.0, 200, false, 110);
        let (score, category) = compute_ada(&f);
        assert_eq!(score, 0);
        assert_eq!(category, "low");
    }

    #[test]
    fn test_ada_moderate_risk() {
        // age 45 (40-49) = 1, female = 0, family history = 1, systolic 130 < 140 = 0,
        // activity 80 < 150 = 2, BMI 27.0 (25-29.9) = 1. Total = 5, category "moderate".
        let f = make_features(45, true, 27.0, 80, true, 130);
        let (score, category) = compute_ada(&f);
        assert_eq!(score, 5);
        assert_eq!(category, "moderate");
    }
}
