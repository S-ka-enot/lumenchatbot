from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import get_password_hash, verify_password
from ..models.admin import Admin


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> Optional[Admin]:
        stmt = select(Admin).where(Admin.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self, username: str, password: str) -> Optional[Admin]:
        admin = await self.get_by_username(username)
        if admin and verify_password(password, admin.password_hash):
            return admin
        return None

    async def update_last_login(self, admin: Admin | None) -> None:
        if admin is None:
            return
        try:
            admin.last_login_at = datetime.now(timezone.utc)
            self.session.add(admin)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def create_admin(self, username: str, password: str, *, is_active: bool = True) -> Admin:
        try:
            admin = Admin(
                username=username,
                password_hash=get_password_hash(password),
                is_active=is_active,
            )
            self.session.add(admin)
            await self.session.commit()
            await self.session.refresh(admin)
            return admin
        except Exception:
            await self.session.rollback()
            raise

