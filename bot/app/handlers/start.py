from __future__ import annotations

import logging
from typing import Any

import httpx
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from ..keyboards import (
    build_contact_keyboard,
    build_main_menu_keyboard,
    build_skip_keyboard,
)
from ..services.backend import BackendClient
from ..utils.validators import normalize_phone, parse_birthday

WAITING_FOR_CONTACT, WAITING_FOR_BIRTHDAY = range(2)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if update.message is None or user is None:
        return ConversationHandler.END

    greeting = (
        "👋 Привет! Я помогу оформить подписку на закрытые каналы.\n\n"
        "Чтобы продолжить, поделись, пожалуйста, своим номером телефона."
    )
    await update.message.reply_text(greeting, reply_markup=build_contact_keyboard())
    return WAITING_FOR_CONTACT


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.contact is None:
        await update.message.reply_text(
            "Пожалуйста, используй кнопку, чтобы поделиться номером телефона.",
            reply_markup=build_contact_keyboard(),
        )
        return WAITING_FOR_CONTACT

    backend_client = _get_backend_client(context)

    contact = update.message.contact
    normalized_phone = normalize_phone(contact.phone_number or "")
    if normalized_phone is None:
        await update.message.reply_text(
            "Не удалось распознать номер телефона. Попробуй ещё раз.",
            reply_markup=build_contact_keyboard(),
        )
        return WAITING_FOR_CONTACT

    user = update.effective_user
    payload: dict[str, Any] = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": contact.first_name or user.first_name,
        "last_name": contact.last_name or user.last_name,
        "phone_number": normalized_phone,
    }

    try:
        response = await backend_client.register_user(payload)
    except httpx.HTTPStatusError as exc:
        await update.message.reply_text(
            "Не удалось зарегистрировать пользователя. Попробуй позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        logger.exception("register_user failed: %s", exc)
        return ConversationHandler.END
    except httpx.RequestError as exc:
        await update.message.reply_text(
            "Сервис временно недоступен. Попробуй позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        logger.exception("register_user request error: %s", exc)
        return ConversationHandler.END

    user_info = response.get("user") if isinstance(response, dict) else None
    if not user_info and isinstance(response, dict) and "id" in response:
        user_info = response

    context.user_data["user_profile"] = user_info or {}
    await update.message.reply_text(
        "Отлично! Теперь укажи дату рождения (формат ДД.ММ.ГГГГ) "
        "или нажми «Пропустить».",
        reply_markup=build_skip_keyboard(),
    )
    return WAITING_FOR_BIRTHDAY


async def receive_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    text = update.message.text or ""
    birthday = parse_birthday(text)
    if birthday is None:
        await update.message.reply_text(
            "Не получилось распознать дату. Проверь формат и попробуй снова "
            "или нажми «Пропустить».",
            reply_markup=build_skip_keyboard(),
        )
        return WAITING_FOR_BIRTHDAY

    await _update_user_profile(context, {"birthday": birthday.isoformat()})
    await update.message.reply_text(
        "Спасибо! Регистрация завершена. Чем могу помочь?",
        reply_markup=build_main_menu_keyboard(is_subscriber=False),
    )
    return ConversationHandler.END


async def skip_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is not None:
        await update.message.reply_text(
            "Регистрация завершена. Чем могу помочь?",
            reply_markup=build_main_menu_keyboard(is_subscriber=False),
        )
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is not None:
        await update.message.reply_text(
            "Регистрация отменена. Если захочешь продолжить — набери /start.",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END


async def _update_user_profile(
    context: ContextTypes.DEFAULT_TYPE,
    payload: dict[str, Any],
) -> None:
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile", {})
    user_id = user_profile.get("id")
    if not user_id:
        return
    try:
        await backend_client.update_user(user_id=user_id, payload=payload)
    except httpx.RequestError as exc:
        logger.warning("update_user network error: %s", exc)
    except httpx.HTTPStatusError as exc:
        logger.warning("update_user failed: %s", exc)


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client
