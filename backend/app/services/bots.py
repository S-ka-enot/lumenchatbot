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
