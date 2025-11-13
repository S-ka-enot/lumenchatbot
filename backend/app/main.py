from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .api.router import api_router
from .background.scheduler import shutdown_scheduler, start_scheduler
from .core.config import settings
from .core.logging import configure_logging
from .core.rate_limit import limiter
from .db.session import AsyncSessionLocal, async_engine
from .services.admins import AdminService
from .services.bots import BotService
from .services.payment_providers import PaymentProviderSettingsService

logger = logging.getLogger("lumenpay.backend")


async def ensure_default_admin() -> None:
    if not settings.admin_seed_username or not settings.admin_seed_password:
        logger.debug("Skipping default admin creation: credentials not provided")
        return

    async with AsyncSessionLocal() as session:
        service = AdminService(session)
        existing_admin = await service.get_by_username(settings.admin_seed_username)
        if existing_admin:
            logger.debug(
                "Default admin already exists",
                extra={"username": settings.admin_seed_username},
            )
            return
        await service.create_admin(
            username=settings.admin_seed_username,
            password=settings.admin_seed_password.get_secret_value(),
        )
        logger.info(
            "Created default admin account",
            extra={"username": settings.admin_seed_username},
        )


async def ensure_yookassa_settings() -> None:
    """Автоматически восстанавливает настройки YooKassa из переменных окружения при старте."""
    import os
    from pathlib import Path
    
    # Пытаемся загрузить настройки из env.local напрямую, если они не загрузились через pydantic
    shop_id = settings.yookassa_shop_id
    api_key = settings.yookassa_api_key
    
    if not shop_id or not api_key:
        # Пытаемся прочитать напрямую из файла (относительно корня проекта)
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / "config" / "env.local"
        if not env_file.exists():
            # Пробуем относительно текущей директории
            env_file = Path("config/env.local")
        
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("YOOKASSA_SHOP_ID="):
                            shop_id = line.split("=", 1)[1].strip()
                        elif line.startswith("YOOKASSA_API_KEY="):
                            api_key_str = line.split("=", 1)[1].strip()
                            from pydantic import SecretStr
                            api_key = SecretStr(api_key_str)
                if shop_id and api_key:
                    logger.info("Loaded YooKassa settings from env.local file")
            except Exception as exc:
                logger.debug("Failed to read YooKassa settings from env.local: %s", exc)
    
    logger.info("Checking YooKassa settings on startup (shop_id: %s, has_api_key: %s)", 
                shop_id, bool(api_key))
    
    if not shop_id or not api_key:
        logger.debug("Skipping YooKassa settings restoration: credentials not provided")
        return

    logger.info("Restoring YooKassa settings from environment variables on startup...")
    
    async with AsyncSessionLocal() as session:
        try:
            provider_service = PaymentProviderSettingsService(session)
            # Всегда обновляем настройки из env при старте, чтобы гарантировать работоспособность
            api_key_value = api_key.get_secret_value() if hasattr(api_key, 'get_secret_value') else str(api_key)
            await provider_service.upsert_yookassa_settings(
                shop_id=shop_id,
                api_key=api_key_value,
            )
            logger.info(
                "YooKassa settings restored from environment variables (shop_id: %s)",
                shop_id,
            )
        except Exception as exc:
            logger.error(
                "Failed to restore YooKassa settings from environment: %s",
                exc,
                exc_info=True,
            )


async def ensure_bot_token() -> None:
    """Автоматически восстанавливает токен бота из переменных окружения при старте."""
    from pathlib import Path
    
    # Пытаемся загрузить токен из настроек
    bot_token = settings.telegram_bot_token
    
    if not bot_token:
        # Пытаемся прочитать напрямую из файла (относительно корня проекта)
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / "config" / "env.local"
        if not env_file.exists():
            # Пробуем относительно текущей директории
            env_file = Path("config/env.local")
        
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("TELEGRAM_BOT_TOKEN="):
                            token_str = line.split("=", 1)[1].strip()
                            from pydantic import SecretStr
                            bot_token = SecretStr(token_str)
                            logger.info("Loaded bot token from env.local file")
                            break
            except Exception as exc:
                logger.debug("Failed to read bot token from env.local: %s", exc)
    
    logger.info("Checking bot token on startup (has_token: %s)", bool(bot_token))
    
    if not bot_token:
        logger.debug("Skipping bot token restoration: token not provided")
        return

    logger.info("Restoring bot token from environment variables on startup...")
    
    async with AsyncSessionLocal() as session:
        try:
            bot_service = BotService(session)
            # Получаем первого бота (обычно это бот с id=1)
            from sqlalchemy import select
            from .models.bot import Bot
            result = await session.execute(select(Bot).limit(1))
            bot = result.scalar_one_or_none()
            
            if bot:
                token_value = bot_token.get_secret_value() if hasattr(bot_token, 'get_secret_value') else str(bot_token)
                await bot_service.update_token(bot.id, token_value)
                logger.info(
                    "Bot token restored from environment variables (bot_id: %s, bot_name: %s)",
                    bot.id,
                    bot.name,
                )
            else:
                logger.warning("No bot found in database, skipping token restoration")
        except Exception as exc:
            logger.error(
                "Failed to restore bot token from environment: %s",
                exc,
                exc_info=True,
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    start_scheduler()

    if settings.check_db_on_startup:
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(lambda _: None)
        except Exception as exc:  # pragma: no cover - логирование
            logger.error("Database connection failed during startup: %s", exc)
            raise

    await ensure_default_admin()
    await ensure_yookassa_settings()
    await ensure_bot_token()

    yield

    if settings.shutdown_graceful:
        await asyncio.sleep(settings.shutdown_delay_seconds)
    shutdown_scheduler()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.project_name,
        version=settings.version,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Настраиваем rate limiting
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )

