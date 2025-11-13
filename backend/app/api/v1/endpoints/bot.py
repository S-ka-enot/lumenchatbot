from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.models.user import User
from backend.app.schemas.bot import (
    BotUserRegisterRequest,
    BotUserUpdateRequest,
    ChannelPublic,
    PaymentConfirmResponse,
    PaymentCreateRequest,
    PaymentCreateResponse,
    SubscriptionStatusResponse,
)
from backend.app.schemas.user import UserRead
from backend.app.services.channels import ChannelService
from backend.app.services.payments import PaymentService
from backend.app.services.promo_codes import PromoCodeService
from backend.app.services.users import UserService
from backend.app.services.notifications import send_admin_message
from backend.app.services.subscription_plans import SubscriptionPlanService

router = APIRouter()


@router.post("/users/register", response_model=UserRead, summary="Регистрация участницы через бота")
async def bot_register_user(
    payload: BotUserRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    service = UserService(session)
    try:
        user = await service.register_from_bot(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await send_admin_message(
        f"Новая регистрация: {user.first_name or user.username or user.telegram_id}"
    )
    return UserRead.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Обновление профиля участницы через бота",
)
async def bot_update_user(
    user_id: int,
    payload: BotUserUpdateRequest,
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    service = UserService(session)
    user = await service.update_profile_from_bot(user_id, payload.model_dump(exclude_unset=True))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserRead.model_validate(user)


@router.get(
    "/users/{telegram_id}/status",
    response_model=SubscriptionStatusResponse,
    summary="Статус подписки по Telegram ID",
)
async def bot_subscription_status(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
) -> SubscriptionStatusResponse:
    service = UserService(session)
    return await service.get_subscription_status_for_telegram(
        telegram_id=telegram_id,
        bot_id=bot_id,
    )


@router.get("/channels", response_model=list[ChannelPublic], summary="Список каналов для бота")
async def bot_channels(
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
    include_locked: bool = Query(default=False),
) -> list[ChannelPublic]:
    service = ChannelService(session)
    channels = await service.list_channels_for_bot(
        bot_id=bot_id,
        include_locked=include_locked,
    )
    return [ChannelPublic(**channel) for channel in channels]


@router.post(
    "/payments/create",
    response_model=PaymentCreateResponse,
    summary="Создание счёта на оплату",
)
async def bot_create_payment(
    payload: PaymentCreateRequest,
    session: AsyncSession = Depends(get_db),
) -> PaymentCreateResponse:
    user_service = UserService(session)
    payment_service = PaymentService(session)

    user: User | None = None
    if payload.user_id is not None:
        user = await session.get(User, payload.user_id)
    if user is None:
        user = await user_service.get_by_telegram(
            payload.telegram_id,
            bot_id=payload.bot_id,
        )

    if user is None:
        # Автоматически создаем пользователь если не найден
        user_data = {
            "telegram_id": payload.telegram_id,
            "bot_id": payload.bot_id,
            "first_name": "Пользователь",
            "last_name": f"ID:{payload.telegram_id}",
        }
        try:
            user = await user_service.register_from_bot(user_data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    plan_service = SubscriptionPlanService(session)
    try:
        plan = await plan_service.get_plan(payload.plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if plan.bot_id != user.bot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тариф принадлежит другому боту",
        )
    if not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тариф временно недоступен",
        )

    # Валидация и применение промокода
    promo_code_id: int | None = None
    final_amount: Decimal | None = None
    discount_info: dict | None = None
    
    if payload.promo_code:
        promo_service = PromoCodeService(session)
        try:
            promo_code, discounted_price = await promo_service.validate_promo_code(
                payload.promo_code, user.bot_id, plan.price_amount
            )
            promo_code_id = promo_code.id
            final_amount = discounted_price
            discount_amount = plan.price_amount - discounted_price
            discount_info = {
                "promo_code": promo_code.code,
                "promo_code_id": promo_code.id,
                "discount_type": promo_code.discount_type.value,
                "discount_value": str(promo_code.discount_value),
                "original_price": str(plan.price_amount),
                "discount_amount": str(discount_amount),
                "final_price": str(discounted_price),
            }
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка промокода: {exc}",
            ) from exc

    payment = await payment_service.ensure_yookassa_payment(
        user=user,
        plan=plan,
        amount=final_amount,
        description=payload.description,
        promo_code_id=promo_code_id,
        promo_code_info=discount_info,
    )
    await send_admin_message(
        f"Создан счёт #{payment['payment_id']} на {payment['amount_formatted']}"
    )
    return PaymentCreateResponse(**payment)


@router.get(
    "/users/{telegram_id}/payments",
    summary="История платежей пользователя",
)
async def bot_user_payments(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[dict]:
    """Получает историю платежей пользователя по Telegram ID."""
    user_service = UserService(session)
    payment_service = PaymentService(session)
    
    user = await user_service.get_by_telegram(telegram_id, bot_id=bot_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    payments = await payment_service.list_user_payments(user.id, limit=limit)
    return payments


@router.post(
    "/payments/{payment_id}/confirm",
    response_model=PaymentConfirmResponse,
    summary="Подтверждение оплаты",
)
async def bot_confirm_payment(
    payment_id: int,
    session: AsyncSession = Depends(get_db),
) -> PaymentConfirmResponse:
    payment_service = PaymentService(session)
    try:
        payment, subscription = await payment_service.confirm_payment(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    response = PaymentConfirmResponse(
        status=payment.status.value,
        subscription_end=subscription.end_date if subscription else None,
    )
    await send_admin_message(
        f"Оплата #{payment_id} подтверждена. Статус: {response.status}"
    )
    return response


@router.post(
    "/users/{telegram_id}/subscription/cancel-auto-renew",
    summary="Отмена автопродления подписки",
)
async def bot_cancel_auto_renew(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
) -> dict[str, str]:
    """Отменяет автопродление активной подписки пользователя."""
    from backend.app.models.subscription import Subscription
    
    user_service = UserService(session)
    user = await user_service.get_by_telegram(telegram_id, bot_id=bot_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    # Находим активную подписку
    now = datetime.now(timezone.utc)
    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.is_active.is_(True),
            Subscription.end_date >= now,
        )
        .order_by(Subscription.end_date.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    subscription = result.scalar_one_or_none()
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активная подписка не найдена",
        )
    
    # Отменяем автопродление
    subscription.auto_renew = False
    session.add(subscription)
    await session.commit()
    
    await send_admin_message(
        f"Отменено автопродление подписки для пользователя {user.telegram_id}"
    )
    
    return {
        "status": "success",
        "message": "Автопродление подписки отменено",
    }


@router.get(
    "/subscriptions/expiring",
    summary="Получить пользователей с истекающими подписками",
)
async def bot_get_expiring_subscriptions(
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
    days_ahead: int = Query(default=3, ge=1, le=30),
) -> list[dict[str, Any]]:
    """Возвращает список пользователей, у которых подписка истекает в течение указанного количества дней."""
    from backend.app.models.subscription import Subscription
    from backend.app.models.user import User
    
    now = datetime.now(timezone.utc)
    target_date = now + timedelta(days=days_ahead)
    
    stmt = (
        select(User, Subscription)
        .join(Subscription, Subscription.user_id == User.id)
        .where(
            Subscription.is_active.is_(True),
            Subscription.end_date >= now,
            Subscription.end_date <= target_date,
            User.is_blocked.is_(False),
        )
    )
    if bot_id is not None:
        stmt = stmt.where(User.bot_id == bot_id)
    
    result = await session.execute(stmt)
    users_data = []
    for user, subscription in result.all():
        days_left = (subscription.end_date - now).days
        users_data.append({
            "telegram_id": user.telegram_id,
            "user_id": user.id,
            "bot_id": user.bot_id,
            "username": user.username,
            "first_name": user.first_name,
            "subscription_end": subscription.end_date.isoformat(),
            "days_left": days_left,
            "plan_id": subscription.plan_id,
        })
    
    return users_data


@router.get(
    "/subscriptions/expired",
    summary="Получить пользователей с истекшими подписками",
)
async def bot_get_expired_subscriptions(
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
    hours_ago: int = Query(default=24, ge=0, le=168),
) -> list[dict[str, Any]]:
    """Возвращает список пользователей, у которых подписка истекла в течение указанного количества часов."""
    from backend.app.models.subscription import Subscription
    from backend.app.models.user import User
    
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(hours=hours_ago)
    
    stmt = (
        select(User, Subscription)
        .join(Subscription, Subscription.user_id == User.id)
        .where(
            Subscription.is_active.is_(True),
            Subscription.end_date < now,
            Subscription.end_date >= cutoff_date,
            User.is_blocked.is_(False),
        )
    )
    if bot_id is not None:
        stmt = stmt.where(User.bot_id == bot_id)
    
    result = await session.execute(stmt)
    users_data = []
    for user, subscription in result.all():
        users_data.append({
            "telegram_id": user.telegram_id,
            "user_id": user.id,
            "bot_id": user.bot_id,
            "username": user.username,
            "first_name": user.first_name,
            "subscription_end": subscription.end_date.isoformat(),
            "plan_id": subscription.plan_id,
            "channels": [],  # Будет заполнено на фронтенде или в боте
        })
    
    # Загружаем каналы для каждого плана
    for user_data in users_data:
        if user_data["plan_id"]:
            plan_service = SubscriptionPlanService(session)
            try:
                plan = await plan_service.get_plan(user_data["plan_id"])
                user_data["channels"] = [
                    {
                        "channel_id": channel.channel_id,
                        "channel_name": channel.channel_name,
                    }
                    for channel in plan.channels
                ]
            except ValueError:
                pass
    
    return users_data
