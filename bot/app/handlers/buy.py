from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard
from ..services.backend import BackendClient

logger = logging.getLogger(__name__)

PLAN_CALLBACK_PREFIX = "plan:"
PROMO_INPUT_PREFIX = "promo_input:"
PROMO_APPLY_PREFIX = "promo_apply:"
PAY_WITHOUT_PROMO_PREFIX = "pay_no_promo:"


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    if not user_profile:
        await update.message.reply_text(
            "👋 Привет! Похоже, ты ещё не зарегистрирован.\n\n"
            "Используй команду /start, чтобы начать регистрацию и получить доступ к закрытым каналам.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    try:
        plans = await backend_client.list_plans(bot_id=user_profile.get("bot_id"))
    except httpx.HTTPStatusError as exc:
        logger.exception("Не удалось получить список тарифов (HTTP %s): %s", exc.response.status_code, exc)
        if exc.response.status_code == 404:
            plans = []
        else:
            await update.message.reply_text(
                "😔 К сожалению, не удалось загрузить список тарифов.\n\n"
                "Попробуй позже или свяжись с поддержкой.",
                reply_markup=build_main_menu_keyboard(is_subscriber=False),
            )
            return
    except httpx.RequestError as exc:
        logger.exception("Ошибка сети при получении тарифов: %s", exc)
        await update.message.reply_text(
            "🌐 Проблема с подключением к серверу.\n\n"
            "Проверь интернет-соединение и попробуй позже.",
            reply_markup=build_main_menu_keyboard(is_subscriber=False),
        )
        return
    except Exception as exc:
        logger.exception("Неожиданная ошибка при получении тарифов: %s", exc)
        await update.message.reply_text(
            "😔 К сожалению, не удалось загрузить список тарифов.\n\n"
            "Попробуй позже или свяжись с поддержкой.",
            reply_markup=build_main_menu_keyboard(is_subscriber=False),
        )
        return

    if not plans:
        await update.message.reply_text(
            "📋 Тарифы пока не настроены.\n\n"
            "Свяжись с администратором для получения доступа.",
            reply_markup=build_main_menu_keyboard(is_subscriber=False),
        )
        return

    if len(plans) == 1:
        context.user_data.pop("available_plans", None)
        await _show_plan_with_promo_option(update, context, plans[0])
        return

    context.user_data["available_plans"] = {str(plan["id"]): plan for plan in plans}
    keyboard = [
        [
            InlineKeyboardButton(
                f"{plan['name']} — {_format_price(plan['price_amount'], plan['price_currency'])}",
                callback_data=f"{PLAN_CALLBACK_PREFIX}{plan['id']}",
            )
        ]
        for plan in plans
    ]
    
    promo_code = context.user_data.get("promo_code")
    promo_text = ""
    if promo_code:
        promo_text = f"\n\n🎟️ Применён промокод: {promo_code}"
    
    await update.message.reply_text(
        "💳 Выбери тариф для оформления подписки:\n\n"
        "Нажми на кнопку с нужным тарифом, чтобы перейти к оплате." + promo_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()

    plan_id = query.data.replace(PLAN_CALLBACK_PREFIX, "", 1)
    available_plans = context.user_data.get("available_plans", {})
    plan = available_plans.get(plan_id)

    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile") or {}

    if plan is None:
        try:
            plans = await backend_client.list_plans(bot_id=user_profile.get("bot_id"))
        except httpx.HTTPError:
            plans = []
        for candidate in plans:
            if str(candidate["id"]) == plan_id:
                plan = candidate
                break

    if plan is None:
        await query.message.reply_text(
            "😔 Не удалось найти выбранный тариф.\n\n"
            "Попробуй ещё раз команду /buy или выбери тариф из списка."
        )
        return

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:  # pragma: no cover - возможны гонки с Telegram API
        pass

    await _show_plan_with_promo_option(update, context, plan)
    context.user_data.pop("available_plans", None)


async def _show_plan_with_promo_option(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: dict) -> None:
    """Показывает тариф с возможностью ввода промокода перед оплатой."""
    promo_code = context.user_data.get("promo_code")
    
    # Если промокод уже применён, показываем информацию о нём и кнопки
    if promo_code:
        backend_client = _get_backend_client(context)
        user_profile = context.user_data.get("user_profile") or {}
        
        try:
            promo_info = await backend_client.validate_promo_code(
                code=promo_code,
                bot_id=user_profile.get("bot_id"),
                plan_price=str(plan.get("price_amount", "0")),
            )
            
            if promo_info.get("valid"):
                discount_type = promo_info.get("promo_code", {}).get("discount_type", "percentage")
                discount_value = promo_info.get("promo_code", {}).get("discount_value", "0")
                original_price = promo_info.get("original_price", plan.get("price_amount", "0"))
                final_price = promo_info.get("final_price", plan.get("price_amount", "0"))
                discount_amount = promo_info.get("discount_amount", "0")
                
                if discount_type == "percentage":
                    discount_text = f"{discount_value}%"
                else:
                    discount_text = f"{discount_value} RUB"
                
                message_parts = [
                    "💳 Оформление подписки",
                    "",
                    f"📦 Тариф: {plan.get('name', 'Тариф')}",
                ]
                
                description = plan.get("description")
                if description:
                    message_parts.append(f"📝 {description}")
                
                message_parts.extend([
                    "",
                    "🎟️ Промокод применён:",
                    f"   Код: {promo_code}",
                    f"   Скидка: {discount_text}",
                    f"   Цена без скидки: {original_price} RUB",
                    f"   Цена со скидкой: {final_price} RUB",
                    f"   Экономия: {discount_amount} RUB",
                    "",
                ])
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ Оформить с промокодом",
                            callback_data=f"{PROMO_APPLY_PREFIX}{plan['id']}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Изменить промокод",
                            callback_data=f"{PROMO_INPUT_PREFIX}{plan['id']}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Без промокода",
                            callback_data=f"{PAY_WITHOUT_PROMO_PREFIX}{plan['id']}",
                        )
                    ],
                ]
                
                await _reply(
                    update,
                    "\n".join(message_parts),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
                return
        except Exception as exc:
            logger.warning("Ошибка при проверке промокода: %s", exc)
            # Если не удалось проверить промокод, продолжаем без него
    
    # Если промокода нет или он недействителен, показываем тариф с кнопкой ввода промокода
    message_parts = [
        "💳 Оформление подписки",
        "",
        f"📦 Тариф: {plan.get('name', 'Тариф')}",
    ]
    
    description = plan.get("description")
    if description:
        message_parts.append(f"📝 {description}")
    
    message_parts.extend([
        "",
        f"💰 Стоимость: {_format_price(plan.get('price_amount'), plan.get('price_currency'))}",
        f"⏰ Длительность: {plan.get('duration_days', 0)} дн.",
        "",
        "💡 У тебя есть промокод? Введи его для получения скидки!",
    ])
    
    keyboard = [
        [
            InlineKeyboardButton(
                "🎟️ Ввести промокод",
                callback_data=f"{PROMO_INPUT_PREFIX}{plan['id']}",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Оформить без промокода",
                callback_data=f"{PAY_WITHOUT_PROMO_PREFIX}{plan['id']}",
            )
        ],
    ]
    
    await _reply(
        update,
        "\n".join(message_parts),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_promo_input_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку ввода промокода."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    
    plan_id = query.data.replace(PROMO_INPUT_PREFIX, "", 1)
    context.user_data["promo_input_plan_id"] = plan_id
    context.user_data["waiting_for_promo"] = True
    
    try:
        await query.edit_message_text(
            "🎟️ Введите промокод для получения скидки.\n\n"
            "Промокод будет применён к выбранному тарифу.\n"
            "Или используйте /cancel для отмены.",
        )
    except Exception:
        await query.message.reply_text(
            "🎟️ Введите промокод для получения скидки.\n\n"
            "Промокод будет применён к выбранному тарифу.\n"
            "Или используйте /cancel для отмены.",
        )


async def handle_promo_apply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку оформления с промокодом."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    
    plan_id = query.data.replace(PROMO_APPLY_PREFIX, "", 1)
    available_plans = context.user_data.get("available_plans", {})
    plan = available_plans.get(plan_id)
    
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile") or {}
    
    if plan is None:
        try:
            plans = await backend_client.list_plans(bot_id=user_profile.get("bot_id"))
        except httpx.HTTPError:
            plans = []
        for candidate in plans:
            if str(candidate["id"]) == plan_id:
                plan = candidate
                break
    
    if plan is None:
        await query.message.reply_text(
            "😔 Не удалось найти выбранный тариф.\n\n"
            "Попробуй ещё раз команду /buy."
        )
        return
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    await _start_plan_payment(update, context, plan)


async def handle_pay_without_promo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку оформления без промокода."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    
    plan_id = query.data.replace(PAY_WITHOUT_PROMO_PREFIX, "", 1)
    available_plans = context.user_data.get("available_plans", {})
    plan = available_plans.get(plan_id)
    
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile") or {}
    
    if plan is None:
        try:
            plans = await backend_client.list_plans(bot_id=user_profile.get("bot_id"))
        except httpx.HTTPError:
            plans = []
        for candidate in plans:
            if str(candidate["id"]) == plan_id:
                plan = candidate
                break
    
    if plan is None:
        await query.message.reply_text(
            "😔 Не удалось найти выбранный тариф.\n\n"
            "Попробуй ещё раз команду /buy."
        )
        return
    
    # Очищаем промокод из контекста, так как оформляем без него
    context.user_data.pop("promo_code", None)
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    await _start_plan_payment(update, context, plan)


async def _start_plan_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: dict) -> None:
    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    if not user_profile or update.effective_user is None:
        return

    payload = {
        "user_id": user_profile.get("id"),
        "telegram_id": update.effective_user.id,
        "plan_id": plan["id"],
        "bot_id": plan.get("bot_id") or user_profile.get("bot_id"),
        "promo_code": context.user_data.get("promo_code"),
    }

    try:
        invoice = await backend_client.create_payment(payload)
    except httpx.HTTPStatusError as exc:
        logger.warning("create_payment failed: %s", exc)
        await _reply(
            update,
            "😔 Не удалось сформировать ссылку на оплату.\n\n"
            "Попробуй позже или свяжись с поддержкой."
        )
        return
    except httpx.RequestError as exc:
        logger.warning("create_payment network error: %s", exc)
        await _reply(
            update,
            "🌐 Не удалось подключиться к сервису оплаты.\n\n"
            "Проверь интернет-соединение и попробуй позже."
        )
        return

    payment_url = invoice.get("payment_url") or invoice.get("confirmation_url")
    amount = invoice.get("amount_formatted") or invoice.get("amount")
    duration = invoice.get("duration_days")
    plan_name = invoice.get("plan_name") or plan.get("name")

    # Информация о промокоде
    promo_code = invoice.get("promo_code")
    original_price = invoice.get("original_price")
    discount_amount = invoice.get("discount_amount")

    message_parts = [
        "💳 Оформление подписки\n",
        f"📦 Тариф: {plan_name}",
    ]
    
    description = invoice.get("description") or plan.get("description")
    if description:
        message_parts.append(f"📝 {description}")
    
    message_parts.append("")
    
    # Показываем информацию о промокоде, если он применен
    if promo_code and original_price and discount_amount:
        message_parts.append("🎟️ Промокод применён:")
        message_parts.append(f"   Код: {promo_code}")
        message_parts.append(f"   Цена без скидки: {original_price} RUB")
        message_parts.append(f"   Скидка: -{discount_amount} RUB")
        message_parts.append("")
    
    if amount:
        message_parts.append(f"💰 Стоимость: {amount}")
    if duration:
        message_parts.append(f"⏰ Длительность: {duration} дн.")
    
    message_parts.append("")

    if payment_url:
        message_parts.append("➡️ Перейди по ссылке для оплаты:")
        message_parts.append(f"{payment_url}")
        message_parts.append("")
        message_parts.append("💡 После успешной оплаты ты получишь уведомление и доступ к закрытым каналам.")
    else:
        message_parts.append("⚠️ Ссылка на оплату не получена.")
        message_parts.append("Свяжись с поддержкой для решения проблемы.")
    
    # Очищаем промокод из контекста после использования
    context.user_data.pop("promo_code", None)

    await _reply(
        update,
        "\n".join(message_parts),
        reply_markup=build_main_menu_keyboard(
            is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
        ),
    )


async def _reply(
    update: Update,
    text: str,
    *,
    reply_markup=None,
) -> None:
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client


def _format_price(amount: str | Decimal | None, currency: str | None) -> str:
    if amount is None:
        return "-"
    if isinstance(amount, Decimal):
        value = amount
    else:
        value = Decimal(str(amount))
    code = currency or "RUB"
    return f"{value:,.2f} {code}".replace(",", " ")
