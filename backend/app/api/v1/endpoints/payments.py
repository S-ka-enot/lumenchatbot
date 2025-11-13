from __future__ import annotations

import csv
import io
from base64 import b64decode
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_admin, get_db
from backend.app.schemas.admin import PaymentListItem
from backend.app.schemas.auth import MeResponse
from backend.app.schemas.base import PaginatedResponse
from backend.app.services.payments import PaymentService
from backend.app.services.payment_providers import PaymentProviderSettingsService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[PaymentListItem],
    summary="Список платежей",
)
async def list_payments(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
) -> PaginatedResponse[PaymentListItem]:
    service = PaymentService(session)
    items, total = await service.list_recent(page=page, size=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get(
    "/export",
    response_class=StreamingResponse,
    summary="Экспорт платежей в CSV",
)
async def export_payments(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    service = PaymentService(session)
    rows = await service.export_payments()
    buffer = io.StringIO()
    fieldnames = [
        "id",
        "invoice",
        "member",
        "telegram_id",
        "amount",
        "currency",
        "amount_formatted",
        "status",
        "provider",
        "plan",
        "external_id",
        "created_at",
        "paid_at",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    headers = {
        "Content-Disposition": 'attachment; filename="payments.csv"',
    }
    return StreamingResponse(
        buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


@router.post(
    "/yookassa/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Webhook YooKassa",
    response_class=Response,
)
async def yookassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> Response:
    if not authorization or not authorization.startswith("Basic "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    encoded = authorization.split(" ", 1)[1]
    try:
        decoded = b64decode(encoded).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc

    if ":" not in decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials format"
        )
    auth_shop_id, auth_api_key = decoded.split(":", 1)

    provider_service = PaymentProviderSettingsService(session)
    try:
        shop_id, api_key = await provider_service.get_yookassa_credentials()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YooKassa is not configured",
        ) from exc

    if auth_shop_id != shop_id or auth_api_key != api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied")

    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload"
        ) from exc

    service = PaymentService(session)
    await service.handle_yookassa_notification(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

