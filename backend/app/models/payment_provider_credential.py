from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from .payment import PaymentProvider


class PaymentProviderCredential(TimestampMixin, Base):
    __tablename__ = "payment_provider_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=True)
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider), nullable=False, unique=True
    )
    shop_id: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - отладочный вывод
        return f"<PaymentProviderCredential provider={self.provider} shop_id={self.shop_id}>"
