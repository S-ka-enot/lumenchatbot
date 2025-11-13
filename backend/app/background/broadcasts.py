from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from ..db.session import AsyncSessionLocal
from ..models.scheduled_broadcast import BroadcastStatus, ScheduledBroadcast
from ..services.broadcasts import BroadcastService

logger = logging.getLogger(__name__)

_BROADCAST_JOB_ID = "process_scheduled_broadcasts"


async def process_scheduled_broadcasts() -> None:
    """Обрабатывает запланированные рассылки, которые должны быть отправлены"""
    async with AsyncSessionLocal() as session:
        service = BroadcastService(session)
        
        # Получаем все рассылки со статусом PENDING, у которых scheduled_at <= сейчас
        # Используем UTC для сравнения, так как scheduled_at хранится с timezone
        now = datetime.now(timezone.utc)
        stmt = (
            select(ScheduledBroadcast)
            .where(
                ScheduledBroadcast.status == BroadcastStatus.PENDING,
                ScheduledBroadcast.scheduled_at.isnot(None),  # scheduled_at должен быть указан
                ScheduledBroadcast.scheduled_at <= now,
            )
        )
        result = await session.execute(stmt)
        broadcasts = result.scalars().all()
        
        if not broadcasts:
            logger.debug("Нет запланированных рассылок для отправки")
            return
        
        logger.info(f"Найдено {len(broadcasts)} рассылок для отправки")
        
        for broadcast in broadcasts:
            try:
                logger.info(f"Отправка рассылки {broadcast.id}")
                result = await service.send_broadcast_now(broadcast.id)
                logger.info(
                    f"Рассылка {broadcast.id} отправлена: {result.get('sent')} отправлено, "
                    f"{result.get('failed')} ошибок из {result.get('total')} получателей"
                )
            except Exception as exc:
                logger.error(f"Ошибка при отправке рассылки {broadcast.id}: {exc}", exc_info=True)


def setup_broadcast_jobs(scheduler: AsyncIOScheduler) -> None:
    """Настраивает задачи для обработки рассылок"""
    # Удаляем существующую задачу, если есть
    if scheduler.get_job(_BROADCAST_JOB_ID):
        scheduler.remove_job(_BROADCAST_JOB_ID)
    
    # Добавляем задачу на выполнение каждую минуту
    scheduler.add_job(
        process_scheduled_broadcasts,
        "cron",
        minute="*",  # Каждую минуту
        id=_BROADCAST_JOB_ID,
        name="Process scheduled broadcasts",
        replace_existing=True,
    )
    logger.info("Задача обработки запланированных рассылок настроена")

