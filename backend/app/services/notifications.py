from __future__ import annotations

import logging

import httpx

from ..core.config import settings

logger = logging.getLogger("lumenpay.notifications")


async def send_admin_message(text: str) -> None:
    if not settings.backup_send_to_telegram:
        return
    if not settings.telegram_bot_token or not settings.backup_admin_chat_id:
        logger.debug("Админский чат или токен не настроены, уведомление пропущено")
        return

    token = settings.telegram_bot_token.get_secret_value()
    chat_id = settings.backup_admin_chat_id
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text})
        except httpx.HTTPError as exc:  # pragma: no cover - внешние ошибки
            logger.warning("Не удалось отправить уведомление администратору: %s", exc)
