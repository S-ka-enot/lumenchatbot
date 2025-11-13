from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import decode_token
from ..db.session import get_async_session
from ..schemas.auth import MeResponse
from ..services.admins import AdminService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_async_session():
        yield session


async def get_admin_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AdminService:
    return AdminService(session=session)


async def get_current_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> MeResponse:
    try:
        payload = decode_token(token)
    except ValueError as exc:  # pragma: no cover - валидация токена
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
        ) from exc

    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

    admin = await admin_service.get_by_username(username)
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Администратор не найден")

    return MeResponse(
        id=admin.id,
        username=admin.username,
        is_active=admin.is_active,
        telegram_id=admin.telegram_id,
        last_login_at=admin.last_login_at,
    )

