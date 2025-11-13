"""
ВАРИАНТ 3: Полная переработка метода extend_subscription
Проблема: Недостаточная валидация и обработка ошибок
Решение: Полностью переписать логику с явной валидацией и обработкой всех случаев
"""

async def extend_subscription(
    self, user_id: int, payload: SubscriptionExtendRequest
) -> SubscriberListItem:
    try:
        # Загружаем пользователя со всеми связями
        user = await self._get_user(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        # Валидация входных данных
        if not payload.days and not payload.plan_id:
            raise ValueError("Необходимо указать количество дней или ID тарифа")

        # Определяем длительность подписки
        days = payload.days
        plan: SubscriptionPlan | None = None
        if payload.plan_id:
            plan = await self.session.get(SubscriptionPlan, payload.plan_id)
            if plan is None:
                raise ValueError("Указанный тариф не найден")
            days = plan.duration_days
        
        if days is None or days <= 0:
            raise ValueError("Не указана длительность подписки или она некорректна")

        # Вычисляем даты начала и окончания
        now = datetime.now(timezone.utc)
        start_date = now
        if user.subscription_end:
            end_ref = (
                user.subscription_end.replace(tzinfo=timezone.utc)
                if user.subscription_end.tzinfo is None
                else user.subscription_end
            )
            if end_ref > now:
                start_date = end_ref

        end_date = start_date + timedelta(days=days)

        # Создаем платеж, если указана сумма
        payment_id: int | None = None
        if payload.amount is not None and payload.amount > 0:
            payment = Payment(
                bot_id=user.bot_id,
                user_id=user.id,
                amount=payload.amount,
                currency="RUB",
                payment_provider=PaymentProvider.YOOKASSA,
                status=PaymentStatus.SUCCEEDED,
                description=payload.description or "Продление через админку",
                paid_at=now,
                plan_id=payload.plan_id,
            )
            self.session.add(payment)
            await self.session.flush()
            payment_id = payment.id

        # Создаем подписку
        subscription = Subscription(
            bot_id=user.bot_id,
            user_id=user.id,
            payment_id=payment_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_renew=False,
            plan_id=payload.plan_id,
        )
        self.session.add(subscription)
        await self.session.flush()

        # Обновляем пользователя: загружаем подписки и активируем последнюю
        await self.session.refresh(user, attribute_names=["subscriptions"])
        self._activate_latest_subscription(user)
        self.session.add(user)
        await self.session.flush()
        
        # Финальный коммит всех изменений
        await self.session.commit()
        
        # Перезагружаем пользователя для получения актуальных данных
        await self.session.refresh(user, attribute_names=["subscriptions", "subscription_end", "is_premium"])
        
        logger.info(
            "Продлена подписка подписчика",
            extra={
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "days": days,
                "plan_id": payload.plan_id,
                "subscription_id": subscription.id,
            },
        )
        return await self._get_subscriber_item(user.id)
    except ValueError as exc:
        await self.session.rollback()
        raise
    except Exception as exc:
        await self.session.rollback()
        logger.error(
            "Ошибка при продлении подписки",
            extra={"user_id": user_id, "error": str(exc)},
            exc_info=True,
        )
        raise

