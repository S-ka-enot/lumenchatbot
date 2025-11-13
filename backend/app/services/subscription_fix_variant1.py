"""
ВАРИАНТ 1: Исправление метода extend_subscription
Проблема: После создания подписки пользователь не обновляется явно
Решение: Добавить явное обновление пользователя после создания подписки
"""

async def extend_subscription(
    self, user_id: int, payload: SubscriptionExtendRequest
) -> SubscriberListItem:
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
        
        # ИСПРАВЛЕНИЕ: Явное обновление пользователя после создания подписки
        self.session.add(user)
        await self.session.flush()
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

