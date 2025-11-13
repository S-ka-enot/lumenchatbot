from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_admin, get_db
from backend.app.schemas.auth import MeResponse
from backend.app.schemas.base import PaginatedResponse
from backend.app.schemas.broadcast import BroadcastCreate, BroadcastRead, BroadcastUpdate
from backend.app.services.broadcasts import BroadcastService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[BroadcastRead],
    summary="Список рассылок",
)
async def list_broadcasts(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    bot_id: int | None = Query(default=None),
) -> PaginatedResponse[BroadcastRead]:
    service = BroadcastService(session)
    items, total = await service.list_broadcasts(page=page, size=size, bot_id=bot_id)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get(
    "/{broadcast_id}",
    response_model=BroadcastRead,
    summary="Получить рассылку",
)
async def get_broadcast(
    broadcast_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BroadcastRead:
    service = BroadcastService(session)
    broadcast = await service.get_broadcast(broadcast_id)
    if broadcast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рассылка не найдена"
        )
    return broadcast


@router.post(
    "",
    response_model=BroadcastRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать рассылку",
)
async def create_broadcast(
    payload: BroadcastCreate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BroadcastRead:
    service = BroadcastService(session)
    try:
        return await service.create_broadcast(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put(
    "/{broadcast_id}",
    response_model=BroadcastRead,
    summary="Обновить рассылку",
)
async def update_broadcast(
    broadcast_id: int,
    payload: BroadcastUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BroadcastRead:
    service = BroadcastService(session)
    try:
        return await service.update_broadcast(broadcast_id, payload)
    except ValueError as exc:
        exc_lower = str(exc).lower()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "не найден" in exc_lower or "не найдена" in exc_lower
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete(
    "/{broadcast_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить рассылку",
)
async def delete_broadcast(
    broadcast_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = BroadcastService(session)
    try:
        await service.delete_broadcast(broadcast_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{broadcast_id}/recipients/count",
    summary="Получить количество получателей рассылки",
)
async def get_recipients_count(
    broadcast_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    service = BroadcastService(session)
    broadcast = await service.get_broadcast(broadcast_id)
    if broadcast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рассылка не найдена"
        )
    # Нужно получить объект модели для подсчета
    from sqlalchemy import select
    from backend.app.models.scheduled_broadcast import ScheduledBroadcast

    stmt = select(ScheduledBroadcast).where(ScheduledBroadcast.id == broadcast_id)
    result = await session.execute(stmt)
    broadcast_model = result.scalar_one_or_none()
    if broadcast_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рассылка не найдена"
        )
    count = await service.get_recipients_count(broadcast_model)
    return {"count": count}


@router.post(
    "/{broadcast_id}/send",
    summary="Отправить рассылку немедленно",
)
async def send_broadcast_now(
    broadcast_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    service = BroadcastService(session)
    try:
        result = await service.send_broadcast_now(broadcast_id)
        return result
    except ValueError as exc:
        exc_lower = str(exc).lower()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "не найден" in exc_lower or "не найдена" in exc_lower
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

