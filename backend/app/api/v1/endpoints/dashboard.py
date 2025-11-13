from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_admin, get_db
from ....schemas.admin import DashboardSummary
from ....schemas.auth import MeResponse
from ....services.analytics import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary, summary="Сводка для дашборда")
async def dashboard_summary(
    _: MeResponse = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    service = AnalyticsService(session)
    return await service.dashboard_summary()

