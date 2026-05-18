"""RiskAssessment ORM model (performed_by FK added in a later phase)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.clinical_score import ClinicalScore
    from app.models.patient import Patient


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    assessment_timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    probability: Mapped[float] = mapped_column(Float(), nullable=False)
    confidence_lower: Mapped[float] = mapped_column(Float(), nullable=False)
    confidence_upper: Mapped[float] = mapped_column(Float(), nullable=False)
    shap_values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    patient: Mapped[Patient] = relationship("Patient", back_populates="risk_assessments")
    clinical_scores: Mapped[list[ClinicalScore]] = relationship(
        "ClinicalScore", back_populates="assessment", cascade="all, delete-orphan"
    )
