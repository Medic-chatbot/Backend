"""
인증 관련 스키마
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """사용자 기본 정보"""

    email: EmailStr
    nickname: str
    age: int
    gender: str


class UserCreate(UserBase):
    """사용자 생성 시 필요한 정보"""

    password: str


class UserUpdate(UserBase):
    """사용자 정보 업데이트 시 필요한 정보"""

    password: Optional[str] = None


class UserResponse(UserBase):
    """사용자 정보 응답"""

    id: UUID  # str에서 UUID로 변경
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """토큰 응답"""

    access_token: str
    token_type: str
    user: UserResponse
