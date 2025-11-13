from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .bot import Bot
    from .channel import Channel


class BroadcastStatus(str, enum.Enum):
    PENDING = "pending"
    SENDING = "sending"
    COMPLETED = "completed"
    CANCELED = "canceled"
    DRAFT = "draft"


class BroadcastAudience(str, enum.Enum):
    ALL = "all"
    SUBSCRIBERS = "subscribers"
    ACTIVE_SUBSCRIBERS = "active_subscribers"
    EXPIRED_SUBSCRIBERS = "expired_subscribers"
    EXPIRING_SOON = "expiring_soon"
    NON_SUBSCRIBERS = "non_subscribers"
    BIRTHDAY = "birthday"
    CUSTOM = "custom"  # Для выбора отдельных пользователей


class ParseMode(str, enum.Enum):
    HTML = "HTML"
    MARKDOWN = "Markdown"
    MARKDOWN_V2 = "MarkdownV2"
    NONE = "None"


class ScheduledBroadcast(TimestampMixin, Base):
    __tablename__ = "scheduled_broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("channels.id", ondelete="SET NULL"), nullable=True
    )
    message_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    parse_mode: Mapped[ParseMode | None] = mapped_column(
        Enum(ParseMode, name="broadcast_parse_mode", native_enum=False),
        nullable=True,
        default=ParseMode.NONE,
    )
    target_audience: Mapped[BroadcastAudience] = mapped_column(
        Enum(BroadcastAudience, name="broadcast_audience", native_enum=False), nullable=False
    )
    user_ids: Mapped[list[int] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, default=list
    )  # Для выбора отдельных пользователей
    birthday_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    media_files: Mapped[list[dict] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, default=list
    )  # Массив объектов с type, file_id, caption и т.д.
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, name="broadcast_status", native_enum=False),
        default=BroadcastStatus.DRAFT,
        nullable=False,
    )
    stats: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict
    )
    buttons: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict
    )

    bot: Mapped["Bot"] = relationship(back_populates="broadcasts")
    channel: Mapped["Channel | None"] = relationship(back_populates="broadcasts")

    def __repr__(self) -> str:
        return f"<ScheduledBroadcast id={self.id} status={self.status}>"

