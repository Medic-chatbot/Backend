"""
기본 스키마 정의
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """모든 응답 스키마의 기본 클래스"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TimestampMixin(BaseModel):
    """타임스탬프 필드를 포함하는 Mixin"""

    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BaseMedicalEntity(BaseResponse):
    """의료 관련 엔티티의 기본 클래스"""

    name: str

    class Config:
        from_attributes = True
