from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .bot_message import BotMessage
    from .channel import Channel
    from .payment import Payment
    from .promo_code import PromoCode
    from .scheduled_broadcast import ScheduledBroadcast
    from .subscription_plan import SubscriptionPlan
    from .subscription import Subscription
    from .user import User


class Bot(TimestampMixin, Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    telegram_bot_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(512))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="bot", cascade="all, delete-orphan")
    channels: Mapped[list["Channel"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )
    promo_codes: Mapped[list["PromoCode"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )
    plans: Mapped[list["SubscriptionPlan"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )
    bot_messages: Mapped[list["BotMessage"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )
    broadcasts: Mapped[list["ScheduledBroadcast"]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Bot id={self.id} slug={self.slug!r}>"

