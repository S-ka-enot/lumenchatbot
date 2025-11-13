from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from ..core.config import settings
from ..db.session import AsyncSessionLocal
from ..models import Payment, Subscription, User

logger = logging.getLogger("lumenpay.backups")

TABLES_TO_DUMP = {
    "users": User,
    "payments": Payment,
    "subscriptions": Subscription,
}

BACKUP_FILE_TEMPLATE = "backup-{timestamp}.zip"


def _serialize_instance(instance) -> dict[str, str | int | float | None]:
    mapper = inspect(instance)
    row: dict[str, str | int | float | None] = {}
    for attr in mapper.mapper.column_attrs:
        value = getattr(instance, attr.key)
        if isinstance(value, datetime):
            row[attr.key] = value.astimezone(timezone.utc).isoformat()
        else:
            row[attr.key] = value
    return row


async def _dump_table(session: AsyncSession, model) -> list[dict[str, str | int | float | None]]:
    stmt = select(model)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_serialize_instance(row) for row in rows]


async def _generate_backup_archive(session: AsyncSession, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = target_dir / BACKUP_FILE_TEMPLATE.format(timestamp=timestamp)

    datasets: dict[str, list[dict[str, str | int | float | None]]] = {}
    for table_name, model in TABLES_TO_DUMP.items():
        datasets[table_name] = await _dump_table(session, model)

    with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
        for table_name, rows in datasets.items():
            buffer = io.StringIO()
            fieldnames = rows[0].keys() if rows else []
            writer = csv.DictWriter(buffer, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            archive.writestr(f"{table_name}.csv", buffer.getvalue())

    logger.info("Создан архив резервной копии", extra={"path": str(archive_path)})
    return archive_path


async def _upload_to_yandex(file_path: Path) -> None:
    if not settings.backup_yandex_token:
        return

    token = settings.backup_yandex_token.get_secret_value()
    target_name = file_path.name
    upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {"path": f"app-backups/{target_name}", "overwrite": "true"}
    headers = {"Authorization": f"OAuth {token}"}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(upload_url, params=params, headers=headers)
        response.raise_for_status()
        href = response.json().get("href")
        if not href:
            raise RuntimeError("Не удалось получить ссылку для загрузки на Яндекс.Диск")
        with file_path.open("rb") as fp:
            put_response = await client.put(href, content=fp.read())
            put_response.raise_for_status()

    logger.info("Резервная копия отправлена на Яндекс.Диск", extra={"file": target_name})


async def _send_telegram_document(file_path: Path, caption: str) -> None:
    if not settings.backup_send_to_telegram:
        return
    if not settings.telegram_bot_token or not settings.backup_admin_chat_id:
        logger.warning(
            "Не указан chat_id или токен бота для отправки резервной копии"
        )
        return

    token = settings.telegram_bot_token.get_secret_value()
    chat_id = settings.backup_admin_chat_id
    url = f"https://api.telegram.org/bot{token}/sendDocument"

    async with httpx.AsyncClient(timeout=60) as client:
        with file_path.open("rb") as document:
            form = {
                "chat_id": str(chat_id),
                "caption": caption,
            }
            files = {"document": (file_path.name, document, "application/zip")}
            response = await client.post(url, data=form, files=files)
            response.raise_for_status()

    logger.info("Резервная копия отправлена администратору в Telegram")


def _cleanup_old_backups(target_dir: Path, keep_days: int) -> None:
    if keep_days <= 0:
        return
    threshold = datetime.now(timezone.utc) - timedelta(days=keep_days)
    for file in target_dir.glob("backup-*.zip"):
        try:
            mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if mtime < threshold:
            file.unlink(missing_ok=True)
            logger.info("Удалён устаревший архив", extra={"file": str(file)})


async def create_backup_and_dispatch() -> None:
    target_dir = Path(settings.backup_directory)
    async with AsyncSessionLocal() as session:
        archive_path = await _generate_backup_archive(session, target_dir)

    try:
        await _upload_to_yandex(archive_path)
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        logger.exception("Не удалось отправить резервную копию на Яндекс.Диск")
        await notify_failure(f"Ошибка загрузки резервной копии на Яндекс.Диск: {exc}")

    try:
        caption = (
            f"Резервная копия от {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')}"
        )
        await _send_telegram_document(archive_path, caption)
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        logger.exception("Не удалось отправить резервную копию в Telegram")
        await notify_failure(f"Ошибка отправки резервной копии в Telegram: {exc}")

    _cleanup_old_backups(target_dir, settings.backup_keep_days)


async def notify_failure(message: str) -> None:
    if not settings.backup_send_to_telegram:
        logger.error(message)
        return
    if not settings.telegram_bot_token or not settings.backup_admin_chat_id:
        logger.error(message)
        return

    token = settings.telegram_bot_token.get_secret_value()
    chat_id = settings.backup_admin_chat_id
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json={"chat_id": chat_id, "text": message})
        response.raise_for_status()


async def run_backup_job() -> None:
    if not settings.backup_enabled:
        return
    try:
        await create_backup_and_dispatch()
    except Exception as exc:  # pragma: no cover - защита от сбоев
        logger.exception("Ошибка выполнения резервного копирования")
        await notify_failure(f"Ошибка резервного копирования: {exc}")
