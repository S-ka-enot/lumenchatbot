from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
    message, inline_keyboard = _format_status_message(status_data)
    is_subscriber = status_data.get("is_active", False)
    
    # Создаем inline клавиатуру для каналов, если они есть
    reply_markup = None
    if inline_keyboard:
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        logger.info("Created inline keyboard with %d buttons", len(inline_keyboard))
    else:
        logger.warning("No inline keyboard created - channels: %s", status_data.get("channels", []))
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
    )
    
    # Отправляем основную клавиатуру отдельным сообщением
    await update.message.reply_text(
        "💡 Используй кнопки выше для перехода в каналы." if inline_keyboard else "💡 Используй команду /channels для просмотра каналов.",
        reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
    )


def _format_status_message(status_data: dict) -> tuple[str, list[list[InlineKeyboardButton]] | None]:
    """
    Форматирует сообщение со статусом подписки.
    
    Returns:
        tuple: (текст сообщения, список кнопок для каналов или None)
    """
    if status_data.get("status") in {"not_found", "inactive"}:
        return (
            "📊 Статус подписки:\n\n"
            "❌ Подписка не активна\n\n"
            "Чтобы получить доступ к закрытым каналам, оформи подписку.\n"
            "Используй команду /buy или кнопку «Купить подписку».",
            None,
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

    # Формируем список каналов и кнопки
    channels_list_items = []
    channel_buttons = []
    
    for ch in channels:
        # Поддерживаем разные форматы данных (dict или объект с model_dump)
        if hasattr(ch, 'model_dump'):
            ch_dict = ch.model_dump()
        elif isinstance(ch, dict):
            ch_dict = ch
        else:
            ch_dict = {}
        
        channel_name = ch_dict.get('channel_name') or ch_dict.get('name') or 'Канал'
        invite_link = ch_dict.get('invite_link')
        channel_username = ch_dict.get('channel_username')
        
        logger.debug(
            "Channel data: name=%s, invite_link=%s, username=%s",
            channel_name,
            invite_link,
            channel_username,
        )
        
        # Добавляем название канала в список
        channels_list_items.append(f"• {channel_name}")
        
        # Формируем кнопку для канала
        if invite_link:
            # Используем invite_link как URL
            channel_buttons.append([
                InlineKeyboardButton(f"📺 {channel_name}", url=invite_link)
            ])
            logger.debug("Created button for channel %s with invite_link", channel_name)
        elif channel_username:
            # Если нет invite_link, используем username
            username = channel_username.lstrip('@')
            channel_url = f"https://t.me/{username}"
            channel_buttons.append([
                InlineKeyboardButton(f"📺 {channel_name}", url=channel_url)
            ])
            logger.debug("Created button for channel %s with username", channel_name)
        else:
            # Если нет ни invite_link, ни username, все равно создаем кнопку с channel_id
            # Пользователь может попробовать перейти, и бот создаст ссылку
            channel_id = ch_dict.get('channel_id')
            if channel_id:
                # Пытаемся создать ссылку на основе channel_id
                # Для приватных каналов это может не сработать, но попробуем
                try:
                    # Если channel_id - это число, формируем ссылку
                    if isinstance(channel_id, (int, str)) and str(channel_id).lstrip('-').isdigit():
                        # Для приватных каналов без username нельзя создать прямую ссылку
                        # Но мы все равно создадим кнопку, которая будет обработана через /channels
                        logger.debug("Channel %s has channel_id but no invite_link or username", channel_name)
                except Exception:
                    pass
            logger.debug("No invite_link or username for channel %s, skipping button", channel_name)
    
    channels_list = "\n".join(channels_list_items) if channels_list_items else "—"
    inline_keyboard = channel_buttons if channel_buttons else None
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
    
    return "\n".join(lines), inline_keyboard


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

