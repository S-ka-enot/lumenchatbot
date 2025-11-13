from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.crypto import decrypt_secret
from ..models.bot import Bot
from ..models.channel import Channel
from ..models.subscription_plan import SubscriptionPlan
from ..models.user import User

if TYPE_CHECKING:
    from ..models.subscription import Subscription

logger = logging.getLogger(__name__)


class ChannelAccessService:
    """Сервис для управления доступом пользователей к каналам."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user_to_channels(
        self,
        user: User,
        plan: SubscriptionPlan | None = None,
    ) -> list[dict[str, str | bool]]:
        """
        Добавляет пользователя в каналы, связанные с планом подписки.
        
        Returns:
            Список результатов добавления: [{"channel_name": "...", "success": True/False, "link": "..."}]
        """
        if plan is None:
            # Если план не указан, получаем все активные каналы для бота
            stmt = (
                select(Channel)
                .where(Channel.bot_id == user.bot_id, Channel.is_active.is_(True))
                .where(Channel.requires_subscription.is_(True))
            )
            result = await self.session.execute(stmt)
            channels = result.scalars().all()
        else:
            # Получаем каналы, связанные с планом
            stmt = (
                select(SubscriptionPlan)
                .options(selectinload(SubscriptionPlan.channels))
                .where(SubscriptionPlan.id == plan.id)
            )
            result = await self.session.execute(stmt)
            plan_obj = result.scalar_one_or_none()
            if plan_obj is None:
                logger.warning("План %s не найден", plan.id)
                return []
            
            channels = plan_obj.channels
            # Если у плана нет каналов, получаем все активные каналы для бота, требующие подписку
            if not channels:
                stmt = (
                    select(Channel)
                    .where(Channel.bot_id == user.bot_id, Channel.is_active.is_(True))
                    .where(Channel.requires_subscription.is_(True))
                )
                result = await self.session.execute(stmt)
                channels = result.scalars().all()
                logger.info(
                    "У плана %s нет связанных каналов, используем все активные каналы бота (%d каналов)",
                    plan.id,
                    len(channels),
                )

        if not channels:
            logger.debug("Нет каналов для добавления пользователя %s", user.telegram_id)
            return []

        # Получаем токен бота
        bot = await self.session.get(Bot, user.bot_id)
        if not bot or not bot.telegram_bot_token_encrypted:
            logger.warning("Токен бота %s не настроен", user.bot_id)
            return []

        try:
            encrypted_str = bot.telegram_bot_token_encrypted.decode() if isinstance(bot.telegram_bot_token_encrypted, bytes) else bot.telegram_bot_token_encrypted
            token = decrypt_secret(encrypted_str)
            if not token:
                logger.warning("Не удалось расшифровать токен бота %s", user.bot_id)
                return []
        except Exception as exc:
            logger.warning("Ошибка при расшифровке токена бота %s: %s", user.bot_id, exc)
            return []

        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for channel in channels:
                channel_name = channel.channel_name
                channel_id = channel.channel_id
                invite_link = channel.invite_link
                channel_username = channel.channel_username

                # Пытаемся добавить пользователя в канал
                success = False
                link = invite_link

                # Если есть invite_link, используем его
                if invite_link:
                    link = invite_link
                    # Пытаемся добавить пользователя через unbanChatMember (если был забанен) или через invite link
                    try:
                        # Пытаемся создать ссылку-приглашение, если её нет
                        if not link:
                            # Пытаемся получить или создать invite link
                            chat_id = channel_id
                            if isinstance(chat_id, str):
                                stripped = chat_id.strip()
                                if stripped.lstrip("-").isdigit():
                                    chat_id = int(stripped)
                            
                            # Создаем временную ссылку-приглашение
                            create_link_url = f"https://api.telegram.org/bot{token}/createChatInviteLink"
                            create_link_payload = {
                                "chat_id": chat_id,
                                "creates_join_request": False,
                            }
                            create_response = await client.post(create_link_url, json=create_link_payload)
                            if create_response.status_code == 200:
                                create_data = create_response.json()
                                if create_data.get("ok"):
                                    link = create_data["result"].get("invite_link")
                                    success = True
                    except Exception as exc:
                        logger.debug("Не удалось создать invite link для канала %s: %s", channel_name, exc)

                # Если есть username, формируем ссылку
                if not link and channel_username:
                    link = f"https://t.me/{channel_username.lstrip('@')}"

                # Пытаемся добавить пользователя в канал через unbanChatMember (если был забанен)
                # или просто предоставляем ссылку
                if channel_id:
                    try:
                        chat_id = channel_id
                        if isinstance(chat_id, str):
                            stripped = chat_id.strip()
                            if stripped.lstrip("-").isdigit():
                                chat_id = int(stripped)
                        
                        # Пытаемся разбанить пользователя (если он был забанен)
                        unban_url = f"https://api.telegram.org/bot{token}/unbanChatMember"
                        unban_payload = {
                            "chat_id": chat_id,
                            "user_id": user.telegram_id,
                            "only_if_banned": True,
                        }
                        unban_response = await client.post(unban_url, json=unban_payload)
                        if unban_response.status_code == 200:
                            unban_data = unban_response.json()
                            if unban_data.get("ok"):
                                success = True
                                logger.info("Пользователь %s разбанен в канале %s", user.telegram_id, channel_name)
                    except Exception as exc:
                        logger.debug("Не удалось разбанить пользователя в канале %s: %s", channel_name, exc)

                results.append({
                    "channel_name": channel_name,
                    "success": success,
                    "link": link,
                })

        return results

    async def remove_user_from_channels(
        self,
        user: User,
        channel_ids: list[int] | None = None,
    ) -> list[dict[str, str | bool]]:
        """
        Удаляет пользователя из каналов.
        
        Args:
            user: Пользователь для удаления
            channel_ids: Список ID каналов для удаления. Если None, удаляет из всех каналов бота, требующих подписку.
        
        Returns:
            Список результатов удаления: [{"channel_name": "...", "success": True/False}]
        """
        # Получаем каналы для удаления
        if channel_ids is not None:
            stmt = select(Channel).where(
                Channel.id.in_(channel_ids),
                Channel.bot_id == user.bot_id,
            )
        else:
            # Получаем все активные каналы для бота, требующие подписку
            stmt = (
                select(Channel)
                .where(Channel.bot_id == user.bot_id, Channel.is_active.is_(True))
                .where(Channel.requires_subscription.is_(True))
            )
        
        result = await self.session.execute(stmt)
        channels = result.scalars().all()
        
        if not channels:
            logger.debug("Нет каналов для удаления пользователя %s", user.telegram_id)
            return []

        # Получаем токен бота
        bot = await self.session.get(Bot, user.bot_id)
        if not bot or not bot.telegram_bot_token_encrypted:
            logger.warning("Токен бота %s не настроен, не могу удалить пользователя из каналов", user.bot_id)
            return []

        try:
            encrypted_str = bot.telegram_bot_token_encrypted.decode() if isinstance(bot.telegram_bot_token_encrypted, bytes) else bot.telegram_bot_token_encrypted
            token = decrypt_secret(encrypted_str)
            if not token:
                logger.warning("Не удалось расшифровать токен бота %s", user.bot_id)
                return []
        except Exception as exc:
            logger.warning("Ошибка при расшифровке токена бота %s: %s", user.bot_id, exc)
            return []

        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for channel in channels:
                channel_name = channel.channel_name
                channel_id = channel.channel_id
                success = False

                try:
                    # Преобразуем channel_id в число, если это строка
                    chat_id = channel_id
                    if isinstance(chat_id, str):
                        stripped = chat_id.strip()
                        if stripped.lstrip("-").isdigit():
                            chat_id = int(stripped)
                    
                    # Удаляем пользователя из канала через banChatMember
                    # Используем ban, чтобы пользователь не мог вернуться по старой invite-ссылке
                    ban_url = f"https://api.telegram.org/bot{token}/banChatMember"
                    ban_payload = {
                        "chat_id": chat_id,
                        "user_id": user.telegram_id,
                    }
                    ban_response = await client.post(ban_url, json=ban_payload)
                    
                    if ban_response.status_code == 200:
                        ban_data = ban_response.json()
                        if ban_data.get("ok"):
                            success = True
                            logger.info(
                                "Пользователь %s удален из канала %s (ID: %s)",
                                user.telegram_id,
                                channel_name,
                                channel_id,
                            )
                        else:
                            error_description = ban_data.get("description", "Unknown error")
                            logger.warning(
                                "Не удалось удалить пользователя %s из канала %s: %s",
                                user.telegram_id,
                                channel_name,
                                error_description,
                            )
                    else:
                        error_text = ban_response.text
                        logger.warning(
                            "Ошибка при удалении пользователя %s из канала %s: HTTP %s - %s",
                            user.telegram_id,
                            channel_name,
                            ban_response.status_code,
                            error_text,
                        )
                except Exception as exc:
                    logger.error(
                        "Исключение при удалении пользователя %s из канала %s: %s",
                        user.telegram_id,
                        channel_name,
                        exc,
                        exc_info=True,
                    )

                results.append({
                    "channel_name": channel_name,
                    "success": success,
                })

        return results

