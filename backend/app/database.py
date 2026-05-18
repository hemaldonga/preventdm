"""SQLAlchemy async engine, session factory, and FastAPI session dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_settings = get_settings()
_engine: AsyncEngine = create_async_engine(_settings.async_database_url, echo=_settings.log_sql)
_async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _engine, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield one AsyncSession per request; used as a FastAPI dependency."""
    async with _async_session_factory() as session:
        yield session
