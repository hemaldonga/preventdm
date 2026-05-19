//! Cambridge Diabetes Risk Score implementation.

use crate::scoring::ScoringFeatures;

/// Compute the Cambridge Diabetes Risk Score for a patient.
///
/// Reference: Griffin SJ, Little PS, Hales CN, et al. Diabetes risk score: towards earlier
/// detection of Type 2 diabetes in general practice. Diabetes/Metabolism Research and Reviews.
/// 2000;16(3):164-171.
///
/// The score is a logistic regression model. Returns a raw probability in `[0.0, 1.0]`.
/// No risk category is encoded in this function; the caller maps the probability to a label.
///
/// Approximations for fields absent from the request schema:
/// - **Steroid use**: coefficient 0.709 from the reference; assumed absent (contributes 0.0).
/// - **Antihypertensive treatment**: proxied by `systolic_bp_mmhg >= 140`, consistent with the
///   FINDRISC and ADA approximations.
pub fn compute_cambridge(features: &ScoringFeatures) -> f64 {
    // Steroid use: field absent from request schema — coefficient contribution assumed zero.
    let linear = -6.322
        + 0.0354 * features.age_years as f64
        + if features.sex_is_female { -0.742 } else { 0.0 }
        + 0.089 * features.bmi
        + if features.family_history_diabetes { 0.934 } else { 0.0 }
        + if features.smoking_current { 0.855 } else { 0.0 }
        // Antihypertensive treatment: proxied by systolic BP >= 140 mmHg.
        + if features.systolic_bp_mmhg >= 140 { 0.836 } else { 0.0 };

    1.0 / (1.0 + f64::exp(-linear))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scoring::ScoringFeatures;

    fn make_features(
        age_years: u32,
        sex_is_female: bool,
        bmi: f64,
        family_history_diabetes: bool,
        smoking_current: bool,
        systolic_bp_mmhg: i32,
    ) -> ScoringFeatures {
        ScoringFeatures {
            age_years,
            sex_is_female,
            bmi,
            waist_circumference_cm: 85.0,
            physical_activity_minutes_per_week: 150,
            family_history_diabetes,
            smoking_current,
            systolic_bp_mmhg,
            hba1c_percent: 5.5,
            fasting_glucose_mg_dl: 95.0,
        }
    }

    #[test]
    fn test_cambridge_reference_case() {
        // linear = -6.322 + (0.0354*52) + 0.0 + (0.089*28.4) + 0.934 + 0.0 + 0.0
        //        = -6.322 + 1.8408 + 2.5276 + 0.934 = -1.0196
        // probability ≈ 0.265
        let f = make_features(52, false, 28.4, true, false, 138);
        let result = compute_cambridge(&f);
        assert!(
            f64::abs(result - 0.265) < 0.001,
            "expected ~0.265, got {result}"
        );
    }

    #[test]
    fn test_cambridge_high_risk() {
        // linear = -6.322 + (0.0354*70) + (-0.742) + (0.089*33.0) + 0.934 + 0.855 + 0.836
        //        = -6.322 + 2.478 - 0.742 + 2.937 + 0.934 + 0.855 + 0.836 = 0.976
        // probability ≈ 0.726
        let f = make_features(70, true, 33.0, true, true, 145);
        let result = compute_cambridge(&f);
        assert!(
            f64::abs(result - 0.726) < 0.001,
            "expected ~0.726, got {result}"
        );
    }

    #[test]
    fn test_cambridge_low_risk() {
        // linear = -6.322 + (0.0354*35) + (-0.742) + (0.089*22.0) + 0.0 + 0.0 + 0.0
        //        = -6.322 + 1.239 - 0.742 + 1.958 = -3.867
        // probability ≈ 0.021
        let f = make_features(35, true, 22.0, false, false, 110);
        let result = compute_cambridge(&f);
        assert!(
            f64::abs(result - 0.021) < 0.001,
            "expected ~0.021, got {result}"
        );
    }
}
