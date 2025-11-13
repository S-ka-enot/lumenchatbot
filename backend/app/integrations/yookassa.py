from __future__ import annotations

import asyncio
from typing import Any

import json
from yookassa import Configuration, Payment

from ..core.config import settings


class YooKassaClient:
    """
    Асинхронная обертка над SDK YooKassa.
    """

    def __init__(self, shop_id: str, api_key: str, return_url: str | None = None) -> None:
        Configuration.account_id = shop_id
        Configuration.secret_key = api_key
        # Преобразуем AnyHttpUrl в строку, если он не None
        default_return_url = str(settings.yookassa_return_url) if settings.yookassa_return_url else None
        self.return_url = return_url or default_return_url

    async def create_payment(
        self,
        *,
        amount: str,
        description: str,
        metadata: dict[str, Any],
        confirmation_return_url: str,
    ) -> dict[str, Any]:
        payload = {
            "amount": {"value": amount, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": confirmation_return_url},
            "capture": True,
            "description": description,
            "metadata": metadata,
        }

        payment = await asyncio.to_thread(Payment.create, payload)
        return json.loads(payment.json())

    async def get_payment(self, payment_id: str) -> dict[str, Any]:
        payment = await asyncio.to_thread(Payment.find_one, payment_id)
        return json.loads(payment.json())

