from __future__ import annotations

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    # Отменяем ожидание ввода промокода, если оно было
    context.user_data.pop("waiting_for_promo", None)
    context.user_data.pop("promo_code", None)
    context.user_data.pop("promo_input_plan_id", None)

    is_subscriber = context.user_data.get("subscription", {}).get("is_active", False)
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber)
        if is_subscriber
        else ReplyKeyboardRemove(),
    )
