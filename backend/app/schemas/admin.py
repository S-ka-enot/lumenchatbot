from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from ..utils.validators import (
    validate_amount,
    validate_phone_number,
    validate_telegram_id,
)


class DashboardMetric(BaseModel):
    id: str
    title: str
    value: str
    change: str | None = None
    icon: str = Field(default="users")


class RevenuePoint(BaseModel):
    date: str
    value: Decimal


class ActivityItem(BaseModel):
    id: str
    title: str
    description: str
    timestamp: datetime


class DashboardSummary(BaseModel):
    metrics: list[DashboardMetric] = Field(default_factory=list)
    revenue_trend: list[RevenuePoint] = Field(default_factory=list)
    recent_activity: list[ActivityItem] = Field(default_factory=list)


class BotSummary(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    has_token: bool


class BotDetails(BaseModel):
    id: int
    name: str
    slug: str
    timezone: str
    is_active: bool
    has_token: bool


class BotTokenUpdate(BaseModel):
    token: str = Field(..., min_length=10, description="Новый токен телеграм бота")


class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название бота")
    slug: str = Field(..., min_length=1, max_length=255, description="Уникальный идентификатор бота")
    timezone: str = Field(default="Europe/Moscow", max_length=64, description="Часовой пояс")
    is_active: bool = Field(default=True, description="Активен ли бот")


class BotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255, description="Название бота")
    slug: str | None = Field(default=None, min_length=1, max_length=255, description="Уникальный идентификатор бота")
    timezone: str | None = Field(default=None, max_length=64, description="Часовой пояс")
    is_active: bool | None = Field(default=None, description="Активен ли бот")


class SubscriberListItem(BaseModel):
    id: int
    bot_id: int
    telegram_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str
    phone_number: str | None = None
    tariff: str | None = None
    expires_at: datetime | None = None
    status: str
    is_blocked: bool
    active_subscription_id: int | None = None


class SubscriberCreate(BaseModel):
    bot_id: int | None = Field(
        default=None, description="ID бота; если не указан, будет выбран первый доступный"
    )
    telegram_id: int = Field(..., gt=0)
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    is_blocked: bool | None = False
    subscription_days: int | None = Field(default=None, gt=0, le=365)
    subscription_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    subscription_description: str | None = Field(
        default="Продление через админку", max_length=255
    )
    plan_id: int | None = None

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id_field(cls, v: int) -> int:
        return validate_telegram_id(v)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number_field(cls, v: str | None) -> str | None:
        return validate_phone_number(v)

    @field_validator("subscription_amount")
    @classmethod
    def validate_subscription_amount_field(cls, v: Decimal | None) -> Decimal | None:
        return validate_amount(v)


class SubscriberUpdate(BaseModel):
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    is_blocked: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number_field(cls, v: str | None) -> str | None:
        return validate_phone_number(v)


class SubscriptionExtendRequest(BaseModel):
    days: int = Field(..., gt=0, le=365)
    amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    description: str | None = Field(
        default="Продление через админку", max_length=255
    )
    plan_id: int | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount_field(cls, v: Decimal | None) -> Decimal | None:
        return validate_amount(v)


class PaymentListItem(BaseModel):
    id: int
    invoice: str
    member: str
    amount: str
    status: str
    created_at: datetime

