from __future__ import annotations

import logging

import httpx
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard
from ..services.backend import BackendClient

logger = logging.getLogger(__name__)


async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    backend_client = _get_backend_client(context)

    # Всегда запрашиваем актуальный статус, чтобы учитывать подписку после оплаты
    try:
        subscription = await backend_client.get_subscription_status(
            telegram_id=update.effective_user.id,
        )
        context.user_data["subscription"] = subscription
    except httpx.HTTPError as exc:
        logger.warning("get_subscription_status failed: %s", exc)
        subscription = context.user_data.get("subscription")
        if subscription is None:
            await update.message.reply_text(
                "😔 Не удалось получить статус подписки.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
                reply_markup=build_main_menu_keyboard(is_subscriber=False),
            )
            return
    except httpx.RequestError as exc:
        logger.warning("get_subscription_status error: %s", exc)
        subscription = context.user_data.get("subscription")
        if subscription is None:
            await update.message.reply_text(
                "😔 Не удалось подключиться к серверу.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
                reply_markup=build_main_menu_keyboard(is_subscriber=False),
            )
            return

    subscription = subscription or {}
    plan = subscription.get("plan") or {}
    plan_channels = plan.get("channels") or []
    is_subscriber = subscription.get("is_active", False)

    if plan_channels:
        channels = plan_channels
    else:
        try:
            channels = await backend_client.list_channels(include_locked=not is_subscriber)
        except httpx.RequestError as exc:
            logger.warning("list_channels error: %s", exc)
            await update.message.reply_text(
                "😔 Не удалось получить список каналов.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
                reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
            )
            return
        except httpx.HTTPStatusError as exc:
            logger.warning("list_channels failed: %s", exc)
            await update.message.reply_text(
                "😔 Не удалось получить список каналов.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
                reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
            )
            return

    if not channels:
        await update.message.reply_text(
            "📚 Список каналов пока пуст.\n\n"
            "Загляни позже — скоро здесь появятся новые каналы!",
            reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
        )
        return

    normalized_channels: list[dict] = []
    for item in channels:
        if hasattr(item, "model_dump"):
            normalized_channels.append(item.model_dump())
        else:
            normalized_channels.append(item)
    channels = normalized_channels

    lines: list[str] = []
    for channel in channels:
        name = channel.get("channel_name") or channel.get("name") or "Канал"
        description = channel.get("description") or ""
        requires_subscription = channel.get("requires_subscription", True)

        if requires_subscription and not is_subscriber:
            locked_emoji = "🔒"
            status_text = " (требуется подписка)"
        else:
            locked_emoji = "🔓"
            status_text = ""

        lines.append(f"{locked_emoji} {name}{status_text}")
        if description:
            lines.append(f"   📝 {description}")
        link = None
        if is_subscriber or not requires_subscription:
            link = await _resolve_channel_link(
                context.bot,
                channel,
                allow_private=is_subscriber,
            )
        if link:
            lines.append(f"   🔗 {link}")
        lines.append("")  # Пустая строка между каналами

    header = "📚 Список каналов:\n"
    if not is_subscriber:
        header += "\n💡 Чтобы получить доступ к закрытым каналам, оформи подписку командой /buy\n"

    message = header + "\n".join(lines)
    await update.message.reply_text(
        message,
        reply_markup=build_main_menu_keyboard(is_subscriber=is_subscriber),
    )


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client


async def _resolve_channel_link(bot, channel: dict, *, allow_private: bool) -> str | None:
    # Сначала проверяем сохранённую ссылку-приглашение из базы
    invite_link = channel.get("invite_link")
    if invite_link:
        return invite_link

    # Если есть username, используем его
    username = channel.get("channel_username") or channel.get("username")
    if username:
        return f"https://t.me/{username.lstrip('@')}"

    # Для приватных каналов без username и invite_link пытаемся создать ссылку через API
    if not allow_private:
        return None

    channel_id = channel.get("channel_id")
    if not channel_id:
        return None

    chat_id = channel_id
    if isinstance(chat_id, str):
        stripped = chat_id.strip()
        if stripped.lstrip("-").isdigit():
            chat_id = int(stripped)

    try:
        invite = await bot.create_chat_invite_link(chat_id=chat_id, creates_join_request=False)
        return invite.invite_link
    except TelegramError as exc:
        logger.warning(
            "Не удалось создать ссылку-приглашение",
            extra={"channel_id": channel_id, "error": str(exc)},
        )
        try:
            return await bot.export_chat_invite_link(chat_id=chat_id)
        except TelegramError as export_exc:
            logger.warning(
                "Не удалось экспортировать ссылку-приглашение",
                extra={"channel_id": channel_id, "error": str(export_exc)},
            )
            return None

