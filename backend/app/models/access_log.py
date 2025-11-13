from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

if TYPE_CHECKING:
    from .bot import Bot
    from .channel import Channel
    from .user import User


class AccessAction(str, enum.Enum):
    JOIN = "join"
    KICK = "kick"
    CHECK = "check"


class AccessResult(str, enum.Enum):
    SUCCESS = "success"
    DENIED = "denied"


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[AccessAction] = mapped_column(Enum(AccessAction), nullable=False)
    has_subscription: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    result: Mapped[AccessResult] = mapped_column(Enum(AccessResult), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    bot: Mapped["Bot"] = relationship()
    user: Mapped["User"] = relationship(back_populates="access_logs")
    channel: Mapped["Channel"] = relationship(back_populates="access_logs")

    def __repr__(self) -> str:
        return f"<AccessLog id={self.id} user_id={self.user_id} action={self.action}>"

