from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.crypto import decrypt_secret
from ..models.bot import Bot
from ..models.subscription import Subscription
from ..models.user import User

logger = logging.getLogger(__name__)


class UserNotificationService:
    """Сервис для отправки уведомлений пользователям через Telegram Bot API."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def send_message(
        self,
        telegram_id: int,
        text: str,
        bot_id: int | None = None,
        parse_mode: str | None = None,
    ) -> bool:
        """
        Отправляет сообщение пользователю через Telegram Bot API.
        
        Returns:
            bool: True если сообщение отправлено успешно, False в противном случае
        """
        # Получаем бота
        if bot_id is None:
            # Если bot_id не указан, пытаемся найти пользователя и получить его bot_id
            user = await self._get_user_by_telegram(telegram_id)
            if user is None:
                logger.warning("Пользователь с telegram_id=%s не найден", telegram_id)
                return False
            bot_id = user.bot_id

        bot = await self.session.get(Bot, bot_id)
        if bot is None:
            logger.warning("Бот с id=%s не найден", bot_id)
            return False

        # Расшифровываем токен бота
        if not bot.telegram_bot_token_encrypted:
            logger.warning("Токен бота %s не настроен", bot_id)
            return False

        try:
            # telegram_bot_token_encrypted это bytes, нужно декодировать в строку перед расшифровкой
            encrypted_str = bot.telegram_bot_token_encrypted.decode() if isinstance(bot.telegram_bot_token_encrypted, bytes) else bot.telegram_bot_token_encrypted
            token = decrypt_secret(encrypted_str)
            if not token:
                logger.warning("Не удалось расшифровать токен бота %s", bot_id)
                return False
        except Exception as exc:
            logger.warning("Ошибка при расшифровке токена бота %s: %s", bot_id, exc)
            return False

        # Отправляем сообщение через Telegram Bot API
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": telegram_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(
                    "Уведомление отправлено пользователю",
                    extra={
                        "telegram_id": telegram_id,
                        "bot_id": bot_id,
                    },
                )
                return True
            except httpx.HTTPStatusError as exc:
                # Если пользователь заблокировал бота или чат не найден - это нормально
                if exc.response.status_code == 403:
                    logger.debug(
                        "Пользователь %s заблокировал бота или чат недоступен",
                        telegram_id,
                    )
                elif exc.response.status_code == 400:
                    logger.warning(
                        "Ошибка при отправке уведомления пользователю %s: %s",
                        telegram_id,
                        exc.response.text,
                    )
                else:
                    logger.warning(
                        "HTTP ошибка при отправке уведомления пользователю %s: %s",
                        telegram_id,
                        exc,
                    )
                return False
            except httpx.RequestError as exc:
                logger.warning(
                    "Ошибка сети при отправке уведомления пользователю %s: %s",
                    telegram_id,
                    exc,
                )
                return False

    async def send_payment_success_notification(
        self,
        user: User,
        payment_id: int,
        amount: str,
        plan_name: str | None = None,
        subscription_end: datetime | None = None,
    ) -> bool:
        """Отправляет уведомление об успешной оплате."""
        message_parts = [
            "✅ Платёж успешно обработан!",
            "",
            f"💰 Сумма: {amount}",
        ]
        
        if plan_name:
            message_parts.append(f"📦 Тариф: {plan_name}")
        
        if subscription_end:
            end_date_str = subscription_end.strftime("%d.%m.%Y")
            days_left = (subscription_end - datetime.now(timezone.utc)).days
            message_parts.append(f"📅 Подписка активна до: {end_date_str}")
            if days_left > 0:
                message_parts.append(f"⏰ Осталось дней: {days_left}")
        
        message_parts.extend([
            "",
            "🎉 Спасибо за покупку! Теперь у тебя есть доступ ко всем закрытым каналам.",
            "",
            "Используй /channels, чтобы увидеть список доступных каналов.",
        ])
        
        return await self.send_message(
            telegram_id=user.telegram_id,
            text="\n".join(message_parts),
            bot_id=user.bot_id,
        )

    async def send_subscription_expiring_notification(
        self,
        user: User,
        days_left: int,
        subscription_end: datetime,
    ) -> bool:
        """Отправляет напоминание об истечении подписки."""
        end_date_str = subscription_end.strftime("%d.%m.%Y")
        
        if days_left == 1:
            emoji = "⏰"
            urgency = "завтра"
            message = (
                f"{emoji} Напоминание: твоя подписка истекает {urgency} ({end_date_str})!\n\n"
                "Чтобы не потерять доступ к закрытым каналам, продли подписку прямо сейчас.\n\n"
                "Используй /buy для продления."
            )
        elif days_left <= 3:
            emoji = "⚠️"
            message = (
                f"{emoji} Напоминание: твоя подписка истекает через {days_left} дня ({end_date_str}).\n\n"
                "Не забудь продлить подписку, чтобы сохранить доступ ко всем каналам.\n\n"
                "Используй /buy для продления."
            )
        else:
            emoji = "📅"
            message = (
                f"{emoji} Напоминание: твоя подписка истекает через {days_left} дней ({end_date_str}).\n\n"
                "Не забудь продлить подписку, чтобы сохранить доступ ко всем каналам.\n\n"
                "Используй /buy для продления."
            )
        
        return await self.send_message(
            telegram_id=user.telegram_id,
            text=message,
            bot_id=user.bot_id,
        )

    async def send_subscription_expired_notification(
        self,
        user: User,
    ) -> bool:
        """Отправляет уведомление об истечении подписки."""
        message = (
            "⏰ Твоя подписка истекла.\n\n"
            "Чтобы восстановить доступ к закрытым каналам, оформи новую подписку.\n\n"
            "Используй /buy для оформления подписки."
        )
        
        return await self.send_message(
            telegram_id=user.telegram_id,
            text=message,
            bot_id=user.bot_id,
        )

    async def _get_user_by_telegram(self, telegram_id: int) -> User | None:
        """Получает пользователя по Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

