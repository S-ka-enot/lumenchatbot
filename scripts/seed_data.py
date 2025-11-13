from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.bot import Bot
from backend.app.models.payment import Payment, PaymentProvider, PaymentStatus
from backend.app.models.subscription import Subscription
from backend.app.models.user import User


async def ensure_bot(session, slug: str, name: str) -> Bot:
    result = await session.execute(select(Bot).where(Bot.slug == slug))
    bot = result.scalar_one_or_none()
    if bot:
        return bot
    bot = Bot(name=name, slug=slug)
    session.add(bot)
    await session.commit()
    await session.refresh(bot)
    return bot


async def ensure_user(session, bot: Bot, telegram_id: int, first_name: str, last_name: str) -> User:
    result = await session.execute(
        select(User).where(User.bot_id == bot.id, User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(
        bot_id=bot.id,
        telegram_id=telegram_id,
        username=f"{first_name.lower()}_{last_name.lower()}",
        first_name=first_name,
        last_name=last_name,
        is_premium=True,
        subscription_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_payment_and_subscription(
    session,
    bot: Bot,
    user: User,
    amount: Decimal,
    *,
    description: str,
    days: int = 30,
) -> None:
    now = datetime.now(timezone.utc)
    payment = Payment(
        bot_id=bot.id,
        user_id=user.id,
        amount=amount,
        currency="RUB",
        payment_provider=PaymentProvider.YOOKASSA,
        status=PaymentStatus.SUCCEEDED,
        description=description,
        paid_at=now,
    )
    session.add(payment)
    await session.flush()

    subscription = Subscription(
        bot_id=bot.id,
        user_id=user.id,
        channel_id=1,  # Временное значение, нужно получить из плана
        payment_id=payment.id,
        started_at=now,
        expires_at=now + timedelta(days=days),
        is_active=True,
        auto_renew=False,
    )
    session.add(subscription)
    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        bot = await ensure_bot(session, slug="lumenpay", name="LumenPay Bot")
        user = await ensure_user(session, bot, telegram_id=123456789, first_name="Мария", last_name="Соколова")

        existing_payments = await session.execute(
            select(Payment).where(Payment.user_id == user.id).limit(1)
        )
        if existing_payments.scalar_one_or_none() is None:
            await create_payment_and_subscription(
                session,
                bot,
                user,
                Decimal("1990.00"),
                description="Подписка Lumen Premium",
            )
            print("Создан тестовый платёж и подписка")
        else:
            print("Платежи уже существуют, пропускаю")


if __name__ == "__main__":
    asyncio.run(main())

