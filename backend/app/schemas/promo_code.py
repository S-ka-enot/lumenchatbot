from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..models.promo_code import DiscountType
from .base import ORMModel, TimestampSchema


class PromoCodeBase(ORMModel):
    bot_id: int
    code: str
    discount_type: DiscountType
    discount_value: Decimal
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    description: Optional[str] = None


class PromoCodeCreate(PromoCodeBase):
    pass


class PromoCodeUpdate(ORMModel):
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = None
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class PromoCodeRead(PromoCodeBase, TimestampSchema):
    id: int
    used_count: int
    is_active: bool

