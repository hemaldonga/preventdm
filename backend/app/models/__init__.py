"""ORM model exports.

All models are imported here so that Base.metadata is fully populated
before Alembic or the application inspects it.
"""

from app.models.base import Base
from app.models.clinical_score import ClinicalScore
from app.models.patient import Patient
from app.models.risk_assessment import RiskAssessment

__all__ = ["Base", "ClinicalScore", "Patient", "RiskAssessment"]
