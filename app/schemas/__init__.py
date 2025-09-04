"""
스키마 모듈 초기화 - 순환 참조 방지
"""

# 기본 스키마들만 import (상세 스키마는 필요시 직접 import)
from app.schemas.auth import Token, UserCreate, UserLogin, UserUpdate
from app.schemas.base import BaseMedicalEntity, BaseResponse, TimestampMixin
from app.schemas.medical import (
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    MedicalEquipmentCategoryResponse,
    MedicalEquipmentSubcategoryResponse,
    ModelInferenceRequest,
    ModelInferenceResponse,
    RecommendedHospitalResponse,
)
from app.schemas.user import UserLocationUpdate, UserResponse

# 상세 스키마들은 명시적으로 import하지 않음 (필요시 직접 import)
# - DiseaseDetailResponse
# - DepartmentDetailResponse
# - HospitalDetailResponse
# - ChatDiagnosisResponse
# - DiseaseWithDepartmentsResponse
# 등은 각 엔드포인트에서 필요시 직접 import하여 사용
