from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..models.payment import PaymentProvider, PaymentStatus
from .base import ORMModel, TimestampSchema


class PaymentBase(ORMModel):
    bot_id: int
    user_id: int
    amount: Decimal
    currency: str = "RUB"
    payment_provider: PaymentProvider
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    external_id: Optional[str] = None


class PaymentUpdate(ORMModel):
    status: Optional[PaymentStatus] = None
    external_id: Optional[str] = None
    payload: Optional[dict] = None
    paid_at: Optional[datetime] = None


class PaymentRead(PaymentBase, TimestampSchema):
    id: int
    status: PaymentStatus
    external_id: Optional[str]
    payload: Optional[dict]
    paid_at: Optional[datetime]

