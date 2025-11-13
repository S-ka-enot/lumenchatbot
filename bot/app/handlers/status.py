from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard
from ..services.backend import BackendClient

logger = logging.getLogger(__name__)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    backend_client = _get_backend_client(context)

    try:
        status_data = await backend_client.get_subscription_status(
            telegram_id=update.effective_user.id,
        )
    except httpx.RequestError as exc:
        logger.warning("get_subscription_status error: %s", exc)
        await update.message.reply_text(
            "Не удалось получить статус подписки. Попробуй позже.",
        )
        return
    except httpx.HTTPStatusError as exc:
        logger.warning("get_subscription_status failed: %s", exc)
        await update.message.reply_text(
            "Не удалось получить статус подписки. Попробуй позже.",
        )
        return

    context.user_data["subscription"] = status_data
    message = _format_status_message(status_data)
    is_subscriber = status_data.get("is_active", False)
    await update.message.reply_text(
        message,
        reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
    )


def _format_status_message(status_data: dict) -> str:
    if status_data.get("status") in {"not_found", "inactive"}:
        return (
            "📊 Статус подписки:\n\n"
            "❌ Подписка не активна\n\n"
            "Чтобы получить доступ к закрытым каналам, оформи подписку.\n"
            "Используй команду /buy или кнопку «Купить подписку»."
        )

    end_date_raw = status_data.get("subscription_end")
    days_left = status_data.get("days_left")
    auto_renew = status_data.get("auto_renew", False)
    channels = status_data.get("channels", [])
    plan = status_data.get("plan")

    try:
        end_date = (
            datetime.fromisoformat(end_date_raw).strftime("%d.%m.%Y")
            if end_date_raw
            else "—"
        )
    except ValueError:
        end_date = "—"

    channels_list = "\n".join(
        f"• {ch.get('channel_name') or ch.get('name') or 'Канал'}" for ch in channels
    ) or "—"
    days_label = f"{days_left} дн." if days_left is not None else "—"
    if plan:
        plan_name = plan.get("name", "—")
        price_label = _format_price(plan.get("price_amount"), plan.get("price_currency"))
        duration_label = f"{plan.get('duration_days')} дн." if plan.get("duration_days") else "—"
        description = plan.get("description")
    else:
        plan_name = "Не определён"
        price_label = "—"
        duration_label = "—"
        description = None

    # Определяем статус подписки
    if days_left is not None and days_left <= 0:
        status_emoji = "❌"
        status_text = "Подписка истекла"
    elif days_left is not None and days_left <= 3:
        status_emoji = "⚠️"
        status_text = "Подписка скоро истечёт"
    else:
        status_emoji = "✅"
        status_text = "Подписка активна"
    
    lines = [
        "📊 Статус подписки:\n",
        f"{status_emoji} {status_text}\n",
        f"📦 Тариф: {plan_name}",
        f"💰 Стоимость: {price_label} за {duration_label}",
        f"📅 Активна до: {end_date}",
        f"⏰ Осталось дней: {days_label}",
    ]
    
    if description:
        lines.insert(4, f"📝 Описание: {description}")
    
    # Информация об автопродлении
    if auto_renew:
        lines.append("🔄 Автопродление: включено")
    else:
        lines.append("🔄 Автопродление: отключено")
    
    lines.append(f"\n📚 Доступные каналы:\n{channels_list}")
    
    if days_left is not None and days_left <= 7:
        if auto_renew:
            lines.append("\n💡 Подписка будет автоматически продлена после окончания срока действия.")
        else:
            lines.append("\n💡 Совет: Не забудь продлить подписку, чтобы не потерять доступ!")
    
    if auto_renew:
        lines.append("\n💡 Используй команду /unsubscribe, чтобы отменить автопродление.")
    
    return "\n".join(lines)


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client


def _format_price(value: str | Decimal | None, currency: str | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        amount = value
    else:
        amount = Decimal(str(value))
    code = currency or "RUB"
    return f"{amount:,.2f} {code}".replace(",", " ")

