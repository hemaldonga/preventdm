//! FINDRISC (Finnish Diabetes Risk Score) implementation.

use crate::scoring::ScoringFeatures;

/// Compute the FINDRISC score for a patient.
///
/// Reference: Lindström JT, Tuomilehto J. The diabetes risk score.
/// Diabetes Care. 2003;26(3):725-731.
///
/// Returns the integer total score and a static risk-category label:
/// `"low"`, `"slightly_elevated"`, `"moderate"`, `"high"`, or `"very_high"`.
///
/// Approximations for fields absent from the request schema:
/// - **Daily vegetable/fruit consumption**: assumed adequate (0 points) — field unavailable.
/// - **Antihypertensive medication use**: proxied by `systolic_bp_mmhg >= 140` (2 points) —
///   medication status is not captured in the schema.
pub fn compute_findrisc(features: &ScoringFeatures) -> (i32, &'static str) {
    let age_points = match features.age_years {
        0..=44 => 0,
        45..=54 => 2,
        55..=64 => 3,
        _ => 4,
    };

    let bmi_points = if features.bmi < 25.0 {
        0
    } else if features.bmi <= 30.0 {
        1
    } else {
        3
    };

    let waist_points = if features.sex_is_female {
        if features.waist_circumference_cm < 80.0 {
            0
        } else if features.waist_circumference_cm <= 88.0 {
            3
        } else {
            4
        }
    } else if features.waist_circumference_cm < 94.0 {
        0
    } else if features.waist_circumference_cm <= 102.0 {
        3
    } else {
        4
    };

    let activity_points = if features.physical_activity_minutes_per_week >= 150 {
        0
    } else {
        2
    };

    // Vegetable/fruit consumption: field not available in request schema; assumed adequate (0 pts).
    let vegetable_points: i32 = 0;

    // Antihypertensive medication use: not captured in schema; proxied by systolic BP >= 140 mmHg.
    let hypertension_points = if features.systolic_bp_mmhg >= 140 {
        2
    } else {
        0
    };

    let glucose_points = if features.hba1c_percent >= 5.7 || features.fasting_glucose_mg_dl >= 100.0
    {
        5
    } else {
        0
    };

    let family_points = if features.family_history_diabetes {
        5
    } else {
        0
    };

    let total = age_points
        + bmi_points
        + waist_points
        + activity_points
        + vegetable_points
        + hypertension_points
        + glucose_points
        + family_points;

    let category = match total {
        0..=7 => "low",
        8..=11 => "slightly_elevated",
        12..=14 => "moderate",
        15..=20 => "high",
        _ => "very_high",
    };

    (total, category)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scoring::ScoringFeatures;

    #[allow(clippy::too_many_arguments)]
    fn make_features(
        age_years: u32,
        sex_is_female: bool,
        bmi: f64,
        waist_circumference_cm: f64,
        physical_activity_minutes_per_week: i32,
        family_history_diabetes: bool,
        hba1c_percent: f64,
        fasting_glucose_mg_dl: f64,
        systolic_bp_mmhg: i32,
    ) -> ScoringFeatures {
        ScoringFeatures {
            age_years,
            sex_is_female,
            bmi,
            waist_circumference_cm,
            physical_activity_minutes_per_week,
            family_history_diabetes,
            smoking_current: false,
            systolic_bp_mmhg,
            hba1c_percent,
            fasting_glucose_mg_dl,
        }
    }

    #[test]
    fn test_findrisc_reference_case() {
        // age 52 (45-54) = 2, BMI 28.4 (25-30) = 1, waist 102.0 cm male (94-102 incl.) = 3,
        // activity 90 < 150 = 2, vegetables = 0, hypertension proxy systolic 138 < 140 = 0,
        // high glucose hba1c 6.1 >= 5.7 = 5, family history = 5. Total = 18.
        let f = make_features(52, false, 28.4, 102.0, 90, true, 6.1, 115.0, 138);
        let (score, category) = compute_findrisc(&f);
        assert_eq!(score, 18);
        assert_eq!(category, "high");
    }

    #[test]
    fn test_findrisc_low_risk() {
        // age 35 (<45) = 0, BMI 22.0 (<25) = 0, waist 82.0 male (<94) = 0,
        // activity 200 >= 150 = 0, vegetables = 0, systolic 115 < 140 = 0,
        // hba1c 5.2 and glucose 90.0 both below thresholds = 0, family history false = 0.
        // Total = 0.
        let f = make_features(35, false, 22.0, 82.0, 200, false, 5.2, 90.0, 115);
        let (score, category) = compute_findrisc(&f);
        assert_eq!(score, 0);
        assert_eq!(category, "low");
    }

    #[test]
    fn test_findrisc_very_high_risk() {
        // age 70 (>=65) = 4, BMI 35.0 (>30) = 3, waist 95.0 cm female (>88) = 4,
        // activity 30 < 150 = 2, vegetables = 0, hypertension systolic 145 >= 140 = 2,
        // high glucose hba1c 6.2 >= 5.7 = 5, family history = 5. Total = 25.
        let f = make_features(70, true, 35.0, 95.0, 30, true, 6.2, 110.0, 145);
        let (score, category) = compute_findrisc(&f);
        assert_eq!(score, 25);
        assert_eq!(category, "very_high");
    }
}
