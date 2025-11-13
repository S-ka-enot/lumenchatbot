from __future__ import annotations

import logging
from datetime import datetime

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard
from ..services.backend import BackendClient

logger = logging.getLogger(__name__)


async def payments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для просмотра истории платежей."""
    if update.message is None or update.effective_user is None:
        return

    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    if not user_profile:
        await update.message.reply_text(
            "Похоже, ты ещё не зарегистрирован. Используй /start, чтобы начать.",
        )
        return

    try:
        payments = await backend_client.get_user_payments(
            telegram_id=update.effective_user.id,
            bot_id=user_profile.get("bot_id"),
            limit=20,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await update.message.reply_text(
                "Пользователь не найден. Используй /start для регистрации.",
                reply_markup=build_main_menu_keyboard(
                    is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
                ),
            )
            return
        logger.warning("get_user_payments failed: %s", exc)
        await update.message.reply_text(
            "Не удалось получить историю платежей. Попробуй позже.",
            reply_markup=build_main_menu_keyboard(
                is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
            ),
        )
        return
    except httpx.RequestError as exc:
        logger.warning("get_user_payments network error: %s", exc)
        await update.message.reply_text(
            "Не удалось подключиться к сервису. Попробуй позже.",
            reply_markup=build_main_menu_keyboard(
                is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
            ),
        )
        return

    if not payments:
        await update.message.reply_text(
            "📋 У тебя пока нет платежей.\n\n"
            "Используй /buy, чтобы оформить подписку.",
            reply_markup=build_main_menu_keyboard(
                is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
            ),
        )
        return

    # Формируем сообщение с историей платежей
    message_parts = ["📋 История платежей:\n"]
    
    for i, payment in enumerate(payments[:10], 1):  # Показываем максимум 10 платежей
        invoice = payment.get("invoice", f"#{payment.get('id', '?')}")
        amount = payment.get("amount_formatted", payment.get("amount", "0"))
        status_label = payment.get("status_label", payment.get("status", "unknown"))
        status_emoji = _get_status_emoji(payment.get("status", ""))
        
        # Форматируем дату
        created_at = payment.get("created_at")
        date_str = _format_date(created_at) if created_at else "—"
        
        plan_name = payment.get("plan_name")
        plan_text = f" ({plan_name})" if plan_name else ""
        
        message_parts.append(
            f"{i}. {status_emoji} {invoice} — {amount}{plan_text}\n"
            f"   Статус: {status_label}\n"
            f"   Дата: {date_str}"
        )
        
        # Добавляем информацию о подписке, если есть
        if payment.get("has_subscription") and payment.get("subscription_end"):
            sub_end = _format_date(payment.get("subscription_end"))
            message_parts.append(f"   Подписка до: {sub_end}")
        
        message_parts.append("")  # Пустая строка между платежами

    if len(payments) > 10:
        message_parts.append(f"\n... и ещё {len(payments) - 10} платежей")

    await update.message.reply_text(
        "\n".join(message_parts),
        reply_markup=build_main_menu_keyboard(
            is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
        ),
    )


def _get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса платежа."""
    emoji_map = {
        "pending": "⏳",
        "succeeded": "✅",
        "failed": "❌",
        "canceled": "🚫",
    }
    return emoji_map.get(status.lower(), "📄")


def _format_date(date_str: str | None) -> str:
    """Форматирует дату в читаемый вид."""
    if not date_str:
        return "—"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, AttributeError):
        return date_str


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client

