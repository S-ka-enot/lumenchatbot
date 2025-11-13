from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from .config import settings


def _get_fernet() -> Fernet:
    raw_key = settings.bot_token_encryption_key.get_secret_value().encode()
    try:
        return Fernet(raw_key)
    except (TypeError, ValueError):
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())
        return Fernet(derived)


def encrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    token = _get_fernet().encrypt(value.encode())
    return token.decode()


def decrypt_secret(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:  # pragma: no cover - повреждённый токен
        raise RuntimeError("Не удалось расшифровать секрет") from exc
