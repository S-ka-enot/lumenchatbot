from __future__ import annotations

from typing import Any

import httpx


class BackendClient:
    def __init__(self, base_url: str, api_prefix: str = "/api/v1", timeout: float = 15.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}{api_prefix}",
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def register_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/bot/users/register", json=payload)
        response.raise_for_status()
        return response.json()

    async def update_user(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.put(f"/bot/users/{user_id}", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_subscription_status(self, telegram_id: int) -> dict[str, Any]:
        response = await self._client.get(f"/bot/users/{telegram_id}/status")
        if response.status_code == httpx.codes.NOT_FOUND:
            return {"status": "not_found"}
        response.raise_for_status()
        return response.json()

    async def list_channels(self, *, include_locked: bool = False) -> list[dict[str, Any]]:
        response = await self._client.get("/bot/channels", params={"include_locked": include_locked})
        response.raise_for_status()
        return response.json()

    async def list_plans(self, *, bot_id: int | None = None) -> list[dict[str, Any]]:
        params = {}
        if bot_id is not None:
            params["bot_id"] = bot_id
        response = await self._client.get("/plans/public", params=params or None)
        response.raise_for_status()
        return response.json()

    async def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/bot/payments/create", json=payload)
        response.raise_for_status()
        return response.json()

    async def confirm_payment(self, payment_id: str) -> dict[str, Any]:
        response = await self._client.post(f"/bot/payments/{payment_id}/confirm")
        response.raise_for_status()
        return response.json()

    async def validate_promo_code(
        self, code: str, bot_id: int, plan_price: str | None = None
    ) -> dict[str, Any]:
        """
        Валидирует промокод.
        Если указан plan_price, возвращает информацию о скидке.
        """
        params: dict[str, Any] = {"code": code, "bot_id": bot_id}
        if plan_price is not None:
            params["plan_price"] = plan_price
        response = await self._client.get("/promo-codes/validate", params=params)
        response.raise_for_status()
        return response.json()

    async def get_user_payments(
        self, telegram_id: int, bot_id: int | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Получает историю платежей пользователя."""
        params: dict[str, Any] = {"limit": limit}
        if bot_id is not None:
            params["bot_id"] = bot_id
        response = await self._client.get(
            f"/bot/users/{telegram_id}/payments", params=params
        )
        response.raise_for_status()
        return response.json()

    async def cancel_auto_renew(
        self, telegram_id: int, bot_id: int | None = None
    ) -> dict[str, Any]:
        """Отменяет автопродление подписки пользователя."""
        params: dict[str, Any] = {}
        if bot_id is not None:
            params["bot_id"] = bot_id
        response = await self._client.post(
            f"/bot/users/{telegram_id}/subscription/cancel-auto-renew",
            params=params or None,
        )
        response.raise_for_status()
        return response.json()

    async def get_expiring_subscriptions(
        self, bot_id: int | None = None, days_ahead: int = 3
    ) -> list[dict[str, Any]]:
        """Получает список пользователей с истекающими подписками."""
        params: dict[str, Any] = {"days_ahead": days_ahead}
        if bot_id is not None:
            params["bot_id"] = bot_id
        response = await self._client.get(
            "/bot/subscriptions/expiring", params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_expired_subscriptions(
        self, bot_id: int | None = None, hours_ago: int = 24
    ) -> list[dict[str, Any]]:
        """Получает список пользователей с истекшими подписками."""
        params: dict[str, Any] = {"hours_ago": hours_ago}
        if bot_id is not None:
            params["bot_id"] = bot_id
        response = await self._client.get(
            "/bot/subscriptions/expired", params=params
        )
        response.raise_for_status()
        return response.json()
