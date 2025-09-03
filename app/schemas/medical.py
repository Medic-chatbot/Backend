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


# ===== 의료장비 관련 스키마 =====


class MedicalEquipmentCategoryResponse(BaseModel):
    """의료장비 대분류 응답"""

    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalEquipmentSubcategoryResponse(BaseModel):
    """의료장비 세분류 응답"""

    id: UUID
    name: str
    category: MedicalEquipmentCategoryResponse
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 매핑 관련 스키마 =====


class DepartmentDiseaseResponse(BaseModel):
    """진료과-질환 매핑 응답"""

    department: DepartmentResponse
    disease: DiseaseResponse

    class Config:
        from_attributes = True


class EquipmentDiseaseResponse(BaseModel):
    """의료장비-질환 매핑 응답"""

    equipment_subcategory: MedicalEquipmentSubcategoryResponse
    disease: DiseaseResponse

    class Config:
        from_attributes = True


# ===== 채팅 및 진단 관련 스키마 =====


class ChatSymptomAnalysisRequest(BaseModel):
    """채팅 증상 분석 요청"""

    chat_room_id: UUID = Field(..., description="채팅방 ID")
    symptoms: str = Field(..., description="증상 설명")


class ChatDiagnosisResponse(BaseModel):
    """채팅 진단 결과 응답"""

    chat_room_id: UUID
    message_id: UUID
    final_disease: DiseaseResponse
    departments: List[DepartmentResponse]
    confidence_score: float
    inference_time: Optional[float] = None

    class Config:
        from_attributes = True


class DiseaseWithDepartmentsResponse(BaseModel):
    """질환과 관련 진료과 정보"""

    disease: DiseaseResponse
    departments: List[DepartmentResponse]

    class Config:
        from_attributes = True


# ===== 병원 추천 관련 스키마 =====


class HospitalRecommendationRequest(BaseModel):
    """병원 추천 요청"""

    inference_result_id: UUID = Field(..., description="모델 추론 결과 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    max_distance: Optional[float] = Field(20.0, description="최대 검색 거리 (km)")
    limit: Optional[int] = Field(3, description="추천 병원 수")


class RecommendedHospitalResponse(BaseModel):
    """추천 병원 상세 정보"""

    id: UUID
    name: str
    address: str
    hospital_type_name: Optional[str] = None
    phone: Optional[str] = None
    distance: float
    rank: int
    recommendation_score: float
    department_match: bool
    equipment_match: bool
    recommended_reason: str

    class Config:
        from_attributes = True


class HospitalRecommendationResponse(BaseModel):
    """병원 추천 결과 응답"""

    inference_result_id: UUID
    user_id: UUID
    final_disease: DiseaseResponse
    total_candidates: int
    recommendations: List[RecommendedHospitalResponse]
    search_criteria: dict

    class Config:
        from_attributes = True
