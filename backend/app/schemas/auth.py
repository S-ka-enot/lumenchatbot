from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6, max_length=128)


class MeResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    telegram_id: Optional[int]
    last_login_at: Optional[datetime]

