from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field, model_validator

from .base import ORMModel, TimestampSchema


class SubscriptionBase(ORMModel):
    bot_id: int
    user_id: int
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    auto_renew: bool = False


class SubscriptionCreate(ORMModel):
    user_id: int
    bot_id: int
    payment_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    auto_renew: bool = False
    plan_id: Optional[int] = None


class SubscriptionUpdate(ORMModel):
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    auto_renew: Optional[bool] = None


class SubscriptionRead(SubscriptionBase, TimestampSchema):
    id: int
    payment_id: Optional[int]
    plan_id: Optional[int]
    is_active: bool


class SubscriptionExtendRequest(ORMModel):
    extend_days: Optional[int] = Field(default=None, ge=1, le=365)
    new_end_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_choice(self) -> "SubscriptionExtendRequest":
        if self.extend_days is None and self.new_end_date is None:
            raise ValueError("Укажите количество дней продления или новую дату окончания")
        return self

