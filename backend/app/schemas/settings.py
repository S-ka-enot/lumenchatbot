from __future__ import annotations

from pydantic import BaseModel, Field


class YooKassaSettingsResponse(BaseModel):
    shop_id: str | None = None
    is_configured: bool = Field(default=False, description="Есть ли сохранённые настройки")
    has_api_key: bool = Field(default=False, description="Сохранён ли секретный ключ")


class YooKassaSettingsUpdate(BaseModel):
    shop_id: str = Field(..., min_length=4, max_length=255)
    api_key: str | None = Field(default=None, min_length=1, max_length=512)
