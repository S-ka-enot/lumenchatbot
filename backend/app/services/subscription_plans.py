from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.channel import Channel
from ..models.subscription_plan import SubscriptionPlan
from ..schemas.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanPublic,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
)


class SubscriptionPlanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_plans(self, *, bot_id: int | None = None) -> list[SubscriptionPlanRead]:
        stmt = select(SubscriptionPlan).options(selectinload(SubscriptionPlan.channels))
        if bot_id is not None:
            stmt = stmt.where(SubscriptionPlan.bot_id == bot_id)
        result = await self.session.execute(stmt)
        plans = result.scalars().unique().all()
        return [SubscriptionPlanRead.model_validate(plan) for plan in plans]

    async def list_public_plans(
        self, *, bot_id: int | None = None
    ) -> list[SubscriptionPlanPublic]:
        try:
            stmt = (
                select(SubscriptionPlan)
                .options(selectinload(SubscriptionPlan.channels))
                .where(SubscriptionPlan.is_active.is_(True))
            )
            if bot_id is not None:
                stmt = stmt.where(SubscriptionPlan.bot_id == bot_id)
            result = await self.session.execute(stmt)
            plans = result.scalars().unique().all()
            return [
                SubscriptionPlanPublic(
                    id=plan.id,
                    name=plan.name,
                    slug=plan.slug,
                    description=plan.description,
                    price_amount=plan.price_amount,
                    price_currency=plan.price_currency,
                    duration_days=plan.duration_days,
                    is_recommended=plan.is_recommended,
                    channels=[
                        {
                            "channel_name": channel.channel_name,
                            "description": channel.description,
                            "requires_subscription": channel.requires_subscription,
                        }
                        for channel in (plan.channels or [])
                    ],
                )
                for plan in plans
            ]
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Ошибка в list_public_plans: %s", exc)
            # Возвращаем пустой список при ошибке
            return []

    async def get_plan(self, plan_id: int) -> SubscriptionPlan:
        plan = await self.session.get(
            SubscriptionPlan,
            plan_id,
            options=(selectinload(SubscriptionPlan.channels),),
        )
        if plan is None:
            raise ValueError("Тариф не найден")
        return plan

    async def create_plan(self, payload: SubscriptionPlanCreate) -> SubscriptionPlanRead:
        try:
            data = payload.model_dump(exclude={"channel_ids"})
            data["price_amount"] = Decimal(data["price_amount"])
            # Нормализуем slug: нижний регистр, заменяем пробелы на дефисы
            if "slug" in data and data["slug"]:
                data["slug"] = data["slug"].lower().strip().replace(" ", "-")
            plan = SubscriptionPlan(**data)
            self.session.add(plan)
            await self.session.flush()
            if payload.channel_ids:
                plan.channels = await self._load_channels(payload.channel_ids, plan.bot_id)
            await self.session.commit()
            # Перезагружаем план с каналами через selectinload
            await self.session.refresh(plan, attribute_names=["channels"])
            # Загружаем каналы явно, если они не загрузились
            stmt = (
                select(SubscriptionPlan)
                .options(selectinload(SubscriptionPlan.channels))
                .where(SubscriptionPlan.id == plan.id)
            )
            result = await self.session.execute(stmt)
            plan = result.scalar_one()
            return SubscriptionPlanRead.model_validate(plan)
        except Exception:
            await self.session.rollback()
            raise

    async def update_plan(
        self, plan_id: int, payload: SubscriptionPlanUpdate
    ) -> SubscriptionPlanRead:
        plan = await self.get_plan(plan_id)
        data = payload.model_dump(exclude_unset=True, exclude={"channel_ids"})
        if "price_amount" in data and data["price_amount"] is not None:
            data["price_amount"] = Decimal(data["price_amount"])
        # Нормализуем slug: нижний регистр, заменяем пробелы на дефисы
        if "slug" in data and data["slug"]:
            data["slug"] = data["slug"].lower().strip().replace(" ", "-")
        for field, value in data.items():
            setattr(plan, field, value)
        if payload.channel_ids is not None:
            plan.channels = await self._load_channels(payload.channel_ids, plan.bot_id)
        self.session.add(plan)
        await self.session.commit()
        # Перезагружаем план с каналами через selectinload
        stmt = (
            select(SubscriptionPlan)
            .options(selectinload(SubscriptionPlan.channels))
            .where(SubscriptionPlan.id == plan.id)
        )
        result = await self.session.execute(stmt)
        plan = result.scalar_one()
        return SubscriptionPlanRead.model_validate(plan)

    async def delete_plan(self, plan_id: int) -> None:
        plan = await self.get_plan(plan_id)
        await self.session.delete(plan)
        await self.session.commit()

    async def _load_channels(self, channel_ids: list[int], bot_id: int) -> list[Channel]:
        if not channel_ids:
            return []
        stmt = select(Channel).where(Channel.id.in_(channel_ids))
        result = await self.session.execute(stmt)
        channels = result.scalars().all()
        if len(channels) != len(set(channel_ids)):
            raise ValueError("Некоторые каналы не найдены")
        for channel in channels:
            if channel.bot_id != bot_id:
                raise ValueError("Канал принадлежит другому боту")
        return list(channels)
