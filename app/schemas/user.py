"""
사용자 관련 스키마
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserLocationUpdate(BaseModel):
    """사용자 위치 정보 업데이트"""

    road_address: str = Field(
        ..., description="도로명 주소 (다음 우편번호 서비스 결과)"
    )
    latitude: float = Field(..., description="위도 (카카오 지오코딩 결과)")
    longitude: float = Field(..., description="경도 (카카오 지오코딩 결과)")


class UserResponse(BaseModel):
    """사용자 정보 응답"""

    id: UUID
    email: str
    nickname: str
    age: int
    gender: str
    road_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLocationResponse(BaseModel):
    """사용자 위치 정보 응답"""

    id: UUID
    user_id: UUID
    latitude: float
    longitude: float
    address: Optional[str] = None
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True
