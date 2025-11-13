"""
ВАРИАНТ A: Минимальные изменения с явным сохранением пользователя
Подход: Добавляем явное сохранение пользователя после создания подписки
Преимущества: Минимальные изменения, простое решение
"""

# ============================================================================
# МЕТОД 1: extend_subscription
# ============================================================================
# ЗАМЕНИТЬ в файле backend/app/services/users.py строки 319-351
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
        
        # ВАРИАНТ A: Явное обновление пользователя перед коммитом
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


# ============================================================================
# МЕТОД 2: create_subscriber
# ============================================================================
# ЗАМЕНИТЬ в файле backend/app/services/users.py строки 227-283
async def create_subscriber(self, payload: SubscriberCreate) -> SubscriberListItem:
    try:
        bot_id = await self._resolve_bot_id(payload.bot_id)

        # Check for existing user with the same Telegram ID or phone number
        conditions = [User.bot_id == bot_id, User.telegram_id == payload.telegram_id]
        stmt = select(User).where(*conditions)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ValueError("Пользователь с таким Telegram ID уже существует")

        if payload.phone_number:
            phone_stmt = select(User).where(
                User.bot_id == bot_id, User.phone_number == payload.phone_number
            )
            phone_result = await self.session.execute(phone_stmt)
            if phone_result.scalar_one_or_none() is not None:
                raise ValueError("Пользователь с таким номером телефона уже существует")

        user = User(
            bot_id=bot_id,
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            is_blocked=payload.is_blocked or False,
        )
        self.session.add(user)
        await self.session.flush()

        if payload.subscription_days or payload.plan_id:
            await self._create_subscription_for_user(
                user=user,
                days=payload.subscription_days,
                amount=payload.subscription_amount,
                description=payload.subscription_description,
                plan_id=payload.plan_id,
            )
            # ВАРИАНТ A: Явное обновление пользователя после создания подписки
            await self.session.refresh(user, attribute_names=["subscriptions", "subscription_end", "is_premium"])

        await self.session.commit()
        logger.info(
            "Создан новый подписчик",
            extra={
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "bot_id": bot_id,
                "has_subscription": bool(payload.subscription_days or payload.plan_id),
            },
        )
        return await self._get_subscriber_item(user.id)
    except Exception:
        await self.session.rollback()
        raise


# ============================================================================
# МЕТОД 3: _create_subscription_for_user
# ============================================================================
# ЗАМЕНИТЬ в файле backend/app/services/users.py строки 449-517
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

    # ВАРИАНТ A: Минимальное исправление - только активация подписки
    await self.session.refresh(user, attribute_names=["subscriptions"])
    self._activate_latest_subscription(user)
    # Явно добавляем пользователя для сохранения изменений
    self.session.add(user)
    await self.session.flush()

