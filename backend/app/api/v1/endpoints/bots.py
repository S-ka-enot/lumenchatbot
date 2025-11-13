from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_admin, get_db
from ....schemas.admin import BotCreate, BotDetails, BotSummary, BotTokenUpdate, BotUpdate
from ....schemas.auth import MeResponse
from ....services.bots import BotService

router = APIRouter()


@router.get("", response_model=list[BotSummary], summary="Список ботов")
async def list_bots(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> list[BotSummary]:
    service = BotService(session)
    bots = await service.list_bots()
    return [
        BotSummary(
            id=bot.id,
            name=bot.name,
            slug=bot.slug,
            is_active=bot.is_active,
            has_token=bool(bot.telegram_bot_token_encrypted),
        )
        for bot in bots
    ]


@router.get(
    "/{bot_id}",
    response_model=BotDetails,
    summary="Информация о боте",
)
async def get_bot_details(
    bot_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BotDetails:
    service = BotService(session)
    try:
        bot = await service.get_bot(bot_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    has_token = bool(bot.telegram_bot_token_encrypted)
    return BotDetails(
        id=bot.id,
        name=bot.name,
        slug=bot.slug,
        timezone=bot.timezone,
        is_active=bot.is_active,
        has_token=has_token,
    )


@router.post("", response_model=BotDetails, status_code=status.HTTP_201_CREATED, summary="Создать бота")
async def create_bot(
    payload: BotCreate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BotDetails:
    service = BotService(session)
    try:
        bot = await service.create_bot(
            name=payload.name,
            slug=payload.slug,
            timezone=payload.timezone,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BotDetails(
        id=bot.id,
        name=bot.name,
        slug=bot.slug,
        timezone=bot.timezone,
        is_active=bot.is_active,
        has_token=bool(bot.telegram_bot_token_encrypted),
    )


@router.put(
    "/{bot_id}",
    response_model=BotDetails,
    summary="Обновить бота",
)
async def update_bot(
    bot_id: int,
    payload: BotUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BotDetails:
    service = BotService(session)
    try:
        bot = await service.update_bot(
            bot_id=bot_id,
            name=payload.name,
            slug=payload.slug,
            timezone=payload.timezone,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BotDetails(
        id=bot.id,
        name=bot.name,
        slug=bot.slug,
        timezone=bot.timezone,
        is_active=bot.is_active,
        has_token=bool(bot.telegram_bot_token_encrypted),
    )


@router.put(
    "/{bot_id}/token",
    response_model=BotDetails,
    summary="Обновить токен бота",
)
async def update_bot_token(
    bot_id: int,
    payload: BotTokenUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> BotDetails:
    service = BotService(session)
    try:
        bot = await service.update_token(bot_id, payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return BotDetails(
        id=bot.id,
        name=bot.name,
        slug=bot.slug,
        timezone=bot.timezone,
        is_active=bot.is_active,
        has_token=bool(bot.telegram_bot_token_encrypted),
    )


@router.delete(
    "/{bot_id}",
    summary="Удалить бота",
)
async def delete_bot(
    bot_id: int,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = BotService(session)
    try:
        await service.delete_bot(bot_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

