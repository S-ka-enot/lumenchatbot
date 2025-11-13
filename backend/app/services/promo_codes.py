from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.promo_code import DiscountType, PromoCode
from ..schemas.promo_code import (
    PromoCodeCreate,
    PromoCodeRead,
    PromoCodeUpdate,
)


class PromoCodeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_promo_codes(self, *, bot_id: int | None = None) -> list[PromoCodeRead]:
        stmt = select(PromoCode)
        if bot_id is not None:
            stmt = stmt.where(PromoCode.bot_id == bot_id)
        stmt = stmt.order_by(PromoCode.created_at.desc())
        result = await self.session.execute(stmt)
        promo_codes = result.scalars().all()
        return [PromoCodeRead.model_validate(pc) for pc in promo_codes]

    async def get_promo_code(self, promo_code_id: int) -> PromoCode:
        promo_code = await self.session.get(PromoCode, promo_code_id)
        if promo_code is None:
            raise ValueError("Промокод не найден")
        return promo_code

    async def get_promo_code_by_code(
        self, code: str, bot_id: int | None = None
    ) -> PromoCode | None:
        stmt = select(PromoCode).where(PromoCode.code == code.upper())
        if bot_id is not None:
            stmt = stmt.where(PromoCode.bot_id == bot_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def validate_promo_code(
        self, code: str, bot_id: int, plan_price: Decimal
    ) -> tuple[PromoCode, Decimal]:
        """
        Валидирует промокод и возвращает его вместе с итоговой ценой после скидки.
        
        Returns:
            tuple[PromoCode, Decimal]: Промокод и итоговая цена после применения скидки
            
        Raises:
            ValueError: Если промокод невалиден
        """
        promo_code = await self.get_promo_code_by_code(code, bot_id)
        if promo_code is None:
            raise ValueError("Промокод не найден")

        if not promo_code.is_active:
            raise ValueError("Промокод неактивен")

        now = datetime.now(timezone.utc)
        if promo_code.valid_from and promo_code.valid_from > now:
            raise ValueError("Промокод ещё не действует")

        if promo_code.valid_until and promo_code.valid_until < now:
            raise ValueError("Промокод истёк")

        if promo_code.max_uses is not None and promo_code.used_count >= promo_code.max_uses:
            raise ValueError("Промокод исчерпан")

        # Вычисляем итоговую цену
        if promo_code.discount_type == DiscountType.PERCENTAGE:
            discount_amount = plan_price * (promo_code.discount_value / Decimal("100"))
            final_price = plan_price - discount_amount
        else:  # FIXED
            final_price = max(Decimal("0"), plan_price - promo_code.discount_value)

        return promo_code, final_price

    async def apply_promo_code(self, promo_code_id: int) -> None:
        """Увеличивает счётчик использования промокода."""
        promo_code = await self.get_promo_code(promo_code_id)
        promo_code.used_count += 1
        self.session.add(promo_code)
        await self.session.commit()

    async def create_promo_code(self, payload: PromoCodeCreate) -> PromoCodeRead:
        # Проверяем уникальность кода
        existing = await self.get_promo_code_by_code(payload.code, payload.bot_id)
        if existing is not None:
            raise ValueError("Промокод с таким кодом уже существует")

        data = payload.model_dump()
        data["code"] = data["code"].upper()
        data["discount_value"] = Decimal(data["discount_value"])
        promo_code = PromoCode(**data)
        self.session.add(promo_code)
        await self.session.commit()
        await self.session.refresh(promo_code)
        return PromoCodeRead.model_validate(promo_code)

    async def update_promo_code(
        self, promo_code_id: int, payload: PromoCodeUpdate
    ) -> PromoCodeRead:
        promo_code = await self.get_promo_code(promo_code_id)
        data = payload.model_dump(exclude_unset=True)
        if "discount_value" in data and data["discount_value"] is not None:
            data["discount_value"] = Decimal(data["discount_value"])
        for field, value in data.items():
            setattr(promo_code, field, value)
        self.session.add(promo_code)
        await self.session.commit()
        await self.session.refresh(promo_code)
        return PromoCodeRead.model_validate(promo_code)

    async def delete_promo_code(self, promo_code_id: int) -> None:
        promo_code = await self.get_promo_code(promo_code_id)
        await self.session.delete(promo_code)
        await self.session.commit()

