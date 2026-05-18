"""ClinicalScore ORM model — one row per score type per assessment."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.risk_assessment import RiskAssessment


class ClinicalScore(Base):
    __tablename__ = "clinical_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_assessments.id"), nullable=False, index=True
    )
    score_type: Mapped[str] = mapped_column(String(32), nullable=False)
    score_value: Mapped[float] = mapped_column(Float(), nullable=False)
    risk_category: Mapped[str] = mapped_column(String(32), nullable=False)

    assessment: Mapped[RiskAssessment] = relationship(
        "RiskAssessment", back_populates="clinical_scores"
    )
