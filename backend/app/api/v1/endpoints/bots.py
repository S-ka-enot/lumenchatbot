from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_admin, get_db
from backend.app.schemas.admin import BotDetails, BotSummary, BotTokenUpdate
from backend.app.schemas.auth import MeResponse
from backend.app.services.bots import BotService

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

