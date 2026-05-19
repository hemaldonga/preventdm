"""Shared pytest fixtures for the PreventDM backend test suite."""

from __future__ import annotations

# Must be first — database.py creates its engine at import time using get_settings(),
# so DATABASE_URL must point to the test database before any app module is imported.
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://preventdm:preventdm_dev_password@localhost:5432/preventdm_test",
)

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.config import Settings, get_settings
from app.database import get_db
from app.main import app
from app.models import Base

TEST_DATABASE_URL = (
    "postgresql+asyncpg://preventdm:preventdm_dev_password@localhost:5432/preventdm_test"
)

_RUST_RESPONSE: dict[str, Any] = {
    "validated_features": {
        "bmi": 28.4,
        "age_years": 45,
        "sex_encoded": 0,
        "ethnicity_encoded": 0,
        "hba1c_percent": 5.9,
        "fasting_glucose_mg_dl": 102.0,
        "waist_circumference_cm": 92.0,
        "systolic_bp_mmhg": 128,
        "physical_activity_minutes_per_week": 90,
        "smoking_current": False,
        "family_history_diabetes": True,
    },
    "clinical_scores": {
        "findrisc": {"score": 14, "risk_category": "moderate"},
        "ada": {"score": 6, "risk_category": "high"},
        "cambridge": {"score": 0.27, "risk_category": "moderate"},
    },
}

_ML_RESPONSE: dict[str, Any] = {
    "probability": 0.34,
    "confidence_lower": 0.28,
    "confidence_upper": 0.41,
    "shap_values": {
        "bmi": 0.12,
        "age_years": 0.08,
        "hba1c_percent": 0.15,
        "fasting_glucose_mg_dl": 0.10,
        "waist_circumference_cm": 0.06,
        "systolic_bp_mmhg": 0.04,
        "physical_activity_minutes_per_week": -0.05,
        "smoking_current": 0.01,
        "family_history_diabetes": 0.09,
        "sex_encoded": -0.02,
        "ethnicity_encoded": 0.00,
    },
}


def _run_alembic_upgrade() -> None:
    """Run Alembic migrations to head.

    Called via asyncio.to_thread() to avoid running asyncio.run() inside the
    already-running pytest-asyncio event loop.
    """
    from alembic.config import Config as AlembicConfig

    from alembic import command as alembic_command

    cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(cfg, "head")


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def settings_override() -> Settings:
    """Settings instance pointing at the test database."""
    return Settings(
        database_url="postgresql://preventdm:preventdm_dev_password@localhost:5432/preventdm_test"
    )


async def _reset_schema(engine: AsyncEngine) -> None:
    """Drop all app tables and the alembic version table for a clean slate."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create the test engine, run migrations once, and drop all tables on exit."""
    _engine = create_async_engine(TEST_DATABASE_URL)

    # Ensure a clean slate regardless of prior session state, then migrate to head.
    await _reset_schema(_engine)
    # Alembic's env.py calls asyncio.run(); run it in a thread to avoid nesting.
    await asyncio.to_thread(_run_alembic_upgrade)

    yield _engine

    await _reset_schema(_engine)
    await _engine.dispose()


# ---------------------------------------------------------------------------
# Function-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session wrapped in a transaction that is rolled back after each test.

    The session uses join_transaction_mode="create_savepoint" so that
    session.commit() inside repository methods releases a savepoint rather than
    committing the outer transaction, keeping test isolation intact.
    """
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest.fixture
async def app_client(
    db_session: AsyncSession,
    settings_override: Settings,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTPX AsyncClient wired to the FastAPI app with test DB and settings injected."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = lambda: settings_override

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_rust_service() -> Generator[AsyncMock, None, None]:
    """Patch call_rust_service in the assess router with a fixed success response."""
    mock = AsyncMock(return_value=_RUST_RESPONSE)
    with patch("app.routers.assess.call_rust_service", mock):
        yield mock


@pytest.fixture
def mock_ml_service() -> Generator[AsyncMock, None, None]:
    """Patch call_ml_service in the assess router with a fixed success response."""
    mock = AsyncMock(return_value=_ML_RESPONSE)
    with patch("app.routers.assess.call_ml_service", mock):
        yield mock


@pytest.fixture
def sample_payload() -> dict[str, Any]:
    """Valid AssessmentRequest payload matching Phase 8/9 integration test values."""
    return {
        "patient_external_id": "TEST-UNIT-001",
        "demographics": {
            "age_years": 45,
            "sex": "male",
            "ethnicity": "white",
        },
        "anthropometrics": {
            "height_cm": 175.0,
            "weight_kg": 87.0,
            "waist_circumference_cm": 92.0,
        },
        "clinical": {
            "hba1c_percent": 5.9,
            "fasting_glucose_mg_dl": 102.0,
            "systolic_bp_mmhg": 128,
            "diastolic_bp_mmhg": 82,
            "total_cholesterol_mg_dl": 195.0,
            "hdl_cholesterol_mg_dl": 52.0,
        },
        "lifestyle": {
            "physical_activity_minutes_per_week": 90,
            "smoking_status": "former",
            "family_history_diabetes": True,
        },
    }
