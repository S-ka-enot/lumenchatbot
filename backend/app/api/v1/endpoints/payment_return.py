from __future__ import annotations

import httpx
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_db
from ....core.crypto import decrypt_secret
from ....models.bot import Bot
from ....models.payment import Payment

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_bot_username(bot: Bot) -> str:
    """Получает username бота из токена через Telegram API."""
    token = None
    
    # Сначала пробуем получить username из токена бота в базе данных
    if bot.telegram_bot_token_encrypted:
        try:
            encrypted_str = bot.telegram_bot_token_encrypted.decode() if isinstance(bot.telegram_bot_token_encrypted, bytes) else bot.telegram_bot_token_encrypted
            token = decrypt_secret(encrypted_str)
        except Exception as exc:
            logger.debug("Не удалось расшифровать токен бота из БД: %s", exc)
    
    # Если не удалось расшифровать, пробуем использовать токен из настроек
    if not token:
        try:
            from backend.app.core.config import settings
            if settings.telegram_bot_token:
                token = settings.telegram_bot_token.get_secret_value()
        except Exception:
            pass
    
    # Получаем username через Telegram API
    if token:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok") and data.get("result", {}).get("username"):
                        username = data["result"]["username"]
                        logger.info("Получен username бота из Telegram API: %s", username)
                        return username
        except Exception as exc:
            logger.debug("Не удалось получить username бота из Telegram API: %s", exc)
    
    # Если не удалось получить username, используем известный username или slug как fallback
    # Для бота с slug "lumenpay" используем известный username
    if bot.slug == "lumenpay":
        return "LumenPayChat_bot"
    
    return bot.slug


@router.get("/payments/return", summary="Возврат после оплаты YooKassa")
async def payment_return(
    orderId: str | None = Query(default=None, alias="orderId"),
    payment_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Обрабатывает возврат пользователя после оплаты в YooKassa.
    Перенаправляет в Telegram бота через deep link.
    """
    # Ищем платеж по external_id (orderId от YooKassa) или по payment_id
    if orderId:
        stmt = select(Payment).where(Payment.external_id == orderId).limit(1)
    elif payment_id:
        stmt = select(Payment).where(Payment.id == payment_id).limit(1)
    else:
        # Если нет параметров, перенаправляем в бота без параметров
        stmt = select(Bot).limit(1)
        result = await session.execute(stmt)
        bot = result.scalar_one_or_none()
        if bot:
            bot_username = await _get_bot_username(bot)
            return RedirectResponse(
                url=f"https://t.me/{bot_username}?start=payment_return",
                status_code=status.HTTP_302_FOUND,
            )
        return RedirectResponse(
            url="https://t.me/lumenpay?start=payment_return",
            status_code=status.HTTP_302_FOUND,
        )

    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        # Если платеж не найден, все равно перенаправляем в бота
        stmt = select(Bot).where(Bot.id == 1).limit(1)
        result = await session.execute(stmt)
        bot = result.scalar_one_or_none()
        if bot:
            bot_username = await _get_bot_username(bot)
        else:
            bot_username = "lumenpay"
        return RedirectResponse(
            url=f"https://t.me/{bot_username}?start=payment_return",
            status_code=status.HTTP_302_FOUND,
        )

    # Получаем бота для создания deep link
    stmt = select(Bot).where(Bot.id == payment.bot_id).limit(1)
    result = await session.execute(stmt)
    bot = result.scalar_one_or_none()
    if bot:
        bot_username = await _get_bot_username(bot)
    else:
        bot_username = "lumenpay"

    # Создаем deep link для возврата в бота
    # Используем payment_id для идентификации платежа
    deep_link = f"https://t.me/{bot_username}?start=payment_{payment.id}"

    return RedirectResponse(url=deep_link, status_code=status.HTTP_302_FOUND)


@router.get("/payments/success", summary="Успешная оплата")
async def payment_success(
    orderId: str | None = Query(default=None, alias="orderId"),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Перенаправляет на страницу успешной оплаты или в бота."""
    return await payment_return(orderId=orderId, session=session)


@router.get("/payments/failure", summary="Неудачная оплата")
async def payment_failure(
    orderId: str | None = Query(default=None, alias="orderId"),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Перенаправляет на страницу неудачной оплаты или в бота."""
    return await payment_return(orderId=orderId, session=session)

