from __future__ import annotations

import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard
from ..services.backend import BackendClient

logger = logging.getLogger(__name__)


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для отмены автопродления подписки."""
    if update.message is None or update.effective_user is None:
        return

    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    
    if not user_profile:
        await update.message.reply_text(
            "👋 Похоже, ты ещё не зарегистрирован.\n\n"
            "Используй команду /start, чтобы начать.",
        )
        return

    # Проверяем статус подписки
    try:
        status_data = await backend_client.get_subscription_status(
            telegram_id=update.effective_user.id,
        )
    except httpx.RequestError as exc:
        logger.warning("get_subscription_status error: %s", exc)
        await update.message.reply_text(
            "😔 Не удалось получить статус подписки.\n\n"
            "Попробуй позже или свяжись с поддержкой.",
        )
        return
    except httpx.HTTPStatusError as exc:
        logger.warning("get_subscription_status failed: %s", exc)
        await update.message.reply_text(
            "😔 Не удалось получить статус подписки.\n\n"
            "Попробуй позже или свяжись с поддержкой.",
        )
        return

    is_active = status_data.get("is_active", False)
    auto_renew = status_data.get("auto_renew", False)

    if not is_active:
        await update.message.reply_text(
            "❌ У тебя нет активной подписки.\n\n"
            "Используй команду /buy, чтобы оформить подписку.",
            reply_markup=build_main_menu_keyboard(is_subscriber=False),
        )
        return

    if not auto_renew:
        await update.message.reply_text(
            "ℹ️ Автопродление подписки уже отключено.\n\n"
            "Твоя подписка не будет автоматически продлеваться после окончания срока действия.",
            reply_markup=build_main_menu_keyboard(is_subscriber=True),
        )
        return

    # Отменяем автопродление
    try:
        result = await backend_client.cancel_auto_renew(
            telegram_id=update.effective_user.id,
            bot_id=user_profile.get("bot_id"),
        )
        
        # Обновляем статус подписки в кэше
        status_data["auto_renew"] = False
        context.user_data["subscription"] = status_data
        
        message = (
            "✅ Автопродление подписки отменено!\n\n"
            "Твоя подписка не будет автоматически продлеваться после окончания срока действия.\n\n"
            "Ты можешь продлить подписку вручную командой /buy в любое время."
        )
        
        await update.message.reply_text(
            message,
            reply_markup=build_main_menu_keyboard(is_subscriber=True),
        )
    except httpx.HTTPStatusError as exc:
        logger.warning("cancel_auto_renew failed: %s", exc)
        if exc.response.status_code == 404:
            await update.message.reply_text(
                "❌ Активная подписка не найдена.\n\n"
                "Возможно, подписка уже истекла или была отменена.",
                reply_markup=build_main_menu_keyboard(is_subscriber=False),
            )
        else:
            await update.message.reply_text(
                "😔 Не удалось отменить автопродление подписки.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
                reply_markup=build_main_menu_keyboard(is_subscriber=True),
            )
    except httpx.RequestError as exc:
        logger.warning("cancel_auto_renew network error: %s", exc)
        await update.message.reply_text(
            "🌐 Не удалось подключиться к серверу.\n\n"
            "Проверь интернет-соединение и попробуй позже.",
            reply_markup=build_main_menu_keyboard(is_subscriber=True),
        )


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client

