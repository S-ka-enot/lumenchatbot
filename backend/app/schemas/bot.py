from __future__ import annotations

from decimal import Decimal
from datetime import datetime, date

from pydantic import AnyHttpUrl, Field, field_validator

from .base import ORMModel, TimestampSchema
from .subscription_plan import SubscriptionPlanPublic
from ..utils.validators import (
    validate_amount,
    validate_phone_number,
    validate_telegram_id,
)


class BotBase(ORMModel):
    name: str
    slug: str
    timezone: str = "Europe/Moscow"


class BotCreate(BotBase):
    telegram_bot_token: str | None = None
    webhook_url: AnyHttpUrl | None = None


class BotUpdate(ORMModel):
    name: str | None = None
    timezone: str | None = None
    webhook_url: AnyHttpUrl | None = None
    is_active: bool | None = None


class BotRead(BotBase, TimestampSchema):
    id: int
    is_active: bool
    webhook_url: str | None = None


class BotUserRegisterRequest(ORMModel):
    telegram_id: int
    bot_id: int | None = None
    username: str | None = None
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id_field(cls, v: int) -> int:
        return validate_telegram_id(v)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number_field(cls, v: str | None) -> str | None:
        return validate_phone_number(v)


class BotUserUpdateRequest(ORMModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    username: str | None = Field(default=None, max_length=255)
    birthday: date | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number_field(cls, v: str | None) -> str | None:
        return validate_phone_number(v)


class ChannelPublic(ORMModel):
    channel_id: str | None = None
    channel_name: str
    channel_username: str | None = None
    invite_link: str | None = None
    description: str | None = None
    requires_subscription: bool = True


class SubscriptionStatusResponse(ORMModel):
    status: str = "inactive"
    is_active: bool = False
    subscription_end: datetime | None = None
    days_left: int | None = None
    auto_renew: bool = False
    channels: list[ChannelPublic] = Field(default_factory=list)
    plan: SubscriptionPlanPublic | None = None


class PaymentCreateRequest(ORMModel):
    user_id: int | None = None
    telegram_id: int
    promo_code: str | None = None
    bot_id: int | None = None
    plan_id: int
    amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    duration_days: int | None = Field(default=None, ge=1, le=365)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id_field(cls, v: int) -> int:
        return validate_telegram_id(v)

    @field_validator("amount")
    @classmethod
    def validate_amount_field(cls, v: Decimal | None) -> Decimal | None:
        return validate_amount(v)


class PaymentCreateResponse(ORMModel):
    payment_id: int
    payment_url: str
    amount: str
    amount_formatted: str
    duration_days: int
    description: str | None = None
    plan_id: int | None = None
    plan_name: str | None = None


class PaymentConfirmResponse(ORMModel):
    status: str
    subscription_end: datetime | None

