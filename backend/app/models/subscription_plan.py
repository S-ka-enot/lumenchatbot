from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .bot import Bot
    from .channel import Channel
    from .payment import Payment
    from .subscription import Subscription


subscription_plan_channels = Table(
    "subscription_plan_channels",
    Base.metadata,
    Column("plan_id", ForeignKey("subscription_plans.id", ondelete="CASCADE"), primary_key=True),
    Column("channel_id", ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True),
)


class SubscriptionPlan(TimestampMixin, Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("bot_id", "slug", name="uq_subscription_plan_bot_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_currency: Mapped[str] = mapped_column(String(10), default="RUB", nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bot: Mapped["Bot"] = relationship(back_populates="plans")
    channels: Mapped[list["Channel"]] = relationship(
        secondary=subscription_plan_channels,
        back_populates="plans",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="plan")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SubscriptionPlan id={self.id} name={self.name!r} bot_id={self.bot_id}>"
