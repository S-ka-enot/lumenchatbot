from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from ..models.bot import Bot
from ..models.payment import Payment, PaymentProvider, PaymentStatus
from ..models.subscription import Subscription
from ..models.subscription_plan import SubscriptionPlan
from ..models.user import User
from ..schemas.admin import (
    SubscriberCreate,
    SubscriberListItem,
    SubscriberUpdate,
    SubscriptionExtendRequest,
)
from ..schemas.bot import ChannelPublic, SubscriptionStatusResponse
from ..schemas.subscription_plan import SubscriptionPlanPublic
from .channels import ChannelService


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_subscribers(
        self, page: int = 1, size: int = 50
    ) -> tuple[list[SubscriberListItem], int]:
        offset = (page - 1) * size

        # Получаем общее количество
        from sqlalchemy import func
        count_stmt = select(func.count(User.id))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one() or 0

        # Получаем страницу данных
        stmt: Select[tuple[User]] = (
            select(User)
            .options(
                selectinload(User.subscriptions)
                .selectinload(Subscription.payment),
                selectinload(User.subscriptions)
                .selectinload(Subscription.plan),
            )
            .order_by(User.created_at.desc())
            .limit(size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        users = result.scalars().unique().all()
        items = [self._to_subscriber_list_item(user) for user in users]
        return items, total

    async def register_from_bot(self, payload: dict[str, Any]) -> User:
        telegram_id = payload["telegram_id"]
        phone_number = payload.get("phone_number")
        bot_id = await self._resolve_bot_id(payload.get("bot_id"))

        stmt = (
            select(User)
            .where(User.bot_id == bot_id, User.telegram_id == telegram_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None and phone_number:
            stmt_phone = (
                select(User)
                .where(User.bot_id == bot_id, User.phone_number == phone_number)
                .limit(1)
            )
            result_phone = await self.session.execute(stmt_phone)
            user = result_phone.scalar_one_or_none()

        if user is None:
            user = User(
                bot_id=bot_id,
                telegram_id=telegram_id,
                username=payload.get("username"),
                first_name=payload.get("first_name"),
                last_name=payload.get("last_name"),
                phone_number=phone_number,
            )
            self.session.add(user)
        else:
            user.username = payload.get("username") or user.username
            user.first_name = payload.get("first_name") or user.first_name
            user.last_name = payload.get("last_name") or user.last_name
            if phone_number:
                user.phone_number = phone_number

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile_from_bot(self, user_id: int, data: dict[str, Any]) -> User | None:
        user = await self.session.get(User, user_id)
        if user is None:
            return None

        for field in ("first_name", "last_name", "phone_number", "username"):
            if field in data and data[field] is not None:
                setattr(user, field, data[field])

        birthday = data.get("birthday")
        if birthday:
            user.birthday = birthday

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_telegram(
        self,
        telegram_id: int,
        *,
        bot_id: int | None = None,
    ) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        if bot_id is not None:
            stmt = stmt.where(User.bot_id == bot_id)
        stmt = stmt.options(
            selectinload(User.subscriptions).selectinload(Subscription.payment)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subscription_status_for_telegram(
        self,
        telegram_id: int,
        *,
        bot_id: int | None = None,
    ) -> SubscriptionStatusResponse:
        stmt = (
            select(User)
            .options(
                selectinload(User.subscriptions)
                .selectinload(Subscription.plan)
                .selectinload(SubscriptionPlan.channels)
            )
            .where(User.telegram_id == telegram_id)
            .order_by(User.created_at.desc())
            .limit(1)
        )
        if bot_id is not None:
            stmt = stmt.where(User.bot_id == bot_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return SubscriptionStatusResponse(status="not_found", is_active=False)

        now = datetime.now(timezone.utc)
        latest_subscription = None
        subscription_end = None

        if user.subscriptions:
            latest_subscription = max(
                user.subscriptions, key=lambda item: item.end_date or datetime.min
            )
            if latest_subscription:
                subscription_end = self._ensure_timezone(
                    latest_subscription.end_date
                ) if latest_subscription.end_date else None
        if subscription_end is None and user.subscription_end:
            subscription_end = self._ensure_timezone(user.subscription_end)

        is_active = False
        if (
            latest_subscription
            and subscription_end
            and subscription_end >= now
            and not user.is_blocked
        ):
            is_active = True
        status = "active" if is_active else "inactive"

        days_left = None
        if subscription_end:
            delta = subscription_end - now
            days_left = max(0, delta.days)

        plan_public: SubscriptionPlanPublic | None = None
        channel_service = ChannelService(self.session)
        if latest_subscription and latest_subscription.plan:
            plan_model = latest_subscription.plan
            plan_channels = [
                ChannelPublic(
                    channel_id=channel.channel_id,
                    channel_name=channel.channel_name,
                    channel_username=channel.channel_username,
                    invite_link=channel.invite_link,
                    description=channel.description,
                    requires_subscription=channel.requires_subscription,
                )
                for channel in plan_model.channels
            ]
            channels = plan_channels
            plan_public = SubscriptionPlanPublic(
                id=plan_model.id,
                name=plan_model.name,
                slug=plan_model.slug,
                description=plan_model.description,
                price_amount=plan_model.price_amount,
                price_currency=plan_model.price_currency,
                duration_days=plan_model.duration_days,
                is_recommended=plan_model.is_recommended,
                channels=[channel.model_dump() for channel in plan_channels],
            )
        else:
            channels_raw = await channel_service.list_channels_for_bot(
                bot_id=user.bot_id,
                include_locked=is_active,
            )
            channels = [ChannelPublic(**channel) for channel in channels_raw]

        auto_renew = False
        if latest_subscription:
            auto_renew = latest_subscription.auto_renew

        return SubscriptionStatusResponse(
            status=status,
            is_active=is_active,
            subscription_end=subscription_end,
            days_left=days_left,
            auto_renew=auto_renew,
            channels=channels,
            plan=plan_public,
        )

    async def create_subscriber(self, payload: SubscriberCreate) -> SubscriberListItem:
        try:
            bot_id = await self._resolve_bot_id(payload.bot_id)

            # Check for existing user with the same Telegram ID or phone number
            conditions = [User.bot_id == bot_id, User.telegram_id == payload.telegram_id]
            stmt = select(User).where(*conditions)
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none() is not None:
                raise ValueError("Пользователь с таким Telegram ID уже существует")

            if payload.phone_number:
                phone_stmt = select(User).where(
                    User.bot_id == bot_id, User.phone_number == payload.phone_number
                )
                phone_result = await self.session.execute(phone_stmt)
                if phone_result.scalar_one_or_none() is not None:
                    raise ValueError("Пользователь с таким номером телефона уже существует")

            user = User(
                bot_id=bot_id,
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                phone_number=payload.phone_number,
                is_blocked=payload.is_blocked or False,
            )
            self.session.add(user)
            await self.session.flush()

            if payload.subscription_days or payload.plan_id:
                await self._create_subscription_for_user(
                    user=user,
                    days=payload.subscription_days,
                    amount=payload.subscription_amount,
                    description=payload.subscription_description,
                    plan_id=payload.plan_id,
                )
                # ИСПРАВЛЕНИЕ: Перезагружаем пользователя после создания подписки
                # для получения актуальных данных перед коммитом
                await self.session.refresh(user, attribute_names=["subscriptions", "subscription_end", "is_premium"])

            await self.session.commit()
            logger.info(
                "Создан новый подписчик",
                extra={
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "bot_id": bot_id,
                    "has_subscription": bool(payload.subscription_days or payload.plan_id),
                },
            )
            return await self._get_subscriber_item(user.id)
        except Exception:
            await self.session.rollback()
            raise

    async def update_subscriber(
        self, user_id: int, payload: SubscriberUpdate
    ) -> SubscriberListItem:
        try:
            user = await self._get_user(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            if payload.username is not None:
                user.username = payload.username
            if payload.first_name is not None:
                user.first_name = payload.first_name
            if payload.last_name is not None:
                user.last_name = payload.last_name
            if payload.phone_number is not None:
                user.phone_number = payload.phone_number
            if payload.is_blocked is not None:
                user.is_blocked = payload.is_blocked

            self._activate_latest_subscription(user)
            await self.session.commit()
            logger.info(
                "Обновлены данные подписчика",
                extra={
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "is_blocked": payload.is_blocked,
                },
            )
            return await self._get_subscriber_item(user.id)
        except Exception:
            await self.session.rollback()
            raise

    async def extend_subscription(
        self, user_id: int, payload: SubscriptionExtendRequest
    ) -> SubscriberListItem:
        # ВАРИАНТ 1 (текущий): Минимальные изменения
        try:
            user = await self._get_user(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            await self._create_subscription_for_user(
                user=user,
                days=payload.days,
                amount=payload.amount,
                description=payload.description,
                plan_id=payload.plan_id,
            )
            
            # ИСПРАВЛЕНИЕ: Перезагружаем пользователя после создания подписки
            await self.session.refresh(user, attribute_names=["subscriptions", "subscription_end", "is_premium"])
            
            await self.session.commit()
            logger.info(
                "Продлена подписка подписчика",
                extra={
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "days": payload.days,
                    "plan_id": payload.plan_id,
                },
            )
            return await self._get_subscriber_item(user.id)
        except Exception:
            await self.session.rollback()
            raise

    # ============================================================================
    # ВАРИАНТ 2: Использование expire для синхронизации
    # ============================================================================
    async def extend_subscription_variant_b(
        self, user_id: int, payload: SubscriptionExtendRequest
    ) -> SubscriberListItem:
        try:
            user = await self._get_user(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            await self._create_subscription_for_user_variant_b(
                user=user,
                days=payload.days,
                amount=payload.amount,
                description=payload.description,
                plan_id=payload.plan_id,
            )
            
            # ВАРИАНТ 2: Используем expire_all для принудительной перезагрузки
            self.session.expire_all()
            await self.session.refresh(user, attribute_names=["subscriptions", "subscription_end", "is_premium"])
            
            await self.session.commit()
            logger.info(
                "Продлена подписка подписчика (вариант B)",
                extra={
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "days": payload.days,
                    "plan_id": payload.plan_id,
                },
            )
            return await self._get_subscriber_item(user.id)
        except Exception:
            await self.session.rollback()
            raise

    # ============================================================================
    # ВАРИАНТ 3: Полная переработка с перезагрузкой
    # ============================================================================
    async def extend_subscription_variant_c(
        self, user_id: int, payload: SubscriptionExtendRequest
    ) -> SubscriberListItem:
        try:
            user = await self._get_user(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            await self._create_subscription_for_user_variant_c(
                user=user,
                days=payload.days,
                amount=payload.amount,
                description=payload.description,
                plan_id=payload.plan_id,
            )
            
            # ВАРИАНТ 3: Полная перезагрузка пользователя с подписками
            stmt = (
                select(User)
                .options(
                    selectinload(User.subscriptions).selectinload(Subscription.payment),
                    selectinload(User.subscriptions).selectinload(Subscription.plan),
                )
                .where(User.id == user_id)
            )
            result = await self.session.execute(stmt)
            user = result.scalar_one()
            
            self._activate_latest_subscription(user)
            self.session.add(user)
            await self.session.flush()
            
            await self.session.commit()
            logger.info(
                "Продлена подписка подписчика (вариант C)",
                extra={
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "days": payload.days,
                    "plan_id": payload.plan_id,
                },
            )
            return await self._get_subscriber_item(user.id)
        except Exception:
            await self.session.rollback()
            raise

    async def delete_subscriber(self, user_id: int) -> None:
        try:
            user = await self.session.get(User, user_id)
            if user is None:
                raise ValueError("Пользователь не найден")
            telegram_id = user.telegram_id
            bot_id = user.bot_id
            await self.session.delete(user)
            await self.session.commit()
            logger.info(
                "Удалён подписчик",
                extra={
                    "user_id": user_id,
                    "telegram_id": telegram_id,
                    "bot_id": bot_id,
                },
            )
        except Exception:
            await self.session.rollback()
            raise

    async def remove_subscription(
        self, user_id: int, subscription_id: int
    ) -> SubscriberListItem:
        try:
            stmt = (
                select(Subscription)
                .options(
                    selectinload(Subscription.plan),
                )
                .where(Subscription.id == subscription_id, Subscription.user_id == user_id)
            )
            result = await self.session.execute(stmt)
            subscription = result.scalar_one_or_none()
            if subscription is None:
                raise ValueError("Подписка не найдена")

            await self.session.delete(subscription)
            await self.session.flush()

            user = await self._get_user(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            self._activate_latest_subscription(user)
            self.session.add(user)
            await self.session.commit()
            logger.info(
                "Удалена подписка подписчика",
                extra={
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "telegram_id": user.telegram_id,
                },
            )
            return self._to_subscriber_list_item(user)
        except Exception:
            await self.session.rollback()
            raise

    async def export_subscribers(self) -> list[dict[str, str]]:
        stmt = (
            select(User)
            .options(
                selectinload(User.subscriptions)
                .selectinload(Subscription.plan),
                selectinload(User.subscriptions).selectinload(Subscription.payment),
            )
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(stmt)
        users = result.scalars().unique().all()

        rows: list[dict[str, str]] = []
        for user in users:
            item = self._to_subscriber_list_item(user)
            rows.append(
                {
                    "id": str(item.id),
                    "bot_id": str(item.bot_id),
                    "telegram_id": str(item.telegram_id or ""),
                    "full_name": item.full_name,
                    "username": item.username or "",
                    "phone_number": item.phone_number or "",
                    "tariff": item.tariff or "",
                    "status": item.status,
                    "expires_at": item.expires_at.isoformat() if item.expires_at else "",
                    "is_blocked": "yes" if item.is_blocked else "no",
                    "created_at": (
                        user.created_at.isoformat() if getattr(user, "created_at", None) else ""
                    ),
                }
            )
        return rows

    async def _create_subscription_for_user(
        self,
        *,
        user: User,
        days: int | None,
        amount: Decimal | None,
        description: str | None,
        plan_id: int | None,
    ) -> None:
        # ВАРИАНТ 1 (текущий): Минимальные изменения
        now = datetime.now(timezone.utc)
        start_date = now
        if user.subscription_end:
            end_ref = (
                user.subscription_end.replace(tzinfo=timezone.utc)
                if user.subscription_end.tzinfo is None
                else user.subscription_end
            )
            if end_ref > now:
                start_date = end_ref

        plan: SubscriptionPlan | None = None
        if plan_id:
            plan = await self.session.get(SubscriptionPlan, plan_id)
            if plan is None:
                raise ValueError("Указанный тариф не найден")
            days = plan.duration_days
        if days is None:
            raise ValueError("Не указана длительность подписки")

        end_date = start_date + timedelta(days=days)

        payment_id: int | None = None
        if amount is not None:
            payment = Payment(
                bot_id=user.bot_id,
                user_id=user.id,
                amount=amount,
                currency="RUB",
                payment_provider=PaymentProvider.YOOKASSA,
                status=PaymentStatus.SUCCEEDED,
                description=description,
                paid_at=now,
                plan_id=plan_id,
            )
            self.session.add(payment)
            await self.session.flush()
            payment_id = payment.id

        subscription = Subscription(
            bot_id=user.bot_id,
            user_id=user.id,
            payment_id=payment_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_renew=False,
            plan_id=plan_id,
        )
        self.session.add(subscription)
        await self.session.flush()

        # ВАРИАНТ 1: Явное сохранение пользователя после активации подписки
        await self.session.refresh(user, attribute_names=["subscriptions"])
        self._activate_latest_subscription(user)
        self.session.add(user)
        await self.session.flush()

    # ============================================================================
    # ВАРИАНТ 2: Использование expire для синхронизации
    # ============================================================================
    async def _create_subscription_for_user_variant_b(
        self,
        *,
        user: User,
        days: int | None,
        amount: Decimal | None,
        description: str | None,
        plan_id: int | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        start_date = now
        if user.subscription_end:
            end_ref = (
                user.subscription_end.replace(tzinfo=timezone.utc)
                if user.subscription_end.tzinfo is None
                else user.subscription_end
            )
            if end_ref > now:
                start_date = end_ref

        plan: SubscriptionPlan | None = None
        if plan_id:
            plan = await self.session.get(SubscriptionPlan, plan_id)
            if plan is None:
                raise ValueError("Указанный тариф не найден")
            days = plan.duration_days
        if days is None:
            raise ValueError("Не указана длительность подписки")

        end_date = start_date + timedelta(days=days)

        payment_id: int | None = None
        if amount is not None:
            payment = Payment(
                bot_id=user.bot_id,
                user_id=user.id,
                amount=amount,
                currency="RUB",
                payment_provider=PaymentProvider.YOOKASSA,
                status=PaymentStatus.SUCCEEDED,
                description=description,
                paid_at=now,
                plan_id=plan_id,
            )
            self.session.add(payment)
            await self.session.flush()
            payment_id = payment.id

        subscription = Subscription(
            bot_id=user.bot_id,
            user_id=user.id,
            payment_id=payment_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_renew=False,
            plan_id=plan_id,
        )
        self.session.add(subscription)
        await self.session.flush()

        # ВАРИАНТ 2: Используем expire для принудительной перезагрузки связей
        self.session.expire(user, ["subscriptions"])
        await self.session.refresh(user, attribute_names=["subscriptions"])
        self._activate_latest_subscription(user)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user, attribute_names=["subscription_end", "is_premium"])

    # ============================================================================
    # ВАРИАНТ 3: Полная переработка с перезагрузкой
    # ============================================================================
    async def _create_subscription_for_user_variant_c(
        self,
        *,
        user: User,
        days: int | None,
        amount: Decimal | None,
        description: str | None,
        plan_id: int | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        start_date = now
        if user.subscription_end:
            end_ref = (
                user.subscription_end.replace(tzinfo=timezone.utc)
                if user.subscription_end.tzinfo is None
                else user.subscription_end
            )
            if end_ref > now:
                start_date = end_ref

        plan: SubscriptionPlan | None = None
        if plan_id:
            plan = await self.session.get(SubscriptionPlan, plan_id)
            if plan is None:
                raise ValueError("Указанный тариф не найден")
            days = plan.duration_days
        if days is None:
            raise ValueError("Не указана длительность подписки")

        end_date = start_date + timedelta(days=days)

        payment_id: int | None = None
        if amount is not None:
            payment = Payment(
                bot_id=user.bot_id,
                user_id=user.id,
                amount=amount,
                currency="RUB",
                payment_provider=PaymentProvider.YOOKASSA,
                status=PaymentStatus.SUCCEEDED,
                description=description,
                paid_at=now,
                plan_id=plan_id,
            )
            self.session.add(payment)
            await self.session.flush()
            payment_id = payment.id

        subscription = Subscription(
            bot_id=user.bot_id,
            user_id=user.id,
            payment_id=payment_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_renew=False,
            plan_id=plan_id,
        )
        self.session.add(subscription)
        await self.session.flush()

        # ВАРИАНТ 3: Полная перезагрузка пользователя с подписками через selectinload
        stmt = (
            select(User)
            .options(
                selectinload(User.subscriptions).selectinload(Subscription.payment),
                selectinload(User.subscriptions).selectinload(Subscription.plan),
            )
            .where(User.id == user.id)
        )
        result = await self.session.execute(stmt)
        user_updated = result.scalar_one()
        
        self._activate_latest_subscription(user_updated)
        self.session.add(user_updated)
        await self.session.flush()
        
        # Обновляем ссылку на пользователя для вызывающего кода
        user.subscription_end = user_updated.subscription_end
        user.is_premium = user_updated.is_premium

    async def _get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User)
                .options(
                    selectinload(User.subscriptions)
                    .selectinload(Subscription.payment),
                    selectinload(User.subscriptions).selectinload(Subscription.plan),
                )
                .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_subscriber_item(self, user_id: int) -> SubscriberListItem:
        user = await self._get_user(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        return self._to_subscriber_list_item(user)

    def _activate_latest_subscription(self, user: User) -> None:
        latest_subscription: Subscription | None = None
        for subscription in user.subscriptions:
            if (
                latest_subscription is None
                or subscription.end_date > latest_subscription.end_date
            ):
                latest_subscription = subscription

        now = datetime.now(timezone.utc)
        if latest_subscription:
            for subscription in user.subscriptions:
                subscription.is_active = subscription is latest_subscription

            end_date = latest_subscription.end_date
            if end_date and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            user.subscription_end = end_date
            user.is_premium = bool(end_date and end_date >= now) and not user.is_blocked
        else:
            user.subscription_end = None
            user.is_premium = False

    def _to_subscriber_list_item(self, user: User) -> SubscriberListItem:
        latest_subscription: Subscription | None = None
        if user.subscriptions:
            latest_subscription = max(user.subscriptions, key=lambda item: item.end_date)

        full_name = " ".join(
            part for part in [user.first_name or "", user.last_name or ""] if part
        ).strip() or (user.username or f"#{user.telegram_id}")

        now = datetime.now(timezone.utc)
        status = "inactive"
        if user.is_blocked:
            status = "blocked"
        elif latest_subscription:
            subscription_end = latest_subscription.end_date
            if subscription_end and subscription_end.tzinfo is None:
                subscription_end = subscription_end.replace(tzinfo=timezone.utc)
            if subscription_end and subscription_end < now:
                status = "expired"
            elif latest_subscription.is_active:
                status = "active"
            else:
                status = "pending"

        if latest_subscription:
            subscription_end = latest_subscription.end_date
            if subscription_end and subscription_end.tzinfo is None:
                subscription_end = subscription_end.replace(tzinfo=timezone.utc)
        else:
            subscription_end = None

        active_subscription_id = latest_subscription.id if latest_subscription else None
        tariff = None
        if latest_subscription:
            if latest_subscription.plan:
                tariff = latest_subscription.plan.name
            elif latest_subscription.payment and latest_subscription.payment.description:
                tariff = latest_subscription.payment.description

        return SubscriberListItem(
            id=user.id,
            bot_id=user.bot_id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=full_name,
            phone_number=user.phone_number,
            tariff=tariff,
            expires_at=subscription_end,
            status=status,
            is_blocked=user.is_blocked,
            active_subscription_id=active_subscription_id,
        )

    async def _resolve_bot_id(self, bot_id: int | None) -> int:
        if bot_id is not None:
            return bot_id

        result = await self.session.execute(select(Bot).order_by(Bot.id.asc()).limit(1))
        bot = result.scalar_one_or_none()
        if bot is None:
            raise ValueError("В системе отсутствуют боты. Сначала создайте бота.")
        return bot.id

    @staticmethod
    def _ensure_timezone(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

