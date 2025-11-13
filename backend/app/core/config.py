from __future__ import annotations

import json
import secrets
from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("config/env.local", "config/env.example"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    version: str = "0.1.0"
    project_name: str = "LumenPay Bot"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"  # noqa: S104 - требуется для запуска в контейнере
    port: int = 8000
    reload: bool = True
    log_level: str = "INFO"

    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    access_token_expire_minutes: int = 60

    backend_cors_origins: list[AnyHttpUrl] | list[str] = ["http://localhost:5173"]

    database_url: str = "sqlite+aiosqlite:///./lumenpay.db"
    sync_database_url: str = "sqlite:///./lumenpay.db"
    redis_url: str = "redis://localhost:6379/0"

    timezone: str = "Europe/Moscow"

    admin_seed_username: str | None = None
    admin_seed_password: SecretStr | None = None

    bot_token_encryption_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32))
    )
    telegram_bot_token: SecretStr | None = None

    backup_enabled: bool = True
    backup_daily_time: str = "03:00"
    backup_directory: str = "backups"
    backup_keep_days: int = 7
    backup_yandex_token: SecretStr | None = None
    backup_send_to_telegram: bool = False
    backup_admin_chat_id: int | None = None

    check_db_on_startup: bool = True
    shutdown_graceful: bool = True
    shutdown_delay_seconds: float = 0.0

    yookassa_shop_id: str | None = None
    yookassa_api_key: SecretStr | None = None
    yookassa_return_url: AnyHttpUrl | None = None
    yookassa_success_url: AnyHttpUrl | None = None
    yookassa_failure_url: AnyHttpUrl | None = None

    stripe_api_key: SecretStr | None = None

    sentry_dsn: AnyHttpUrl | None = None

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            v_strip = v.strip()
            if v_strip.startswith("[") and v_strip.endswith("]"):
                return list(json.loads(v_strip))
            return [origin.strip() for origin in v_strip.split(",") if origin]
        if isinstance(v, list):
            return v
        raise ValueError("Некорректный формат BACKEND_CORS_ORIGINS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

