from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..db.session import AsyncSessionLocal
from ..services.payments import PaymentService

logger = logging.getLogger(__name__)


async def _sync_pending_payments() -> None:
    async with AsyncSessionLocal() as session:
        service = PaymentService(session)
        try:
            await service.sync_pending_yookassa_payments()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Не удалось синхронизировать платежи YooKassa: %s", exc)


def setup_payment_jobs(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        _sync_pending_payments,
        trigger="interval",
        minutes=2,
        id="sync_yookassa_payments",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

