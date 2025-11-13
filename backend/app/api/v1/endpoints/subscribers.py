from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_admin, get_db
from ....schemas.admin import (
    SubscriberCreate,
    SubscriberListItem,
    SubscriberUpdate,
    SubscriptionExtendRequest,
)
from ....schemas.auth import MeResponse
from ....schemas.base import PaginatedResponse
from ....services.users import UserService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SubscriberListItem],
    summary="Список подписчиков",
)
async def list_subscribers(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
) -> PaginatedResponse[SubscriberListItem]:
    service = UserService(session)
    items, total = await service.list_subscribers(page=page, size=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get(
    "/export",
    response_class=StreamingResponse,
    summary="Экспорт списка подписчиц в CSV",
)
async def export_subscribers(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    service = UserService(session)
    rows = await service.export_subscribers()
    buffer = io.StringIO()
    fieldnames = [
        "id",
        "bot_id",
        "telegram_id",
        "full_name",
        "username",
        "phone_number",
        "tariff",
        "status",
        "expires_at",
        "is_blocked",
        "created_at",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    headers = {
        "Content-Disposition": 'attachment; filename="subscribers.csv"',
    }
    return StreamingResponse(
        buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


@router.post(
    "",
    response_model=SubscriberListItem,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить подписчицу",
)
async def create_subscriber(
    payload: SubscriberCreate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> SubscriberListItem:
    service = UserService(session)
    try:
        return await service.create_subscriber(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось создать участницу. Проверьте уникальность данных.",
        ) from exc


@router.put(
    "/{user_id}",
    response_model=SubscriberListItem,
    summary="Обновить данные подписчицы",
)
async def update_subscriber(
    user_id: int,
    payload: SubscriberUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> SubscriberListItem:
    service = UserService(session)
    try:
        return await service.update_subscriber(user_id, payload)
    except ValueError as exc:
        exc_lower = str(exc).lower()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "не найден" in exc_lower
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось обновить данные участницы. Проверьте уникальность данных.",
        ) from exc


@router.post(
    "/{user_id}/extend",
    response_model=SubscriberListItem,
    summary="Продлить подписку",
)
async def extend_subscription(
    user_id: int,
    payload: SubscriptionExtendRequest,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> SubscriberListItem:
    service = UserService(session)
    try:
        return await service.extend_subscription(user_id, payload)
    except ValueError as exc:
        exc_lower = str(exc).lower()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "не найден" in exc_lower
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить подписчицу",
)
async def delete_subscriber(
    user_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = UserService(session)
    try:
        await service.delete_subscriber(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{user_id}/subscriptions/{subscription_id}",
    response_model=SubscriberListItem,
    summary="Удалить подписку участницы",
)
async def remove_subscription(
    user_id: int,
    subscription_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> SubscriberListItem:
    service = UserService(session)
    try:
        return await service.remove_subscription(user_id, subscription_id)
    except ValueError as exc:
        status_text = str(exc).lower()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "не найден" in status_text or "не найдена" in status_text
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

