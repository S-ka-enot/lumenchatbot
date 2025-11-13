from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import Payment, PaymentStatus
from ..models.subscription import Subscription
from ..schemas.admin import (
    ActivityItem,
    DashboardMetric,
    DashboardSummary,
    RevenuePoint,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def dashboard_summary(self) -> DashboardSummary:
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)

        active_subscriptions = await self._scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.is_active.is_(True))
        )

        monthly_revenue = await self._scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .where(Payment.paid_at.isnot(None))
            .where(Payment.paid_at >= month_ago)
        )

        renewals_today = await self._scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.start_date >= datetime(now.year, now.month, now.day, tzinfo=timezone.utc))
        )

        recent_payments = await self.session.execute(
            select(Payment)
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .order_by(Payment.paid_at.desc().nullslast(), Payment.created_at.desc())
            .limit(5)
        )
        payment_rows: Sequence[Payment] = recent_payments.scalars().all()

        revenue_points = await self._revenue_trend(week_ago, now)

        metrics = [
            DashboardMetric(
                id="active_subscriptions",
                title="Активные подписки",
                value=str(active_subscriptions),
                change=None,
                icon="users",
            ),
            DashboardMetric(
                id="monthly_revenue",
                title="Доход за 30 дней",
                value=f"{monthly_revenue:,.2f} ₽".replace(",", " "),
                change=None,
                icon="credit-card",
            ),
            DashboardMetric(
                id="renewals_today",
                title="Продлений сегодня",
                value=str(renewals_today),
                change=None,
                icon="arrow-up-right",
            ),
        ]

        activities = [
            ActivityItem(
                id=f"payment-{payment.id}",
                title="Успешный платёж",
                description=f"{payment.amount:,.2f} {payment.currency} от пользователя {payment.user_id}",
                timestamp=payment.paid_at or payment.created_at,
            )
            for payment in payment_rows
        ]

        return DashboardSummary(
            metrics=metrics,
            revenue_trend=revenue_points,
            recent_activity=activities,
        )

    async def _revenue_trend(self, start: datetime, end: datetime) -> list[RevenuePoint]:
        stmt = (
            select(Payment)
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .where(Payment.paid_at >= start)
            .where(Payment.paid_at <= end)
            .order_by(Payment.paid_at.asc())
        )
        result = await self.session.execute(stmt)
        rows: Sequence[Payment] = result.scalars().all()

        distribution: dict[str, Decimal] = {}
        for payment in rows:
            if not payment.paid_at:
                continue
            key = payment.paid_at.strftime("%d.%m")
            distribution[key] = distribution.get(key, Decimal("0")) + payment.amount

        return [
            RevenuePoint(date=key, value=value)
            for key, value in sorted(distribution.items())
        ]

    async def _scalar(self, stmt: Select) -> int | Decimal:
        result = await self.session.execute(stmt)
        value = result.scalar()
        if value is None:
            return 0
        return value

