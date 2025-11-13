from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.crypto import decrypt_secret
from ..models.bot import Bot
from ..models.channel import Channel
from ..models.scheduled_broadcast import (
    BroadcastAudience,
    BroadcastStatus,
    ParseMode,
    ScheduledBroadcast,
)
from ..models.subscription import Subscription
from ..models.user import User
from ..schemas.broadcast import BroadcastCreate, BroadcastRead, BroadcastUpdate

logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_broadcasts(
        self, page: int = 1, size: int = 50, bot_id: int | None = None
    ) -> tuple[list[BroadcastRead], int]:
        offset = (page - 1) * size

        # Базовый запрос
        stmt: Select[tuple[ScheduledBroadcast]] = select(ScheduledBroadcast)
        count_stmt = select(func.count(ScheduledBroadcast.id))

        # Фильтр по bot_id если указан
        if bot_id is not None:
            stmt = stmt.where(ScheduledBroadcast.bot_id == bot_id)
            count_stmt = count_stmt.where(ScheduledBroadcast.bot_id == bot_id)

        # Получаем общее количество
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one() or 0

        # Получаем страницу данных
        stmt = (
            stmt.options(
                selectinload(ScheduledBroadcast.bot),
                selectinload(ScheduledBroadcast.channel),
            )
            .order_by(ScheduledBroadcast.created_at.desc())
            .limit(size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        broadcasts = result.scalars().unique().all()
        items = [self._to_broadcast_read(broadcast) for broadcast in broadcasts]
        return items, total

    async def get_broadcast(self, broadcast_id: int) -> BroadcastRead | None:
        stmt = (
            select(ScheduledBroadcast)
            .where(ScheduledBroadcast.id == broadcast_id)
            .options(
                selectinload(ScheduledBroadcast.bot),
                selectinload(ScheduledBroadcast.channel),
            )
        )
        result = await self.session.execute(stmt)
        broadcast = result.scalar_one_or_none()
        if broadcast is None:
            return None
        return self._to_broadcast_read(broadcast)

    async def create_broadcast(self, payload: BroadcastCreate) -> BroadcastRead:
        # Проверяем существование бота
        bot_stmt = select(Bot).where(Bot.id == payload.bot_id)
        bot_result = await self.session.execute(bot_stmt)
        bot = bot_result.scalar_one_or_none()
        if bot is None:
            raise ValueError(f"Бот с ID {payload.bot_id} не найден")

        # Проверяем существование канала если указан
        channel = None
        if payload.channel_id is not None:
            channel_stmt = select(Channel).where(Channel.id == payload.channel_id)
            channel_result = await self.session.execute(channel_stmt)
            channel = channel_result.scalar_one_or_none()
            if channel is None:
                raise ValueError(f"Канал с ID {payload.channel_id} не найден")
            if channel.bot_id != payload.bot_id:
                raise ValueError("Канал не принадлежит указанному боту")

        broadcast = ScheduledBroadcast(
            bot_id=payload.bot_id,
            channel_id=payload.channel_id,
            message_title=payload.message_title,
            message_text=payload.message_text,
            parse_mode=ParseMode(payload.parse_mode or "None"),
            target_audience=BroadcastAudience(payload.target_audience),
            user_ids=payload.user_ids or [],
            birthday_only=payload.birthday_only,
            media_files=payload.media_files or [],
            scheduled_at=payload.scheduled_at,
            status=BroadcastStatus(payload.status or "draft"),
            buttons=payload.buttons or {},
        )
        self.session.add(broadcast)
        await self.session.commit()
        await self.session.refresh(broadcast)
        return self._to_broadcast_read(broadcast)

    async def update_broadcast(
        self, broadcast_id: int, payload: BroadcastUpdate
    ) -> BroadcastRead:
        stmt = (
            select(ScheduledBroadcast)
            .where(ScheduledBroadcast.id == broadcast_id)
            .options(
                selectinload(ScheduledBroadcast.bot),
                selectinload(ScheduledBroadcast.channel),
            )
        )
        result = await self.session.execute(stmt)
        broadcast = result.scalar_one_or_none()
        if broadcast is None:
            raise ValueError(f"Рассылка с ID {broadcast_id} не найдена")

        # Обновляем поля
        if payload.channel_id is not None:
            if payload.channel_id != broadcast.channel_id:
                channel_stmt = select(Channel).where(Channel.id == payload.channel_id)
                channel_result = await self.session.execute(channel_stmt)
                channel = channel_result.scalar_one_or_none()
                if channel is None:
                    raise ValueError(f"Канал с ID {payload.channel_id} не найден")
                if channel.bot_id != broadcast.bot_id:
                    raise ValueError("Канал не принадлежит боту рассылки")
                broadcast.channel_id = payload.channel_id

        if payload.message_title is not None:
            broadcast.message_title = payload.message_title
        if payload.message_text is not None:
            broadcast.message_text = payload.message_text
        if payload.parse_mode is not None:
            broadcast.parse_mode = ParseMode(payload.parse_mode)
        if payload.target_audience is not None:
            broadcast.target_audience = BroadcastAudience(payload.target_audience)
        if payload.user_ids is not None:
            broadcast.user_ids = payload.user_ids
        if payload.birthday_only is not None:
            broadcast.birthday_only = payload.birthday_only
        if payload.media_files is not None:
            broadcast.media_files = payload.media_files
        if payload.scheduled_at is not None:
            broadcast.scheduled_at = payload.scheduled_at
        if payload.status is not None:
            broadcast.status = BroadcastStatus(payload.status)
        if payload.buttons is not None:
            broadcast.buttons = payload.buttons

        await self.session.commit()
        await self.session.refresh(broadcast)
        return self._to_broadcast_read(broadcast)

    async def delete_broadcast(self, broadcast_id: int) -> None:
        stmt = select(ScheduledBroadcast).where(ScheduledBroadcast.id == broadcast_id)
        result = await self.session.execute(stmt)
        broadcast = result.scalar_one_or_none()
        if broadcast is None:
            raise ValueError(f"Рассылка с ID {broadcast_id} не найдена")
        await self.session.delete(broadcast)
        await self.session.commit()

    async def get_recipients_count(
        self, broadcast: ScheduledBroadcast
    ) -> int:
        """Подсчитывает количество получателей рассылки"""
        # Начинаем с базового запроса пользователей
        base_query = select(User.id).where(User.bot_id == broadcast.bot_id)

        # Фильтр по дню рождения
        if broadcast.birthday_only:
            today = date.today()
            base_query = base_query.where(
                func.date_part("month", User.birthday) == today.month,
                func.date_part("day", User.birthday) == today.day,
            )

        # Фильтр по статусу подписки
        if broadcast.target_audience == BroadcastAudience.ALL:
            pass  # Без фильтра
        elif broadcast.target_audience == BroadcastAudience.SUBSCRIBERS:
            base_query = base_query.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == True
            )
        elif broadcast.target_audience == BroadcastAudience.ACTIVE_SUBSCRIBERS:
            now = datetime.now(timezone.utc)
            base_query = base_query.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == True, Subscription.end_date > now
            )
        elif broadcast.target_audience == BroadcastAudience.EXPIRED_SUBSCRIBERS:
            now = datetime.now(timezone.utc)
            base_query = base_query.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == False, Subscription.end_date < now
            )
        elif broadcast.target_audience == BroadcastAudience.EXPIRING_SOON:
            now = datetime.now(timezone.utc)
            three_days_later = now + timedelta(days=3)
            base_query = base_query.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == True,
                Subscription.end_date > now,
                Subscription.end_date <= three_days_later,
            )
        elif broadcast.target_audience == BroadcastAudience.NON_SUBSCRIBERS:
            base_query = base_query.outerjoin(Subscription, User.id == Subscription.user_id).where(
                Subscription.id == None
            )
        elif broadcast.target_audience == BroadcastAudience.BIRTHDAY:
            today = date.today()
            base_query = base_query.where(
                func.date_part("month", User.birthday) == today.month,
                func.date_part("day", User.birthday) == today.day,
            )
        elif broadcast.target_audience == BroadcastAudience.CUSTOM:
            if broadcast.user_ids:
                base_query = base_query.where(User.id.in_(broadcast.user_ids))
            else:
                return 0

        # Исключаем заблокированных пользователей
        base_query = base_query.where(User.is_blocked == False)

        # Подсчитываем количество уникальных пользователей
        count_stmt = select(func.count()).select_from(base_query.distinct().subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one() or 0

    async def send_broadcast_now(self, broadcast_id: int) -> dict[str, Any]:
        """Отправляет рассылку немедленно всем получателям"""
        stmt = (
            select(ScheduledBroadcast)
            .where(ScheduledBroadcast.id == broadcast_id)
            .options(
                selectinload(ScheduledBroadcast.bot),
            )
        )
        result = await self.session.execute(stmt)
        broadcast = result.scalar_one_or_none()
        if broadcast is None:
            raise ValueError(f"Рассылка с ID {broadcast_id} не найдена")

        if broadcast.status == BroadcastStatus.COMPLETED:
            raise ValueError("Рассылка уже была отправлена")

        # Получаем список получателей
        recipients = await self._get_recipients(broadcast)
        
        if not recipients:
            raise ValueError("Нет получателей для рассылки")

        # Получаем токен бота
        bot = await self.session.get(Bot, broadcast.bot_id)
        if not bot or not bot.telegram_bot_token_encrypted:
            raise ValueError("Токен бота не настроен")

        try:
            encrypted_str = (
                bot.telegram_bot_token_encrypted.decode()
                if isinstance(bot.telegram_bot_token_encrypted, bytes)
                else bot.telegram_bot_token_encrypted
            )
            token = decrypt_secret(encrypted_str)
            if not token:
                raise ValueError("Не удалось расшифровать токен бота")
        except Exception as exc:
            raise ValueError(f"Ошибка при расшифровке токена: {exc}") from exc

        # Формируем текст сообщения
        message_text = broadcast.message_text
        if broadcast.message_title:
            message_text = f"{broadcast.message_title}\n\n{message_text}"

        # Определяем parse_mode
        parse_mode = None
        if broadcast.parse_mode and broadcast.parse_mode != ParseMode.NONE:
            parse_mode = broadcast.parse_mode.value.lower()

        # Обновляем статус на "отправляется"
        broadcast.status = BroadcastStatus.SENDING
        broadcast.scheduled_at = datetime.now(timezone.utc)
        await self.session.commit()

        # Отправляем сообщения
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        sent_count = 0
        failed_count = 0
        errors = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, user in enumerate(recipients):
                # Добавляем небольшую задержку между отправками (30 сообщений в секунду - лимит Telegram)
                if idx > 0 and idx % 30 == 0:
                    await asyncio.sleep(1)

                payload = {
                    "chat_id": user.telegram_id,
                    "text": message_text,
                }
                if parse_mode:
                    payload["parse_mode"] = parse_mode

                # Если есть медиа файлы, отправляем их
                if broadcast.media_files:
                    # Для первой фотографии используем sendPhoto с caption
                    first_media = broadcast.media_files[0]
                    if first_media.get("type") == "photo" and first_media.get("file_id"):
                        photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
                        photo_payload = {
                            "chat_id": user.telegram_id,
                            "photo": first_media["file_id"],
                            "caption": message_text,
                        }
                        if parse_mode:
                            photo_payload["parse_mode"] = parse_mode
                        try:
                            response = await client.post(photo_url, json=photo_payload)
                            response.raise_for_status()
                            sent_count += 1
                            continue
                        except Exception as e:
                            errors.append(f"User {user.telegram_id}: {str(e)}")
                            failed_count += 1
                            continue

                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    sent_count += 1
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 403:
                        # Пользователь заблокировал бота - это нормально
                        failed_count += 1
                    else:
                        errors.append(f"User {user.telegram_id}: HTTP {exc.response.status_code}")
                        failed_count += 1
                except Exception as e:
                    errors.append(f"User {user.telegram_id}: {str(e)}")
                    failed_count += 1

        # Обновляем статус и статистику
        broadcast.status = BroadcastStatus.COMPLETED
        broadcast.sent_at = datetime.now(timezone.utc)
        broadcast.stats = {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(recipients),
            "errors": errors[:10],  # Сохраняем только первые 10 ошибок
        }
        await self.session.commit()

        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(recipients),
        }

    async def _get_recipients(self, broadcast: ScheduledBroadcast) -> list[User]:
        """Получает список получателей рассылки"""
        stmt = select(User).where(User.bot_id == broadcast.bot_id)

        # Фильтр по дню рождения
        if broadcast.birthday_only:
            today = date.today()
            stmt = stmt.where(
                func.date_part("month", User.birthday) == today.month,
                func.date_part("day", User.birthday) == today.day,
            )

        # Фильтр по статусу подписки
        if broadcast.target_audience == BroadcastAudience.ALL:
            pass  # Без фильтра
        elif broadcast.target_audience == BroadcastAudience.SUBSCRIBERS:
            stmt = stmt.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == True
            )
        elif broadcast.target_audience == BroadcastAudience.ACTIVE_SUBSCRIBERS:
            now = datetime.now(timezone.utc)
            stmt = stmt.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == True, Subscription.end_date > now
            )
        elif broadcast.target_audience == BroadcastAudience.EXPIRED_SUBSCRIBERS:
            now = datetime.now(timezone.utc)
            stmt = stmt.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == False, Subscription.end_date < now
            )
        elif broadcast.target_audience == BroadcastAudience.EXPIRING_SOON:
            now = datetime.now(timezone.utc)
            three_days_later = now + timedelta(days=3)
            stmt = stmt.join(Subscription, User.id == Subscription.user_id).where(
                Subscription.is_active == True,
                Subscription.end_date > now,
                Subscription.end_date <= three_days_later,
            )
        elif broadcast.target_audience == BroadcastAudience.NON_SUBSCRIBERS:
            stmt = stmt.outerjoin(Subscription, User.id == Subscription.user_id).where(
                Subscription.id == None
            )
        elif broadcast.target_audience == BroadcastAudience.BIRTHDAY:
            today = date.today()
            stmt = stmt.where(
                func.date_part("month", User.birthday) == today.month,
                func.date_part("day", User.birthday) == today.day,
            )
        elif broadcast.target_audience == BroadcastAudience.CUSTOM:
            if broadcast.user_ids:
                stmt = stmt.where(User.id.in_(broadcast.user_ids))
            else:
                return []

        # Исключаем заблокированных пользователей
        stmt = stmt.where(User.is_blocked == False).distinct()

        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    def _to_broadcast_read(self, broadcast: ScheduledBroadcast) -> BroadcastRead:
        return BroadcastRead(
            id=broadcast.id,
            bot_id=broadcast.bot_id,
            channel_id=broadcast.channel_id,
            message_title=broadcast.message_title,
            message_text=broadcast.message_text,
            parse_mode=broadcast.parse_mode.value if broadcast.parse_mode else "None",
            target_audience=broadcast.target_audience.value,
            user_ids=broadcast.user_ids or [],
            birthday_only=broadcast.birthday_only,
            media_files=broadcast.media_files or [],
            scheduled_at=broadcast.scheduled_at,
            sent_at=broadcast.sent_at,
            status=broadcast.status.value,
            stats=broadcast.stats or {},
            buttons=broadcast.buttons or {},
            created_at=broadcast.created_at,
            updated_at=broadcast.updated_at,
        )

