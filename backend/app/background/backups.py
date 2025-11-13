from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..core.config import settings
from ..services.backups import run_backup_job

_BACKUP_JOB_ID = "daily-backup"


def setup_backup_job(scheduler: AsyncIOScheduler) -> None:
    if not settings.backup_enabled:
        return

    if scheduler.get_job(_BACKUP_JOB_ID):
        return

    try:
        hour_str, minute_str = settings.backup_daily_time.split(":", maxsplit=1)
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, AttributeError):  # pragma: no cover - валидация настроек
        hour = 3
        minute = 0

    scheduler.add_job(
        run_backup_job,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=_BACKUP_JOB_ID,
        replace_existing=True,
        misfire_grace_time=3600,
    )
