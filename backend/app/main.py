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

