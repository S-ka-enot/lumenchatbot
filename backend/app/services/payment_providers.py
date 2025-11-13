from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.crypto import decrypt_secret, encrypt_secret
from ..models.payment import PaymentProvider
from ..models.payment_provider_credential import PaymentProviderCredential

logger = logging.getLogger(__name__)


class PaymentProviderSettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._schema_initialized = False

    async def _ensure_schema(self) -> None:
        if self._schema_initialized:
            return

        def _create_table(sync_connection) -> None:  # pragma: no cover
            bind = getattr(sync_connection, "get_bind", None)
            engine = bind() if callable(bind) else sync_connection
            PaymentProviderCredential.__table__.create(bind=engine, checkfirst=True)

        await self.session.run_sync(_create_table)
        self._schema_initialized = True

    async def _get_by_provider(
        self, provider: PaymentProvider
    ) -> PaymentProviderCredential | None:
        await self._ensure_schema()
        stmt = (
            select(PaymentProviderCredential)
            .where(PaymentProviderCredential.provider == provider)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_yookassa_settings(self) -> tuple[str | None, bool]:
        record = await self._get_by_provider(PaymentProvider.YOOKASSA)
        if record is None:
            return None, False
        return record.shop_id, bool(record.api_key_encrypted)

    async def get_yookassa_credentials(self) -> tuple[str, str]:
        record = await self._get_by_provider(PaymentProvider.YOOKASSA)
        if record is None or not record.api_key_encrypted:
            raise RuntimeError("Настройки YooKassa не сконфигурированы")
        api_key = decrypt_secret(record.api_key_encrypted)
        if api_key is None:
            raise RuntimeError("Не удалось расшифровать ключ YooKassa")
        return record.shop_id, api_key

    async def upsert_yookassa_settings(
        self, *, shop_id: str, api_key: str | None
    ) -> tuple[str, bool]:
        record = await self._get_by_provider(PaymentProvider.YOOKASSA)
        if record is None:
            record = PaymentProviderCredential(
                bot_id=None,  # Глобальные настройки для всех ботов
                provider=PaymentProvider.YOOKASSA,
                shop_id=shop_id,
                api_key_encrypted=encrypt_secret(api_key) if api_key else None,
            )
        else:
            record.shop_id = shop_id
            if api_key:
                record.api_key_encrypted = encrypt_secret(api_key)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        logger.info(
            "Обновлены настройки YooKassa",
            extra={
                "shop_id": shop_id,
                "api_key_updated": bool(api_key),
            },
        )
        return record.shop_id, bool(record.api_key_encrypted)
