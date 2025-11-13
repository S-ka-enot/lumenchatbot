from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from .base import ORMModel, TimestampSchema
from .channel import ChannelRead
from ..utils.validators import validate_price_amount


class SubscriptionPlanBase(ORMModel):
    bot_id: int
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: str | None = None
    price_amount: Decimal = Field(..., ge=Decimal("0"))
    price_currency: str = Field(default="RUB", max_length=10)
    duration_days: int = Field(..., ge=1, le=365)
    is_active: bool = True
    is_recommended: bool = False

    @field_validator("price_amount")
    @classmethod
    def validate_price_amount_field(cls, v: Decimal) -> Decimal:
        return validate_price_amount(v)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    channel_ids: list[int] = Field(default_factory=list)


class SubscriptionPlanUpdate(ORMModel):
    name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    price_currency: str | None = Field(default=None, max_length=10)
    duration_days: int | None = Field(default=None, ge=1, le=365)
    is_active: bool | None = None
    is_recommended: bool | None = None
    channel_ids: list[int] | None = None

    @field_validator("price_amount")
    @classmethod
    def validate_price_amount_field(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return None
        return validate_price_amount(v)


class SubscriptionPlanRead(SubscriptionPlanBase, TimestampSchema):
    id: int
    channels: list[ChannelRead] = Field(default_factory=list)


class SubscriptionPlanPublic(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None
    price_amount: Decimal
    price_currency: str
    duration_days: int
    is_recommended: bool
    channels: list[dict[str, Any]] = Field(default_factory=list)
