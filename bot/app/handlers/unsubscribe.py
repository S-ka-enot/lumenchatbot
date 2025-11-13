from __future__ import annotations

import logging

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

    # Предлагаем выбор: отменить автопродление или полностью отменить подписку
    keyboard = [
        [
            InlineKeyboardButton("❌ Отменить автопродление", callback_data="cancel_auto_renew"),
        ],
        [
            InlineKeyboardButton("🚫 Полностью отменить подписку", callback_data="cancel_subscription_full"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🔔 Управление подпиской\n\n"
        "Выбери действие:\n\n"
        "❌ Отменить автопродление — подписка останется активной до окончания срока, но не будет продлеваться автоматически.\n\n"
        "🚫 Полностью отменить подписку — подписка будет деактивирована немедленно, доступ к каналам будет закрыт."
    )
    
    if not auto_renew:
        message += "\n\nℹ️ Автопродление уже отключено."
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
    )


async def handle_cancel_auto_renew_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для отмены автопродления подписки."""
    if update.callback_query is None or update.effective_user is None:
        return
    
    await update.callback_query.answer()
    
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    
    if not user_profile:
        await update.callback_query.edit_message_text(
            "👋 Похоже, ты ещё не зарегистрирован.\n\n"
            "Используй команду /start, чтобы начать.",
        )
        return
    
    try:
        result = await backend_client.cancel_auto_renew(
            telegram_id=update.effective_user.id,
            bot_id=user_profile.get("bot_id"),
        )
        
        # Обновляем статус подписки в кэше
        status_data = context.user_data.get("subscription", {})
        status_data["auto_renew"] = False
        context.user_data["subscription"] = status_data
        
        message = (
            "✅ Автопродление подписки отменено!\n\n"
            "Твоя подписка не будет автоматически продлеваться после окончания срока действия.\n\n"
            "Ты можешь продлить подписку вручную командой /buy в любое время."
        )
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=None,
        )
    except httpx.HTTPStatusError as exc:
        logger.warning("cancel_auto_renew failed: %s", exc)
        if exc.response.status_code == 404:
            await update.callback_query.edit_message_text(
                "❌ Активная подписка не найдена.\n\n"
                "Возможно, подписка уже истекла или была отменена.",
            )
        else:
            await update.callback_query.edit_message_text(
                "😔 Не удалось отменить автопродление подписки.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
            )
    except httpx.RequestError as exc:
        logger.warning("cancel_auto_renew network error: %s", exc)
        await update.callback_query.edit_message_text(
            "🌐 Не удалось подключиться к серверу.\n\n"
            "Проверь интернет-соединение и попробуй позже.",
        )


async def handle_cancel_subscription_full_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для полной отмены подписки."""
    if update.callback_query is None or update.effective_user is None:
        return
    
    await update.callback_query.answer()
    
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    
    if not user_profile:
        await update.callback_query.edit_message_text(
            "👋 Похоже, ты ещё не зарегистрирован.\n\n"
            "Используй команду /start, чтобы начать.",
        )
        return
    
    # Подтверждение перед полной отменой
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, отменить подписку", callback_data="confirm_cancel_subscription"),
        ],
        [
            InlineKeyboardButton("❌ Нет, оставить подписку", callback_data="cancel_cancel_subscription"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "⚠️ Внимание!\n\n"
        "Ты собираешься полностью отменить подписку.\n\n"
        "Это действие:\n"
        "• Немедленно деактивирует твою подписку\n"
        "• Закроет доступ ко всем закрытым каналам\n"
        "• Удалит тебя из каналов\n\n"
        "Подтверди отмену подписки:"
    )
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
    )


async def handle_confirm_cancel_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для подтверждения полной отмены подписки."""
    if update.callback_query is None or update.effective_user is None:
        return
    
    await update.callback_query.answer()
    
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    
    if not user_profile:
        await update.callback_query.edit_message_text(
            "👋 Похоже, ты ещё не зарегистрирован.\n\n"
            "Используй команду /start, чтобы начать.",
        )
        return
    
    try:
        result = await backend_client.cancel_subscription(
            telegram_id=update.effective_user.id,
            bot_id=user_profile.get("bot_id"),
        )
        
        channels_removed = result.get("channels_removed", 0)
        
        # Обновляем статус подписки в кэше
        status_data = context.user_data.get("subscription", {})
        status_data["is_active"] = False
        status_data["auto_renew"] = False
        context.user_data["subscription"] = status_data
        
        message = (
            "✅ Подписка полностью отменена!\n\n"
            f"Ты удален из {channels_removed} каналов.\n\n"
            "Доступ к закрытым каналам закрыт.\n\n"
            "Ты можешь оформить новую подписку командой /buy в любое время."
        )
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=None,
        )
        
        # Обновляем клавиатуру
        await update.callback_query.message.reply_text(
            "Используй /buy для оформления новой подписки.",
            reply_markup=build_main_menu_keyboard(is_subscriber=False),
        )
    except httpx.HTTPStatusError as exc:
        logger.warning("cancel_subscription failed: %s", exc)
        if exc.response.status_code == 404:
            await update.callback_query.edit_message_text(
                "❌ Активная подписка не найдена.\n\n"
                "Возможно, подписка уже истекла или была отменена.",
            )
        else:
            await update.callback_query.edit_message_text(
                "😔 Не удалось отменить подписку.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
            )
    except httpx.RequestError as exc:
        logger.warning("cancel_subscription network error: %s", exc)
        await update.callback_query.edit_message_text(
            "🌐 Не удалось подключиться к серверу.\n\n"
            "Проверь интернет-соединение и попробуй позже.",
        )


async def handle_cancel_cancel_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для отмены действия отмены подписки."""
    if update.callback_query is None:
        return
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "✅ Действие отменено. Твоя подписка остается активной.",
        reply_markup=None,
    )


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client

