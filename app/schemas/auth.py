from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None
    role: UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str
