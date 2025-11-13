from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .bot import Bot
    from .subscription import Subscription
    from .subscription_plan import SubscriptionPlan
    from .user import User


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentProvider(str, enum.Enum):
    YOOKASSA = "yookassa"
    STRIPE = "stripe"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("payment_provider", "external_id", name="uq_payments_provider_ext"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="RUB", nullable=False)
    payment_provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True
    )

    bot: Mapped["Bot"] = relationship(back_populates="payments")
    user: Mapped["User"] = relationship(back_populates="payments")
    subscription: Mapped["Subscription"] = relationship(back_populates="payment", uselist=False)
    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} status={self.status} user_id={self.user_id}>"

