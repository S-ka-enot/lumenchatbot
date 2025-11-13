from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_admin, get_db
from ....schemas.auth import MeResponse
from ....schemas.promo_code import (
    PromoCodeCreate,
    PromoCodeRead,
    PromoCodeUpdate,
)
from ....services.promo_codes import PromoCodeService

router = APIRouter()


# Важно: endpoint /validate должен быть зарегистрирован ДО /{promo_code_id},
# чтобы FastAPI правильно обрабатывал маршруты
@router.get(
    "/validate",
    summary="Валидация промокода (публичный endpoint)",
)
async def validate_promo_code(
    code: str = Query(..., description="Код промокода"),
    bot_id: int = Query(..., description="ID бота"),
    plan_price: str | None = Query(default=None, description="Цена тарифа (опционально)"),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Валидирует промокод и возвращает информацию о скидке.
    Используется ботом перед созданием платежа.
    Если plan_price не указан, возвращает только информацию о валидности промокода.
    """
    from decimal import Decimal
    from datetime import datetime, timezone

    service = PromoCodeService(session)
    try:
        # Если цена не указана, просто проверяем валидность промокода
        if plan_price is None:
            promo_code = await service.get_promo_code_by_code(code, bot_id)
            if promo_code is None:
                return {
                    "valid": False,
                    "error": "Промокод не найден",
                }
            
            # Проверяем базовые условия валидности
            now = datetime.now(timezone.utc)
            if not promo_code.is_active:
                return {
                    "valid": False,
                    "error": "Промокод неактивен",
                }
            if promo_code.valid_from and promo_code.valid_from > now:
                return {
                    "valid": False,
                    "error": "Промокод ещё не действует",
                }
            if promo_code.valid_until and promo_code.valid_until < now:
                return {
                    "valid": False,
                    "error": "Промокод истёк",
                }
            if promo_code.max_uses is not None and promo_code.used_count >= promo_code.max_uses:
                return {
                    "valid": False,
                    "error": "Промокод исчерпан",
                }
            
            return {
                "valid": True,
                "promo_code": PromoCodeRead.model_validate(promo_code).model_dump(),
                "discount_type": promo_code.discount_type.value,
                "discount_value": str(promo_code.discount_value),
            }
        
        # Если цена указана, вычисляем скидку
        price = Decimal(plan_price)
        promo_code, final_price = await service.validate_promo_code(code, bot_id, price)
        discount_amount = price - final_price
        
        return {
            "valid": True,
            "promo_code": PromoCodeRead.model_validate(promo_code).model_dump(),
            "original_price": str(price),
            "discount_amount": str(discount_amount),
            "final_price": str(final_price),
            "discount_type": promo_code.discount_type.value,
            "discount_value": str(promo_code.discount_value),
        }
    except ValueError as exc:
        return {
            "valid": False,
            "error": str(exc),
        }


@router.get(
    "",
    response_model=list[PromoCodeRead],
    summary="Список промокодов",
)
async def list_promo_codes(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
) -> list[PromoCodeRead]:
    service = PromoCodeService(session)
    return await service.list_promo_codes(bot_id=bot_id)


@router.get(
    "/{promo_code_id}",
    response_model=PromoCodeRead,
    summary="Получить промокод",
)
async def get_promo_code(
    promo_code_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> PromoCodeRead:
    service = PromoCodeService(session)
    try:
        promo_code = await service.get_promo_code(promo_code_id)
        return PromoCodeRead.model_validate(promo_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "",
    response_model=PromoCodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать промокод",
)
async def create_promo_code(
    payload: PromoCodeCreate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> PromoCodeRead:
    service = PromoCodeService(session)
    try:
        return await service.create_promo_code(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put(
    "/{promo_code_id}",
    response_model=PromoCodeRead,
    summary="Обновить промокод",
)
async def update_promo_code(
    promo_code_id: int,
    payload: PromoCodeUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> PromoCodeRead:
    service = PromoCodeService(session)
    try:
        return await service.update_promo_code(promo_code_id, payload)
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if "не найден" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete(
    "/{promo_code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить промокод",
    response_class=Response,
)
async def delete_promo_code(
    promo_code_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = PromoCodeService(session)
    try:
        await service.delete_promo_code(promo_code_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
