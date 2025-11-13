from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.bot import Bot
from ..models.channel import Channel
from ..models.subscription_plan import SubscriptionPlan
from ..schemas.channel import ChannelCreate, ChannelRead, ChannelUpdate

logger = logging.getLogger(__name__)


class ChannelService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_channels_for_bot(
        self,
        *,
        bot_id: int | None = None,
        include_locked: bool = False,
    ) -> list[dict[str, str | bool | None]]:
        target_bot_id = await self._resolve_bot_id(bot_id)
        stmt = (
            select(Channel)
            .where(Channel.bot_id == target_bot_id, Channel.is_active.is_(True))
            .order_by(Channel.channel_name.asc())
        )
        if not include_locked:
            stmt = stmt.where(Channel.requires_subscription.is_(False))

        result = await self.session.execute(stmt)
        channels = result.scalars().all()
        return [
            {
                "channel_id": channel.channel_id,
                "channel_name": channel.channel_name,
                "channel_username": channel.channel_username,
                "invite_link": channel.invite_link,
                "description": channel.description,
                "requires_subscription": channel.requires_subscription,
            }
            for channel in channels
        ]

    async def list_channels_for_plan(self, plan_id: int) -> list[dict[str, str | bool | None]]:
        stmt = (
            select(SubscriptionPlan)
            .options(selectinload(SubscriptionPlan.channels))
            .where(SubscriptionPlan.id == plan_id)
        )
        result = await self.session.execute(stmt)
        plan = result.scalar_one_or_none()
        if plan is None:
            raise ValueError("Тариф не найден")
        return [
            {
                "channel_id": channel.channel_id,
                "channel_name": channel.channel_name,
                "channel_username": channel.channel_username,
                "invite_link": channel.invite_link,
                "description": channel.description,
                "requires_subscription": channel.requires_subscription,
            }
            for channel in plan.channels
        ]

    async def list_channels(
        self, *, bot_id: int | None = None, page: int = 1, size: int = 50
    ) -> tuple[list[ChannelRead], int]:
        offset = (page - 1) * size

        # Получаем общее количество
        from sqlalchemy import func
        count_stmt = select(func.count(Channel.id))
        if bot_id is not None:
            count_stmt = count_stmt.where(Channel.bot_id == bot_id)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one() or 0

        # Получаем страницу данных
        stmt = select(Channel)
        if bot_id is not None:
            stmt = stmt.where(Channel.bot_id == bot_id)
        stmt = stmt.order_by(Channel.created_at.desc()).limit(size).offset(offset)
        result = await self.session.execute(stmt)
        channels = result.scalars().all()
        items = [ChannelRead.model_validate(channel) for channel in channels]
        return items, total

    async def get_channel(self, channel_id: int) -> Channel:
        channel = await self.session.get(Channel, channel_id)
        if channel is None:
            raise ValueError("Канал не найден")
        return channel

    async def create_channel(self, payload: ChannelCreate) -> ChannelRead:
        data = payload.model_dump()
        channel = Channel(**data)
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        logger.info(
            "Создан новый канал",
            extra={
                "channel_id": channel.id,
                "channel_name": channel.channel_name,
                "bot_id": channel.bot_id,
                "requires_subscription": channel.requires_subscription,
            },
        )
        return ChannelRead.model_validate(channel)

    async def update_channel(
        self, channel_id: int, payload: ChannelUpdate
    ) -> ChannelRead:
        channel = await self.get_channel(channel_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(channel, field, value)
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return ChannelRead.model_validate(channel)

    async def delete_channel(self, channel_id: int) -> None:
        channel = await self.get_channel(channel_id)
        channel_name = channel.channel_name
        bot_id = channel.bot_id
        await self.session.delete(channel)
        await self.session.commit()
        logger.info(
            "Удалён канал",
            extra={
                "channel_id": channel_id,
                "channel_name": channel_name,
                "bot_id": bot_id,
            },
        )

    async def _resolve_bot_id(self, bot_id: int | None) -> int:
        if bot_id is not None:
            return bot_id
        stmt = select(Bot).order_by(Bot.id.asc()).limit(1)
        result = await self.session.execute(stmt)
        bot = result.scalar_one_or_none()
        if bot is None:
            raise ValueError("В системе отсутствуют боты. Создайте бота перед добавлением каналов.")
        return bot.id
