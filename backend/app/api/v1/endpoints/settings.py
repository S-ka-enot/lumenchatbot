from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_admin, get_db
from ....schemas.auth import MeResponse
from ....schemas.settings import YooKassaSettingsResponse, YooKassaSettingsUpdate
from ....services.payment_providers import PaymentProviderSettingsService

router = APIRouter()


@router.get(
    "/yookassa",
    response_model=YooKassaSettingsResponse,
    summary="Получить настройки YooKassa",
)
async def get_yookassa_settings(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> YooKassaSettingsResponse:
    service = PaymentProviderSettingsService(session)
    shop_id, has_api_key = await service.get_yookassa_settings()
    return YooKassaSettingsResponse(
        shop_id=shop_id,
        has_api_key=has_api_key,
        is_configured=bool(shop_id and has_api_key),
    )


@router.put(
    "/yookassa",
    response_model=YooKassaSettingsResponse,
    summary="Обновить настройки YooKassa",
)
async def update_yookassa_settings(
    payload: YooKassaSettingsUpdate,
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> YooKassaSettingsResponse:
    service = PaymentProviderSettingsService(session)
    if not payload.shop_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Shop ID не может быть пустым"
        )

    shop_id, has_api_key = await service.upsert_yookassa_settings(
        shop_id=payload.shop_id.strip(),
        api_key=payload.api_key.strip() if payload.api_key else None,
    )
    return YooKassaSettingsResponse(
        shop_id=shop_id,
        has_api_key=has_api_key,
        is_configured=bool(shop_id and has_api_key),
    )
