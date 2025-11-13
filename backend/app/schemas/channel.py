from __future__ import annotations

from typing import Optional

from pydantic import Field

from .base import ORMModel, TimestampSchema


class ChannelBase(ORMModel):
    bot_id: int
    channel_id: str = Field(..., min_length=5, max_length=64)
    channel_name: str = Field(..., min_length=2, max_length=255)
    channel_username: Optional[str] = Field(default=None, max_length=255)
    invite_link: Optional[str] = Field(default=None, max_length=512)
    description: Optional[str] = None
    is_active: bool = True
    requires_subscription: bool = True


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(ORMModel):
    channel_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    channel_username: Optional[str] = Field(default=None, max_length=255)
    invite_link: Optional[str] = Field(default=None, max_length=512)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    requires_subscription: Optional[bool] = None
    member_count: Optional[int] = None


class ChannelRead(ChannelBase, TimestampSchema):
    id: int
    member_count: Optional[int]

