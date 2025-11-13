"""
ВАРИАНТ 2: Исправление метода _create_subscription_for_user
Проблема: После активации подписки пользователь не сохраняется явно
Решение: Добавить явное сохранение пользователя внутри метода создания подписки
"""

async def _create_subscription_for_user(
    self,
    *,
    user: User,
    days: int | None,
    amount: Decimal | None,
    description: str | None,
    plan_id: int | None,
) -> None:
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

    plan: SubscriptionPlan | None = None
    if plan_id:
        plan = await self.session.get(SubscriptionPlan, plan_id)
        if plan is None:
            raise ValueError("Указанный тариф не найден")
        days = plan.duration_days
    if days is None:
        raise ValueError("Не указана длительность подписки")

    end_date = start_date + timedelta(days=days)

    payment_id: int | None = None
    if amount is not None:
        payment = Payment(
            bot_id=user.bot_id,
            user_id=user.id,
            amount=amount,
            currency="RUB",
            payment_provider=PaymentProvider.YOOKASSA,
            status=PaymentStatus.SUCCEEDED,
            description=description,
            paid_at=now,
            plan_id=plan_id,
        )
        self.session.add(payment)
        await self.session.flush()
        payment_id = payment.id

    subscription = Subscription(
        bot_id=user.bot_id,
        user_id=user.id,
        payment_id=payment_id,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        auto_renew=False,
        plan_id=plan_id,
    )
    self.session.add(subscription)
    await self.session.flush()

    # ИСПРАВЛЕНИЕ: Явное сохранение пользователя после активации подписки
    await self.session.refresh(user, attribute_names=["subscriptions"])
    self._activate_latest_subscription(user)
    self.session.add(user)
    await self.session.flush()

