from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from .base import ORMModel, TimestampSchema


class BroadcastBase(ORMModel):
    bot_id: int
    channel_id: int | None = None
    message_title: str | None = Field(default=None, max_length=255)
    message_text: str = Field(..., min_length=1)
    parse_mode: str | None = Field(default="None")
    target_audience: str
    user_ids: list[int] | None = Field(default_factory=list)
    birthday_only: bool = False
    media_files: list[dict[str, Any]] | None = Field(default_factory=list)
    scheduled_at: datetime | None = None
    buttons: dict[str, Any] | None = Field(default_factory=dict)

    @field_validator("parse_mode")
    @classmethod
    def validate_parse_mode(cls, v: str | None) -> str | None:
        if v is None:
            return "None"
        valid_modes = ["HTML", "Markdown", "MarkdownV2", "None"]
        if v not in valid_modes:
            raise ValueError(f"parse_mode должен быть одним из: {', '.join(valid_modes)}")
        return v

    @field_validator("target_audience")
    @classmethod
    def validate_target_audience(cls, v: str) -> str:
        valid_audiences = [
            "all",
            "subscribers",
            "active_subscribers",
            "expired_subscribers",
            "expiring_soon",
            "non_subscribers",
            "birthday",
            "custom",
        ]
        if v not in valid_audiences:
            raise ValueError(f"target_audience должен быть одним из: {', '.join(valid_audiences)}")
        return v


class BroadcastCreate(BroadcastBase):
    status: str | None = Field(default="draft")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return "draft"
        valid_statuses = ["pending", "sending", "completed", "canceled", "draft"]
        if v not in valid_statuses:
            raise ValueError(f"status должен быть одним из: {', '.join(valid_statuses)}")
        return v


class BroadcastUpdate(ORMModel):
    channel_id: int | None = None
    message_title: str | None = Field(default=None, max_length=255)
    message_text: str | None = Field(default=None)
    parse_mode: str | None = None
    target_audience: str | None = None
    user_ids: list[int] | None = None
    birthday_only: bool | None = None
    media_files: list[dict[str, Any]] | None = None
    scheduled_at: datetime | None = None
    status: str | None = None
    buttons: dict[str, Any] | None = None

    @field_validator("message_text")
    @classmethod
    def validate_message_text(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("message_text не может быть пустым")
        return v

    @field_validator("parse_mode")
    @classmethod
    def validate_parse_mode(cls, v: str | None) -> str | None:
        if v is None:
            return None
        valid_modes = ["HTML", "Markdown", "MarkdownV2", "None"]
        if v not in valid_modes:
            raise ValueError(f"parse_mode должен быть одним из: {', '.join(valid_modes)}")
        return v

    @field_validator("target_audience")
    @classmethod
    def validate_target_audience(cls, v: str | None) -> str | None:
        if v is None:
            return None
        valid_audiences = [
            "all",
            "subscribers",
            "active_subscribers",
            "expired_subscribers",
            "expiring_soon",
            "non_subscribers",
            "birthday",
            "custom",
        ]
        if v not in valid_audiences:
            raise ValueError(f"target_audience должен быть одним из: {', '.join(valid_audiences)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return None
        valid_statuses = ["pending", "sending", "completed", "canceled", "draft"]
        if v not in valid_statuses:
            raise ValueError(f"status должен быть одним из: {', '.join(valid_statuses)}")
        return v


class BroadcastRead(BroadcastBase, TimestampSchema):
    id: int
    status: str
    sent_at: datetime | None = None
    stats: dict[str, Any] | None = Field(default_factory=dict)

