"""
인증 관련 스키마
"""

from typing import Optional

from app.schemas.user import UserResponse
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
    road_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class UserLogin(BaseModel):
    """로그인 요청"""

    email: EmailStr
    password: str


class UserUpdate(UserBase):
    """사용자 정보 업데이트 시 필요한 정보"""

    password: Optional[str] = None
    road_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Token(BaseModel):
    """토큰 응답"""

    access_token: str
    token_type: str
    user: UserResponse
