from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from telegram import Bot
from telegram.error import TelegramError

from ..services.backend import BackendClient

logger = logging.getLogger(__name__)


async def send_subscription_reminders(
    bot: Bot, backend_client: BackendClient, bot_id: int | None = None
) -> None:
    """Отправляет напоминания пользователям об истекающих подписках."""
    try:
        # Получаем пользователей с подписками, истекающими через 3 дня
        expiring_3d = await backend_client.get_expiring_subscriptions(
            bot_id=bot_id, days_ahead=3
        )
        # Получаем пользователей с подписками, истекающими через 1 день
        expiring_1d = await backend_client.get_expiring_subscriptions(
            bot_id=bot_id, days_ahead=1
        )
        
        # Отправляем напоминания за 3 дня
        for user_data in expiring_3d:
            if user_data["days_left"] == 3:
                await _send_reminder(bot, user_data, days_left=3)
        
        # Отправляем напоминания за 1 день
        for user_data in expiring_1d:
            if user_data["days_left"] == 1:
                await _send_reminder(bot, user_data, days_left=1)
                
    except httpx.RequestError as exc:
        logger.warning("Ошибка сети при получении истекающих подписок: %s", exc)
    except httpx.HTTPStatusError as exc:
        logger.warning("Ошибка HTTP при получении истекающих подписок: %s", exc)
    except Exception as exc:
        logger.exception("Неожиданная ошибка при отправке напоминаний: %s", exc)


async def _send_reminder(bot: Bot, user_data: dict, days_left: int) -> None:
    """Отправляет напоминание конкретному пользователю."""
    telegram_id = user_data["telegram_id"]
    first_name = user_data.get("first_name") or "Пользователь"
    
    try:
        if days_left == 3:
            message = (
                f"👋 Привет, {first_name}!\n\n"
                f"⏰ Твоя подписка истечёт через 3 дня.\n\n"
                f"💡 Чтобы не потерять доступ к закрытым каналам, продли подписку командой /buy\n\n"
                f"💳 Используй промокод командой /promo для получения скидки!"
            )
        elif days_left == 1:
            message = (
                f"⚠️ Внимание, {first_name}!\n\n"
                f"⏰ Твоя подписка истечёт завтра!\n\n"
                f"💡 Продли подписку командой /buy, чтобы сохранить доступ к закрытым каналам.\n\n"
                f"💳 Не забудь использовать промокод командой /promo для скидки!"
            )
        else:
            return
        
        await bot.send_message(chat_id=telegram_id, text=message)
        logger.info(
            "Отправлено напоминание пользователю %s (дней осталось: %d)",
            telegram_id,
            days_left,
        )
    except TelegramError as exc:
        logger.warning(
            "Не удалось отправить напоминание пользователю %s: %s",
            telegram_id,
            exc,
        )


async def remove_expired_users_from_channels(
    bot: Bot, backend_client: BackendClient, bot_id: int | None = None
) -> None:
    """Удаляет пользователей с истекшими подписками из каналов."""
    try:
        # Получаем пользователей с истекшими подписками за последние 24 часа
        expired_users = await backend_client.get_expired_subscriptions(
            bot_id=bot_id, hours_ago=24
        )
        
        removed_count = 0
        error_count = 0
        
        for user_data in expired_users:
            telegram_id = user_data["telegram_id"]
            channels = user_data.get("channels", [])
            
            # Проверяем текущий статус подписки
            try:
                status = await backend_client.get_subscription_status(telegram_id=telegram_id)
                if status.get("is_active", False):
                    # Подписка всё ещё активна, пропускаем
                    continue
            except Exception as exc:
                logger.warning(
                    "Ошибка при проверке статуса подписки для пользователя %s: %s",
                    telegram_id,
                    exc,
                )
                continue
            
            # Удаляем пользователя из всех каналов плана
            for channel in channels:
                channel_id = channel.get("channel_id")
                if not channel_id:
                    continue
                
                try:
                    await _remove_user_from_channel(bot, telegram_id, channel_id)
                    removed_count += 1
                    logger.info(
                        "Пользователь %s удалён из канала %s",
                        telegram_id,
                        channel.get("channel_name", channel_id),
                    )
                except Exception as exc:
                    error_count += 1
                    logger.warning(
                        "Ошибка при удалении пользователя %s из канала %s: %s",
                        telegram_id,
                        channel_id,
                        exc,
                    )
            
            # Отправляем уведомление пользователю
            try:
                first_name = user_data.get("first_name") or "Пользователь"
                message = (
                    f"👋 Привет, {first_name}!\n\n"
                    f"❌ Твоя подписка истекла.\n\n"
                    f"💡 Чтобы восстановить доступ к закрытым каналам, оформи новую подписку командой /buy\n\n"
                    f"💳 Используй промокод командой /promo для получения скидки!"
                )
                await bot.send_message(chat_id=telegram_id, text=message)
            except TelegramError as exc:
                logger.warning(
                    "Не удалось отправить уведомление пользователю %s: %s",
                    telegram_id,
                    exc,
                )
        
        if removed_count > 0 or error_count > 0:
            logger.info(
                "Обработка истекших подписок завершена: удалено %d, ошибок %d",
                removed_count,
                error_count,
            )
                
    except httpx.RequestError as exc:
        logger.warning("Ошибка сети при получении истекших подписок: %s", exc)
    except httpx.HTTPStatusError as exc:
        logger.warning("Ошибка HTTP при получении истекших подписок: %s", exc)
    except Exception as exc:
        logger.exception("Неожиданная ошибка при удалении пользователей из каналов: %s", exc)


async def _remove_user_from_channel(bot: Bot, telegram_id: int, channel_id: str) -> None:
    """Удаляет пользователя из канала."""
    try:
        # Преобразуем channel_id в int, если это строка с числом
        chat_id = channel_id
        if isinstance(chat_id, str):
            stripped = chat_id.strip()
            if stripped.lstrip("-").isdigit():
                chat_id = int(stripped)
        
        # Используем ban_chat_member для удаления пользователя
        # until_date=None означает постоянный бан, но мы можем разбанить позже
        await bot.ban_chat_member(chat_id=chat_id, user_id=telegram_id, until_date=None)
        
        # Сразу разбаниваем, чтобы пользователь мог присоединиться снова при продлении подписки
        # Это удалит пользователя из канала, но не заблокирует его навсегда
        await asyncio.sleep(1)  # Небольшая задержка
        await bot.unban_chat_member(chat_id=chat_id, user_id=telegram_id, only_if_banned=True)
        
    except TelegramError as exc:
        # Если пользователь уже не в канале или бот не имеет прав администратора, это нормально
        if "user not found" in str(exc).lower() or "not enough rights" in str(exc).lower():
            logger.debug(
                "Не удалось удалить пользователя %s из канала %s: %s",
                telegram_id,
                channel_id,
                exc,
            )
        else:
            raise

