"""Sample patient assessment payload used by the CLI test harness."""

from __future__ import annotations

from typing import Any


def get_sample_payload(patient_id: str) -> dict[str, Any]:
    """Return the standard test assessment payload with the given patient external ID.

    All clinical values are fixed so the test is deterministic and repeatable.
    The patient_id is parameterised so tests never collide with real patient data.
    """
    return {
        "patient_external_id": patient_id,
        "demographics": {
            "age_years": 52,
            "sex": "male",
            "ethnicity": "white",
        },
        "anthropometrics": {
            "height_cm": 175.0,
            "weight_kg": 87.0,
            "waist_circumference_cm": 102.0,
        },
        "clinical": {
            "hba1c_percent": 6.1,
            "fasting_glucose_mg_dl": 115.0,
            "systolic_bp_mmhg": 138,
            "diastolic_bp_mmhg": 88,
            "total_cholesterol_mg_dl": 210.0,
            "hdl_cholesterol_mg_dl": 42.0,
        },
        "lifestyle": {
            "physical_activity_minutes_per_week": 90,
            "smoking_status": "never",
            "family_history_diabetes": True,
        },
    }
