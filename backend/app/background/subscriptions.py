from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..db.session import AsyncSessionLocal
from ..models.subscription import Subscription
from ..models.user import User
from ..services.user_notifications import UserNotificationService

logger = logging.getLogger(__name__)

# Отслеживаем, какие уведомления уже были отправлены
# Формат: {(user_id, days_left): timestamp}
_sent_notifications: dict[tuple[int, int], datetime] = {}


async def _check_expiring_subscriptions() -> None:
    """Проверяет истекающие подписки и отправляет напоминания."""
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        
        # Проверяем подписки, которые истекают через 7, 3 и 1 день
        reminder_days = [7, 3, 1]
        
        for days_left in reminder_days:
            target_date = now + timedelta(days=days_left)
            # Проверяем подписки, которые истекают в диапазоне ±12 часов от целевой даты
            start_date = target_date - timedelta(hours=12)
            end_date = target_date + timedelta(hours=12)
            
            stmt = (
                select(Subscription)
                .options(joinedload(Subscription.user))
                .where(
                    Subscription.is_active == True,  # noqa: E712
                    Subscription.end_date >= start_date,
                    Subscription.end_date <= end_date,
                )
            )
            
            result = await session.execute(stmt)
            subscriptions = result.scalars().unique().all()
            
            notification_service = UserNotificationService(session)
            
            for subscription in subscriptions:
                if subscription.user is None:
                    continue
                
                # Вычисляем точное количество дней до истечения
                actual_days_left = (subscription.end_date - now).days
                
                # Проверяем, нужно ли отправить уведомление для этого количества дней
                if actual_days_left not in reminder_days:
                    continue
                
                # Проверяем, не отправляли ли мы уже уведомление для этого пользователя и количества дней
                notification_key = (subscription.user_id, actual_days_left)
                last_sent = _sent_notifications.get(notification_key)
                
                # Отправляем уведомление, если:
                # 1. Еще не отправляли для этого пользователя и количества дней
                # 2. Или последнее уведомление было более 20 часов назад (чтобы не спамить при повторных запусках)
                should_send = (
                    last_sent is None or 
                    (now - last_sent) > timedelta(hours=20)
                )
                
                if should_send:
                    try:
                        success = await notification_service.send_subscription_expiring_notification(
                            user=subscription.user,
                            days_left=actual_days_left,
                            subscription_end=subscription.end_date,
                        )
                        if success:
                            _sent_notifications[notification_key] = now
                            logger.info(
                                "Отправлено напоминание об истечении подписки",
                                extra={
                                    "user_id": subscription.user_id,
                                    "subscription_id": subscription.id,
                                    "days_left": actual_days_left,
                                },
                            )
                    except Exception as exc:
                        logger.exception(
                            "Ошибка при отправке напоминания об истечении подписки: %s",
                            exc,
                            extra={
                                "user_id": subscription.user_id,
                                "subscription_id": subscription.id,
                                "days_left": actual_days_left,
                            },
                        )


async def _check_expired_subscriptions() -> None:
    """Проверяет истекшие подписки и отправляет уведомления."""
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        
        # Проверяем подписки, которые истекли в последние 24 часа
        # (чтобы не отправлять уведомления для старых истекших подписок)
        expired_start = now - timedelta(days=1)
        
        stmt = (
            select(Subscription)
            .options(joinedload(Subscription.user))
            .where(
                Subscription.is_active == True,  # noqa: E712
                Subscription.end_date < now,
                Subscription.end_date >= expired_start,
            )
        )
        
        result = await session.execute(stmt)
        subscriptions = result.scalars().unique().all()
        
        notification_service = UserNotificationService(session)
        
        for subscription in subscriptions:
            if subscription.user is None:
                continue
            
            # Проверяем, не отправляли ли мы уже уведомление об истечении
            notification_key = (subscription.user_id, 0)  # 0 означает истекшая подписка
            last_sent = _sent_notifications.get(notification_key)
            
            # Отправляем уведомление, если еще не отправляли или прошло более 20 часов
            should_send = (
                last_sent is None or 
                (now - last_sent) > timedelta(hours=20)
            )
            
            if should_send:
                try:
                    # Деактивируем подписку
                    subscription.is_active = False
                    if subscription.user:
                        subscription.user.is_premium = False
                    session.add(subscription)
                    if subscription.user:
                        session.add(subscription.user)
                    
                    success = await notification_service.send_subscription_expired_notification(
                        user=subscription.user,
                    )
                    
                    if success:
                        _sent_notifications[notification_key] = now
                        logger.info(
                            "Отправлено уведомление об истечении подписки",
                            extra={
                                "user_id": subscription.user_id,
                                "subscription_id": subscription.id,
                            },
                        )
                    
                    await session.commit()
                except Exception as exc:
                    await session.rollback()
                    logger.exception(
                        "Ошибка при обработке истекшей подписки: %s",
                        exc,
                        extra={
                            "user_id": subscription.user_id,
                            "subscription_id": subscription.id,
                        },
                    )


def setup_subscription_jobs(scheduler: AsyncIOScheduler) -> None:
    """Настраивает фоновые задачи для проверки подписок."""
    # Проверяем истекающие подписки каждый день в 10:00
    scheduler.add_job(
        _check_expiring_subscriptions,
        trigger="cron",
        hour=10,
        minute=0,
        id="check_expiring_subscriptions",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    
    # Проверяем истекшие подписки каждый час
    scheduler.add_job(
        _check_expired_subscriptions,
        trigger="interval",
        hours=1,
        id="check_expired_subscriptions",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

