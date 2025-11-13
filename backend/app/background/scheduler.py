from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..core.config import settings
from .backups import setup_backup_job
from .broadcasts import setup_broadcast_jobs
from .payments import setup_payment_jobs
from .subscriptions import setup_subscription_jobs

scheduler = AsyncIOScheduler(timezone=settings.timezone)


def start_scheduler() -> None:
    if not scheduler.running:
        setup_backup_job(scheduler)
        setup_payment_jobs(scheduler)
        setup_subscription_jobs(scheduler)
        setup_broadcast_jobs(scheduler)
        scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

