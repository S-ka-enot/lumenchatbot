from __future__ import annotations

import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards import build_main_menu_keyboard
from ..services.backend import BackendClient

logger = logging.getLogger(__name__)


async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для ввода промокода."""
    if update.message is None:
        return

    # Устанавливаем флаг, что пользователь ожидает ввода промокода
    context.user_data["waiting_for_promo"] = True

    text = (
        "🎟️ Введите промокод для получения скидки.\n\n"
        "Промокод будет применён при следующей покупке подписки.\n"
        "Используйте команду /buy для оформления подписки.\n"
        "Или /cancel для отмены."
    )
    await update.message.reply_text(
        text,
        reply_markup=build_main_menu_keyboard(
            is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
        ),
    )


async def handle_promo_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка введенного промокода."""
    if update.message is None or update.effective_user is None:
        return

    # Проверяем, что пользователь ожидает ввода промокода
    if not context.user_data.get("waiting_for_promo"):
        return  # Игнорируем, если не ожидаем ввода промокода

    backend_client = _get_backend_client(context)
    user_profile = context.user_data.get("user_profile")
    if not user_profile:
        context.user_data.pop("waiting_for_promo", None)
        await update.message.reply_text(
            "Похоже, ты ещё не зарегистрирован. Используй /start, чтобы начать.",
        )
        return

    promo_code = (update.message.text or "").strip().upper()
    if not promo_code:
        await update.message.reply_text("Пожалуйста, введите промокод.")
        return
    
    # Убираем флаг ожидания
    context.user_data.pop("waiting_for_promo", None)

    # Проверяем, вводится ли промокод в процессе покупки
    plan_id = context.user_data.get("promo_input_plan_id")
    is_buying = plan_id is not None
    
    # Валидируем промокод через API
    try:
        plan_price = None
        if is_buying:
            # Если вводим промокод в процессе покупки, получаем информацию о тарифе
            try:
                plans = await backend_client.list_plans(bot_id=user_profile.get("bot_id"))
                plan = None
                for p in plans:
                    if str(p["id"]) == plan_id:
                        plan = p
                        break
                if plan:
                    plan_price = str(plan.get("price_amount", "0"))
            except Exception:
                pass
        
        response = await backend_client.validate_promo_code(
            code=promo_code,
            bot_id=user_profile.get("bot_id"),
            plan_price=plan_price,
        )
        
        if not response.get("valid"):
            error_msg = response.get("error", "Промокод недействителен")
            if is_buying:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\n"
                    "Попробуйте другой промокод или используйте /buy для покупки без промокода.",
                )
            else:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\nПопробуйте другой промокод или используйте /buy для покупки без промокода.",
                    reply_markup=build_main_menu_keyboard(
                        is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
                    ),
                )
            return

        # Сохраняем промокод в контексте пользователя
        context.user_data["promo_code"] = promo_code
        promo_info = response.get("promo_code", {})
        discount_type = promo_info.get("discount_type", "percentage")
        discount_value = promo_info.get("discount_value", "0")
        
        if discount_type == "percentage":
            discount_text = f"{discount_value}%"
        else:
            discount_text = f"{discount_value} RUB"
        
        original_price = response.get("original_price", "0")
        final_price = response.get("final_price", "0")
        discount_amount = response.get("discount_amount", "0")
        
        if is_buying:
            # Если вводим промокод в процессе покупки, возвращаем к выбору тарифа
            from .buy import _show_plan_with_promo_option
            
            # Получаем информацию о тарифе
            try:
                plans = await backend_client.list_plans(bot_id=user_profile.get("bot_id"))
                plan = None
                for p in plans:
                    if str(p["id"]) == plan_id:
                        plan = p
                        break
                
                if plan:
                    # Очищаем флаг ввода промокода
                    context.user_data.pop("promo_input_plan_id", None)
                    
                    # Показываем тариф с применённым промокодом
                    await _show_plan_with_promo_option(update, context, plan)
                    return
            except Exception as exc:
                logger.warning("Ошибка при получении тарифа после ввода промокода: %s", exc)
            
            # Если не удалось получить тариф, показываем сообщение
            message = (
                f"✅ Промокод {promo_code} применён!\n\n"
                f"💰 Скидка: {discount_text}\n"
                f"💵 Цена без скидки: {original_price} RUB\n"
                f"💵 Цена со скидкой: {final_price} RUB\n"
                f"💸 Экономия: {discount_amount} RUB\n\n"
                f"Используйте /buy для оформления подписки с промокодом."
            )
            await update.message.reply_text(message)
            return
        
        # Если промокод вводится не в процессе покупки
        message = (
            f"✅ Промокод {promo_code} применён!\n\n"
            f"💰 Скидка: {discount_text}\n"
            f"💵 Цена без скидки: {original_price} RUB\n"
            f"💵 Цена со скидкой: {final_price} RUB\n"
            f"💸 Экономия: {discount_amount} RUB\n\n"
            f"Промокод будет использован при следующей покупке подписки.\n"
            f"Используйте /buy для оформления подписки."
        )
        
        await update.message.reply_text(
            message,
            reply_markup=build_main_menu_keyboard(
                is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
            ),
        )
    except httpx.RequestError as exc:
        logger.warning("validate_promo_code network error: %s", exc)
        await update.message.reply_text(
            "Не удалось проверить промокод. Попробуй позже.",
            reply_markup=build_main_menu_keyboard(
                is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
            ),
        )
    except httpx.HTTPStatusError as exc:
        logger.warning("validate_promo_code failed: %s", exc)
        await update.message.reply_text(
            "Не удалось проверить промокод. Попробуй позже.",
            reply_markup=build_main_menu_keyboard(
                is_subscriber=context.user_data.get("subscription", {}).get("is_active", False)
            ),
        )


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        raise RuntimeError("Backend client is not initialized")
    return backend_client

