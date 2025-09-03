"""
의료 관련 스키마
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DiseaseBase(BaseModel):
    """질환 기본 정보"""

    name: str
    description: Optional[str] = None


class DiseaseResponse(DiseaseBase):
    """질환 정보 응답"""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    """진료과 기본 정보"""

    name: str
    description: Optional[str] = None
    code: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    """진료과 정보 응답"""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ModelInferenceRequest(BaseModel):
    """모델 추론 요청"""

    input_text: str = Field(..., description="증상 입력 텍스트")


class DiseasePrediection(BaseModel):
    """질환 예측 결과"""

    disease_id: UUID
    disease_name: str
    score: float


class ModelInferenceResponse(BaseModel):
    """모델 추론 결과 응답"""

    id: UUID
    input_text: str
    first_prediction: DiseasePrediection
    second_prediction: Optional[DiseasePrediection] = None
    third_prediction: Optional[DiseasePrediection] = None
    inference_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HospitalBase(BaseModel):
    """병원 기본 정보"""

    name: str
    address: str
    latitude: float
    longitude: float
    type: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None


class HospitalResponse(HospitalBase):
    """병원 정보 응답"""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class HospitalRecommendationResponse(BaseModel):
    """병원 추천 결과 응답"""

    id: UUID
    hospital: HospitalResponse
    distance: float
    rank: int
    recommendation_score: Optional[float] = None
    department_match: bool
    equipment_match: bool
    recommended_reason: Optional[str] = None

    class Config:
        from_attributes = True


class HospitalRecommendationRequest(BaseModel):
    """병원 추천 요청"""

    symptoms: str = Field(..., description="증상 설명")
    max_distance: Optional[float] = Field(20.0, description="최대 검색 거리 (km)")
    limit: Optional[int] = Field(3, description="추천 병원 수")
