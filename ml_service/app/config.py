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

    app_name: str = "PreventDM ML Service"
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    port: int = 8002


@functools.lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance, constructing it on the first call."""
    return Settings()
