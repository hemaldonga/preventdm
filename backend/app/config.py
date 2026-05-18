"""Application configuration via pydantic-settings."""

from __future__ import annotations

import functools
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PreventDM Backend"
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    rust_service_url: str = "http://rust_service:8001"
    ml_service_url: str = "http://ml_service:8002"
    database_url: str
    log_sql: bool = False

    @property
    def async_database_url(self) -> str:
        """Rewrite the URL prefix so SQLAlchemy uses the asyncpg driver.

        Compose supplies postgresql://...; asyncpg requires postgresql+asyncpg://...
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://") :]
        return url


@functools.lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance, constructing it on the first call."""
    return Settings()
