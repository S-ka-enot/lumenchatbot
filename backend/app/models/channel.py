from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin
from .subscription_plan import subscription_plan_channels

if TYPE_CHECKING:
    from .access_log import AccessLog
    from .bot import Bot
    from .scheduled_broadcast import ScheduledBroadcast
    from .subscription_plan import SubscriptionPlan


class Channel(TimestampMixin, Base):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("bot_id", "channel_id", name="uq_channels_bot_channel_id"),
        UniqueConstraint("bot_id", "channel_username", name="uq_channels_bot_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(64), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_username: Mapped[str | None] = mapped_column(String(255))
    invite_link: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_subscription: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    member_count: Mapped[int | None] = mapped_column(Integer)

    bot: Mapped["Bot"] = relationship(back_populates="channels")
    access_logs: Mapped[list["AccessLog"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )
    plans: Mapped[list["SubscriptionPlan"]] = relationship(
        secondary="subscription_plan_channels",
        back_populates="channels",
    )
    plans = relationship(
        "SubscriptionPlan",
        secondary=subscription_plan_channels,
        back_populates="channels",
    )
    broadcasts: Mapped[list["ScheduledBroadcast"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Channel id={self.id} name={self.channel_name!r}>"

