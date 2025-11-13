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
from ..services.channel_access import ChannelAccessService
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
                    Subscription.expires_at >= start_date,
                    Subscription.expires_at <= end_date,
                )
            )
            
            result = await session.execute(stmt)
            subscriptions = result.scalars().unique().all()
            
            notification_service = UserNotificationService(session)
            
            for subscription in subscriptions:
                if subscription.user is None:
                    continue
                
                # Вычисляем точное количество дней до истечения
                actual_days_left = (subscription.expires_at - now).days
                
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
                            subscription_end=subscription.expires_at,
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


async def _remove_users_without_subscriptions() -> None:
    """Удаляет из каналов пользователей, у которых нет активных подписок."""
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        
        # Получаем всех пользователей, у которых нет активных подписок
        # но они помечены как premium или имеют subscription_end в будущем
        stmt = (
            select(User)
            .options(joinedload(User.subscriptions))
            .where(
                User.is_premium == True,  # noqa: E712
            )
        )
        
        result = await session.execute(stmt)
        users = result.scalars().unique().all()
        
        channel_service = ChannelAccessService(session)
        removed_count = 0
        
        for user in users:
            # Проверяем, есть ли у пользователя активные подписки
            active_subscriptions = [
                sub for sub in user.subscriptions
                if sub.is_active and sub.expires_at > now
            ]
            
            # Если нет активных подписок, но пользователь помечен как premium
            if not active_subscriptions:
                # Обновляем статус пользователя
                user.is_premium = False
                user.subscription_end = None
                session.add(user)
                
                # Удаляем пользователя из всех каналов, требующих подписку
                remove_results = await channel_service.remove_user_from_channels(
                    user=user,
                    channel_ids=None,  # Удаляем из всех каналов
                )
                
                success_count = sum(1 for r in remove_results if r.get("success"))
                if success_count > 0:
                    removed_count += 1
                    logger.info(
                        "Пользователь %s (telegram_id: %s) удален из %d каналов (нет активных подписок)",
                        user.id,
                        user.telegram_id,
                        success_count,
                    )
        
        if removed_count > 0:
            await session.commit()
            logger.info("Удалено %d пользователей без активных подписок из каналов", removed_count)
        else:
            logger.debug("Нет пользователей без активных подписок для удаления из каналов")


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
                Subscription.expires_at < now,
                Subscription.expires_at >= expired_start,
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
                    
                    # Удаляем пользователя из каналов, если у него нет других активных подписок
                    if subscription.user:
                        # Проверяем, есть ли у пользователя другие активные подписки
                        other_active_stmt = (
                            select(Subscription)
                            .where(
                                Subscription.user_id == subscription.user_id,
                                Subscription.id != subscription.id,
                                Subscription.is_active == True,  # noqa: E712
                                Subscription.expires_at > now,
                            )
                        )
                        other_active_result = await session.execute(other_active_stmt)
                        other_active = other_active_result.scalars().all()
                        
                        # Если нет других активных подписок, удаляем пользователя из каналов
                        if not other_active:
                            channel_service = ChannelAccessService(session)
                            # Получаем каналы, связанные с истекшей подпиской
                            channel_ids = None
                            if subscription.channel_id:
                                channel_ids = [subscription.channel_id]
                            
                            remove_results = await channel_service.remove_user_from_channels(
                                user=subscription.user,
                                channel_ids=channel_ids,
                            )
                            
                            removed_count = sum(1 for r in remove_results if r.get("success"))
                            logger.info(
                                "Пользователь %s удален из %d каналов после истечения подписки",
                                subscription.user_id,
                                removed_count,
                            )
                    
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
    
    # Проверяем и удаляем пользователей без активных подписок из каналов каждый день в 3:00
    scheduler.add_job(
        _remove_users_without_subscriptions,
        trigger="cron",
        hour=3,
        minute=0,
        id="remove_users_without_subscriptions",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

