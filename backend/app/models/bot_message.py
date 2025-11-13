from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class BotMessage(TimestampMixin, Base):
    __tablename__ = "bot_messages"
    __table_args__ = (
        UniqueConstraint("bot_id", "message_key", name="uq_bot_messages_bot_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    message_key: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    bot = relationship("Bot", back_populates="bot_messages")

    def __repr__(self) -> str:
        return f"<BotMessage key={self.message_key!r} bot_id={self.bot_id}>"

