from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.crypto import encrypt_secret
from ..models.bot import Bot

logger = logging.getLogger(__name__)


class BotService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_bots(self) -> list[Bot]:
        result = await self.session.execute(select(Bot))
        return result.scalars().all()

    async def get_bot(self, bot_id: int) -> Bot:
        bot = await self.session.get(Bot, bot_id)
        if bot is None:
            raise ValueError("Бот не найден")
        return bot

    async def update_token(self, bot_id: int, token: str) -> Bot:
        bot = await self.get_bot(bot_id)
        bot.telegram_bot_token_encrypted = encrypt_secret(token).encode()
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        logger.info(
            "Обновлён токен бота",
            extra={
                "bot_id": bot_id,
                "bot_name": bot.name,
            },
        )
        return bot

    async def create_bot(self, name: str, slug: str, timezone: str = "Europe/Moscow", is_active: bool = True) -> Bot:
        # Проверяем, что slug уникален
        result = await self.session.execute(select(Bot).where(Bot.slug == slug))
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Бот с slug '{slug}' уже существует")

        bot = Bot(
            name=name,
            slug=slug,
            timezone=timezone,
            is_active=is_active,
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        logger.info(
            "Создан новый бот",
            extra={
                "bot_id": bot.id,
                "bot_name": bot.name,
                "bot_slug": bot.slug,
            },
        )
        return bot

    async def update_bot(
        self, bot_id: int, name: str | None = None, slug: str | None = None, 
        timezone: str | None = None, is_active: bool | None = None
    ) -> Bot:
        bot = await self.get_bot(bot_id)

        if slug is not None and slug != bot.slug:
            # Проверяем, что новый slug уникален
            result = await self.session.execute(select(Bot).where(Bot.slug == slug))
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError(f"Бот с slug '{slug}' уже существует")
            bot.slug = slug

        if name is not None:
            bot.name = name
        if timezone is not None:
            bot.timezone = timezone
        if is_active is not None:
            bot.is_active = is_active

        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        logger.info(
            "Обновлён бот",
            extra={
                "bot_id": bot_id,
                "bot_name": bot.name,
            },
        )
        return bot

    async def delete_bot(self, bot_id: int) -> None:
        bot = await self.get_bot(bot_id)
        await self.session.delete(bot)
        await self.session.commit()
        logger.info(
            "Удалён бот",
            extra={
                "bot_id": bot_id,
                "bot_name": bot.name,
            },
        )
