"""Patient ORM model (Phase Nine subset — org_id added in a later phase)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.risk_assessment import RiskAssessment


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    dob: Mapped[date] = mapped_column(Date(), nullable=False)
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    ethnicity: Mapped[str] = mapped_column(String(32), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    risk_assessments: Mapped[list[RiskAssessment]] = relationship(
        "RiskAssessment", back_populates="patient"
    )
