from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ....api.deps import get_admin_service, get_current_admin
from ....core.config import settings
from ....core.rate_limit import limiter
from ....core.security import create_access_token
from ....schemas import LoginRequest, MeResponse, Token
from ....services.admins import AdminService

router = APIRouter()


@router.post("/login", response_model=Token, summary="Вход администратора")
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    admin_service: AdminService = Depends(get_admin_service),
) -> Token:
    admin = await admin_service.authenticate(payload.username, payload.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    await admin_service.update_last_login(admin)

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(subject=admin.username, expires_delta=expires)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=int(expires.total_seconds()),
    )


@router.get("/me", response_model=MeResponse, summary="Информация о текущем администраторе")
async def read_me(
    current_admin: MeResponse = Depends(get_current_admin),
) -> MeResponse:
    return current_admin


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Выход администратора")
async def logout() -> None:
    # Для JWT-авторизации ничего делать не нужно, фронт просто удаляет токен.
    return None


@router.get("/csrf", summary="Получение CSRF токена")
async def csrf_token() -> dict[str, str]:
    # CSRF токен реализуется на фронтенде, здесь возвращаем заглушку
    return {"csrfToken": "not-required-for-jwt"}

