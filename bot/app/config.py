from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("config/env.local", "config/env.example"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    environment: str = Field(default="development")
    bot_token: SecretStr = Field(alias="TELEGRAM_BOT_TOKEN")
    backend_base_url: AnyHttpUrl | str = Field(default="http://localhost:8000")
    backend_api_prefix: str = Field(default="/api/v1")
    request_timeout_seconds: float = Field(default=15.0, ge=1.0)
    polling_interval: float = Field(default=1.0, ge=0.1)
    timezone: str = Field(default="Europe/Moscow")
    sentry_dsn: AnyHttpUrl | None = None


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()


settings = get_settings()