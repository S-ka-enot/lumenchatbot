from __future__ import annotations

import asyncio
import logging

from telegram import Bot, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .config import settings
from .handlers import (
    WAITING_FOR_BIRTHDAY,
    WAITING_FOR_CONTACT,
    buy_command,
    cancel_command,
    cancel_registration,
    channels_command,
    handle_pay_without_promo_callback,
    handle_plan_selection,
    handle_promo_apply_callback,
    handle_promo_code_input,
    handle_promo_input_callback,
    handle_cancel_auto_renew_callback,
    handle_cancel_cancel_subscription_callback,
    handle_cancel_subscription_full_callback,
    handle_confirm_cancel_subscription_callback,
    help_command,
    payments_command,
    promo_command,
    receive_birthday,
    receive_contact,
    skip_birthday,
    start,
    status_command,
    unsubscribe_command,
)
from .services.backend import BackendClient
from .tasks.subscription_tasks import (
    remove_expired_users_from_channels,
    send_subscription_reminders,
)

logger = logging.getLogger("lumenpay.bot")


def build_application(bot_token: str) -> Application:
    application = (
        ApplicationBuilder()
        .token(bot_token)
        .post_init(_on_startup)
        .post_shutdown(_on_shutdown)
        .build()
    )

    backend_client = BackendClient(
        base_url=str(settings.backend_base_url),
        api_prefix=settings.backend_api_prefix,
        timeout=settings.request_timeout_seconds,
    )
    application.bot_data["backend_client"] = backend_client

    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_CONTACT: [
                MessageHandler(filters.CONTACT, receive_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact),
            ],
            WAITING_FOR_BIRTHDAY: [
                MessageHandler(filters.Regex("^Пропустить$"), skip_birthday),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_birthday),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_registration),
            MessageHandler(filters.Regex("^Отмена$"), cancel_registration),
        ],
        allow_reentry=True,
    )

    application.add_handler(registration_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("payments", payments_command))
    application.add_handler(CommandHandler("history", payments_command))  # Алиас для /payments
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(handle_plan_selection, pattern="^plan:"))
    application.add_handler(CallbackQueryHandler(handle_promo_input_callback, pattern="^promo_input:"))
    application.add_handler(CallbackQueryHandler(handle_promo_apply_callback, pattern="^promo_apply:"))
    application.add_handler(CallbackQueryHandler(handle_pay_without_promo_callback, pattern="^pay_no_promo:"))
    application.add_handler(CallbackQueryHandler(handle_cancel_auto_renew_callback, pattern="^cancel_auto_renew$"))
    application.add_handler(CallbackQueryHandler(handle_cancel_subscription_full_callback, pattern="^cancel_subscription_full$"))
    application.add_handler(CallbackQueryHandler(handle_confirm_cancel_subscription_callback, pattern="^confirm_cancel_subscription$"))
    application.add_handler(CallbackQueryHandler(handle_cancel_cancel_subscription_callback, pattern="^cancel_cancel_subscription$"))
    
    # Обработка ввода промокода (текст без команд, только если ожидается ввод)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(Помощь|Мои каналы|Купить подписку|Продлить подписку|История платежей|Статус)$"),
            handle_promo_code_input
        )
    )

    application.add_handler(MessageHandler(filters.Regex("^Помощь$"), help_command))
    application.add_handler(MessageHandler(filters.Regex("^Мои каналы$"), channels_command))
    application.add_handler(MessageHandler(filters.Regex("^📚 Каналы$"), channels_command))
    application.add_handler(MessageHandler(filters.Regex("^Купить подписку$"), buy_command))
    application.add_handler(MessageHandler(filters.Regex("^Продлить подписку$"), buy_command))
    application.add_handler(MessageHandler(filters.Regex("^История платежей$"), payments_command))
    application.add_handler(MessageHandler(filters.Regex("^Статус$"), status_command))

    return application


async def _on_startup(application: Application) -> None:
    me = await application.bot.get_me()
    application.bot_data["bot_id"] = me.id
    logger.info("Bot started as @%s", me.username)
    
    # Запускаем периодические задачи
    backend_client = application.bot_data.get("backend_client")
    if isinstance(backend_client, BackendClient):
        # Задача для отправки напоминаний (каждый день в 10:00)
        asyncio.create_task(_run_daily_reminders(application.bot, backend_client))
        # Задача для удаления из каналов (каждые 6 часов)
        asyncio.create_task(_run_channel_cleanup(application.bot, backend_client))
        logger.info("Периодические задачи запущены")


async def _run_daily_reminders(bot: Bot, backend_client: BackendClient) -> None:
    """Запускает задачу отправки напоминаний каждый день в 10:00."""
    # Первый запуск - ждём до 10:00
    await _wait_until_time(10, 0)
    
    while True:
        try:
            await send_subscription_reminders(bot, backend_client)
            # Ждём до 10:00 следующего дня
            await _wait_until_time(10, 0)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Ошибка в задаче отправки напоминаний: %s", exc)
            # При ошибке ждём час перед повтором
            await asyncio.sleep(3600)


async def _run_channel_cleanup(bot: Bot, backend_client: BackendClient) -> None:
    """Запускает задачу удаления пользователей из каналов каждые 6 часов."""
    # Первый запуск через час после старта
    await asyncio.sleep(3600)
    
    while True:
        try:
            await remove_expired_users_from_channels(bot, backend_client)
            # Ждём 6 часов до следующего запуска
            await asyncio.sleep(6 * 3600)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Ошибка в задаче удаления из каналов: %s", exc)
            # При ошибке ждём час перед повтором
            await asyncio.sleep(3600)


async def _wait_until_time(hour: int, minute: int) -> None:
    """Ждёт до указанного времени следующего дня."""
    from datetime import datetime, time, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    target_time = time(hour, minute)
    target_datetime = datetime.combine(now.date(), target_time).replace(tzinfo=timezone.utc)
    
    # Если указанное время уже прошло сегодня, планируем на завтра
    if target_datetime <= now:
        target_datetime += timedelta(days=1)
    
    wait_seconds = (target_datetime - now).total_seconds()
    await asyncio.sleep(wait_seconds)


async def _on_shutdown(application: Application) -> None:
    backend_client = application.bot_data.get("backend_client")
    if isinstance(backend_client, BackendClient):
        await backend_client.close()
    logger.info("Bot shutdown complete")


def run() -> None:
    application = build_application(settings.bot_token.get_secret_value())
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    run()
