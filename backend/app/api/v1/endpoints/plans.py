from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_admin, get_db
from ....schemas.auth import MeResponse
from ....schemas.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
)
from ....services.subscription_plans import SubscriptionPlanService

router = APIRouter()


@router.get("", response_model=list[SubscriptionPlanRead], summary="Список тарифов")
async def list_plans(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
) -> list[SubscriptionPlanRead]:
    service = SubscriptionPlanService(session)
    return await service.list_plans(bot_id=bot_id)


@router.post(
    "",
    response_model=SubscriptionPlanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать тариф",
)
async def create_plan(
    payload: SubscriptionPlanCreate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> SubscriptionPlanRead:
    service = SubscriptionPlanService(session)
    try:
        return await service.create_plan(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось создать тариф. Проверьте уникальность данных.",
        ) from exc


@router.put(
    "/{plan_id}",
    response_model=SubscriptionPlanRead,
    summary="Обновить тариф",
)
async def update_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> SubscriptionPlanRead:
    service = SubscriptionPlanService(session)
    try:
        return await service.update_plan(plan_id, payload)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить тариф",
    response_class=Response,
)
async def delete_plan(
    plan_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = SubscriptionPlanService(session)
    try:
        await service.delete_plan(plan_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
