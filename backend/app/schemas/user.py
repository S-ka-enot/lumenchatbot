from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import Field

from .base import ORMModel, TimestampSchema


class UserBase(ORMModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    birthday: Optional[date] = None


class UserCreate(UserBase):
    bot_id: int
    initial_subscription_days: Optional[int] = Field(default=None, ge=1, le=365)


class UserUpdate(ORMModel):
    first_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    birthday: Optional[date] = None
    is_blocked: Optional[bool] = None
    is_premium: Optional[bool] = None
    subscription_end: Optional[datetime] = None


class UserRead(UserBase, TimestampSchema):
    id: int
    bot_id: int
    is_premium: bool
    subscription_end: Optional[datetime]
    is_blocked: bool

