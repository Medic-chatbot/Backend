"""
의료 관련 스키마 - 순환 참조 완전 제거 및 독립적 스키마 정의
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ===== 기본 요청/응답 스키마 =====


class DiseaseBase(BaseModel):
    """질환 기본 정보"""

    name: str
    description: Optional[str] = None


class DiseaseCreate(DiseaseBase):
    """질환 생성 요청"""

    pass


class DiseaseUpdate(DiseaseBase):
    """질환 수정 요청"""

    pass


class DiseaseResponse(BaseModel):
    """질환 기본 응답"""

    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 진료과 스키마 =====


class DepartmentBase(BaseModel):
    """진료과 기본 정보"""

    name: str


class DepartmentCreate(DepartmentBase):
    """진료과 생성 요청"""

    pass


class DepartmentUpdate(DepartmentBase):
    """진료과 수정 요청"""

    pass


class DepartmentResponse(BaseModel):
    """진료과 기본 응답"""

    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 병원 스키마 =====


class HospitalBase(BaseModel):
    """병원 기본 정보"""

    name: str
    address: str
    latitude: float
    longitude: float
    encrypted_code: str
    hospital_type_code: Optional[str] = None
    hospital_type_name: Optional[str] = None
    region_code: Optional[str] = None
    region_name: Optional[str] = None
    district_code: Optional[str] = None
    district_name: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None


class HospitalCreate(HospitalBase):
    """병원 생성 요청"""

    pass


class HospitalUpdate(HospitalBase):
    """병원 수정 요청"""

    pass


class HospitalResponse(BaseModel):
    """병원 기본 응답"""

    id: int
    name: str
    address: str
    hospital_type_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 의료장비 스키마 =====


class MedicalEquipmentCategoryBase(BaseModel):
    """의료장비 대분류 기본 정보"""

    name: str
    code: str


class MedicalEquipmentCategoryResponse(BaseModel):
    """의료장비 대분류 응답"""

    id: int
    name: str
    code: str
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalEquipmentSubcategoryBase(BaseModel):
    """의료장비 세분류 기본 정보"""

    name: str
    code: str


class MedicalEquipmentSubcategoryResponse(BaseModel):
    """의료장비 세분류 응답"""

    id: int
    category_id: int
    name: str
    code: str
    created_at: datetime

    class Config:
        from_attributes = True


class EquipmentResponse(BaseModel):
    """장비 정보 응답 (병원 장비용)"""

    id: int
    name: str
    code: str
    category_name: str
    quantity: int = 1
    is_operational: bool = True

    class Config:
        from_attributes = True


# ===== 상세 조회용 스키마 (Dict 타입으로 순환 참조 완전 방지) =====


class DiseaseDetailResponse(BaseModel):
    """질환 상세 정보 응답"""

    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    departments: List[Dict[str, Any]] = Field(
        default_factory=list, description="관련 진료과 목록"
    )

    class Config:
        from_attributes = True


class DepartmentDetailResponse(BaseModel):
    """진료과 상세 정보 응답"""

    id: int
    name: str
    created_at: datetime
    diseases: List[Dict[str, Any]] = Field(
        default_factory=list, description="관련 질환 목록"
    )
    hospitals: List[Dict[str, Any]] = Field(
        default_factory=list, description="관련 병원 목록"
    )

    class Config:
        from_attributes = True


class HospitalDetailResponse(BaseModel):
    """병원 상세 정보 응답"""

    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    encrypted_code: str
    hospital_type_code: Optional[str] = None
    hospital_type_name: Optional[str] = None
    region_code: Optional[str] = None
    region_name: Optional[str] = None
    district_code: Optional[str] = None
    district_name: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime
    departments: List[Dict[str, Any]] = Field(
        default_factory=list, description="관련 진료과 목록"
    )
    equipment: List[Dict[str, Any]] = Field(
        default_factory=list, description="보유 장비 목록"
    )

    class Config:
        from_attributes = True


# ===== 관계 매핑 스키마 =====


class DepartmentDiseaseResponse(BaseModel):
    """진료과-질환 매핑 응답"""

    department: Dict[str, Any]
    disease: Dict[str, Any]

    class Config:
        from_attributes = True


class EquipmentDiseaseResponse(BaseModel):
    """장비-질환 매핑 응답"""

    equipment_subcategory: Dict[str, Any]
    disease: Dict[str, Any]

    class Config:
        from_attributes = True


# ===== 모델 추론 관련 스키마 =====


class ModelInferenceRequest(BaseModel):
    """모델 추론 요청"""

    input_text: str = Field(..., description="증상 입력 텍스트")


class ModelInferenceResponse(BaseModel):
    """모델 추론 결과 응답"""

    message_id: int
    input_text: str
    predictions: List[Dict[str, Any]] = Field(..., description="질환 예측 결과")
    inference_time: Optional[float] = None

    class Config:
        from_attributes = True


# ===== 채팅 관련 스키마 =====


class ChatSymptomAnalysisRequest(BaseModel):
    """채팅 증상 분석 요청"""

    chat_room_id: int = Field(..., description="채팅방 ID")
    symptoms: str = Field(..., description="증상 설명")


class ChatDiagnosisResponse(BaseModel):
    """채팅 진단 결과 응답"""

    chat_room_id: int
    message_id: int
    final_disease: Dict[str, Any]
    departments: List[Dict[str, Any]]
    confidence_score: float
    inference_time: Optional[float] = None

    class Config:
        from_attributes = True


class DiseaseWithDepartmentsResponse(BaseModel):
    """질환과 관련 진료과 정보"""

    disease: Dict[str, Any]
    departments: List[Dict[str, Any]]

    class Config:
        from_attributes = True


# ===== 병원 추천 관련 스키마 =====


class HospitalRecommendationRequest(BaseModel):
    """병원 추천 요청"""

    inference_result_id: int = Field(..., description="모델 추론 결과 ID")
    chat_room_id: int = Field(..., description="채팅방 ID")
    user_id: str = Field(..., description="사용자 ID (UUID)")
    max_distance: Optional[float] = Field(20.0, description="최대 검색 거리 (km)")
    limit: Optional[int] = Field(3, description="추천 병원 수")


class RecommendedHospitalResponse(BaseModel):
    """추천 병원 상세 정보"""

    id: int
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

    inference_result_id: int
    chat_room_id: int
    user_id: str
    user_nickname: str
    user_location: str
    final_disease: Dict[str, Any]
    total_candidates: int
    recommendations: List[RecommendedHospitalResponse]
    search_criteria: Dict[str, Any]

    class Config:
        from_attributes = True


# ===== 장비 관련 스키마 =====


class HospitalRecommendationByDiseaseRequest(BaseModel):
    """질환명 기반 병원 추천(라이트) 요청"""

    disease_name: str = Field(..., description="질환명")
    user_id: str = Field(..., description="사용자 ID (UUID)")
    chat_room_id: int = Field(..., description="채팅방 ID")
    max_distance: Optional[float] = Field(20.0, description="최대 검색 거리 (km)")
    limit: Optional[int] = Field(3, description="추천 병원 수")


class HospitalRecommendationByDiseaseResponse(BaseModel):
    """질환명 기반 병원 추천(라이트) 응답"""

    chat_room_id: int
    user_id: str
    user_nickname: str
    user_location: str
    final_disease: Dict[str, Any]
    total_candidates: int
    recommendations: List[RecommendedHospitalResponse]
    search_criteria: Dict[str, Any]

    class Config:
        from_attributes = True


class EquipmentCategoryBase(BaseModel):
    """장비 대분류 기본 정보"""

    name: str
    code: str


class EquipmentCategoryCreate(EquipmentCategoryBase):
    """장비 대분류 생성"""

    pass


class EquipmentCategoryUpdate(EquipmentCategoryBase):
    """장비 대분류 수정"""

    pass


class EquipmentCategoryResponse(EquipmentCategoryBase):
    """장비 대분류 응답"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EquipmentSubcategoryBase(BaseModel):
    """장비 세분류 기본 정보"""

    category_id: int
    name: str
    code: str


class EquipmentSubcategoryCreate(EquipmentSubcategoryBase):
    """장비 세분류 생성"""

    pass


class EquipmentSubcategoryUpdate(EquipmentSubcategoryBase):
    """장비 세분류 수정"""

    pass


class EquipmentSubcategoryResponse(EquipmentSubcategoryBase):
    """장비 세분류 응답"""

    id: int
    created_at: datetime
    category: EquipmentCategoryResponse

    class Config:
        from_attributes = True


class EquipmentHospitalResponse(BaseModel):
    """장비 보유 병원 정보 (간단 버전)"""

    id: int
    name: str

    class Config:
        from_attributes = True


class EquipmentCategoryDetailResponse(EquipmentCategoryResponse):
    """장비 대분류 상세 응답"""

    updated_at: datetime
    subcategories: List[EquipmentSubcategoryResponse] = []

    class Config:
        from_attributes = True


class EquipmentSubcategoryDetailResponse(BaseModel):
    """장비 세분류 상세 응답"""

    id: int
    category_id: int
    name: str
    code: str
    created_at: datetime
    updated_at: datetime
    category: EquipmentCategoryResponse
    quantity: int = 0
    hospitals: List[EquipmentHospitalResponse] = []

    class Config:
        from_attributes = True
