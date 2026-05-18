"""Initial schema: patients, risk_assessments, clinical_scores.

Revision ID: 0001
Revises:
Create Date: 2026-05-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("sex", sa.String(16), nullable=False),
        sa.Column("ethnicity", sa.String(32), nullable=False),
        sa.Column("postal_code", sa.String(8), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patients_external_id", "patients", ["external_id"], unique=True)

    op.create_table(
        "risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("confidence_lower", sa.Float(), nullable=False),
        sa.Column("confidence_upper", sa.Float(), nullable=False),
        sa.Column("shap_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_assessments_patient_id", "risk_assessments", ["patient_id"], unique=False
    )

    op.create_table(
        "clinical_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score_type", sa.String(32), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("risk_category", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["risk_assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clinical_scores_assessment_id", "clinical_scores", ["assessment_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_scores_assessment_id", table_name="clinical_scores")
    op.drop_table("clinical_scores")
    op.drop_index("ix_risk_assessments_patient_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
    op.drop_index("ix_patients_external_id", table_name="patients")
    op.drop_table("patients")
