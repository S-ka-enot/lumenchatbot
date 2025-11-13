from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_admin, get_db
from backend.app.schemas.auth import MeResponse
from backend.app.schemas.base import PaginatedResponse
from backend.app.schemas.channel import ChannelCreate, ChannelRead, ChannelUpdate
from backend.app.services.channels import ChannelService

router = APIRouter()


@router.get(
    "", response_model=PaginatedResponse[ChannelRead], summary="Список каналов"
)
async def list_channels(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
    bot_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
) -> PaginatedResponse[ChannelRead]:
    service = ChannelService(session)
    items, total = await service.list_channels(bot_id=bot_id, page=page, size=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.post(
    "",
    response_model=ChannelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать канал",
)
async def create_channel(
    payload: ChannelCreate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> ChannelRead:
    service = ChannelService(session)
    try:
        return await service.create_channel(payload)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Канал с такими параметрами уже существует",
        ) from exc


@router.put(
    "/{channel_id}",
    response_model=ChannelRead,
    summary="Обновить канал",
)
async def update_channel(
    channel_id: int,
    payload: ChannelUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> ChannelRead:
    service = ChannelService(session)
    try:
        return await service.update_channel(channel_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить канал",
    response_class=Response,
)
async def delete_channel(
    channel_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = ChannelService(session)
    try:
        await service.delete_channel(channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
