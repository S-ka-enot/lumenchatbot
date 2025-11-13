from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    text = (
        "📖 Справка по командам:\n\n"
        "🔹 /start — регистрация и главное меню\n"
        "🔹 /buy — оформить или продлить подписку\n"
        "🔹 /promo — ввести промокод для скидки\n"
        "🔹 /payments — история платежей\n"
        "🔹 /status — узнать статус подписки\n"
        "🔹 /channels — список доступных каналов\n"
        "🔹 /unsubscribe — отменить автопродление подписки\n"
        "🔹 /cancel — отменить текущее действие\n"
        "🔹 /help — показать эту справку\n\n"
        "💡 Также ты можешь использовать кнопки главного меню для быстрого доступа к функциям."
    )
    is_subscriber = context.user_data.get("subscription", {}).get("is_active", False)
    await update.message.reply_text(
        text,
        reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
    )
