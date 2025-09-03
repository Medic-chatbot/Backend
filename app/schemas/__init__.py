"""
스키마 모듈 초기화
"""

from app.schemas.auth import Token, UserCreate, UserLogin, UserUpdate
from app.schemas.medical import (
    ChatDiagnosisResponse,
    ChatSymptomAnalysisRequest,
    DepartmentDiseaseResponse,
    DepartmentResponse,
    DiseaseResponse,
    DiseaseWithDepartmentsResponse,
    EquipmentDiseaseResponse,
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    HospitalResponse,
    MedicalEquipmentCategoryResponse,
    MedicalEquipmentSubcategoryResponse,
    ModelInferenceRequest,
    ModelInferenceResponse,
    RecommendedHospitalResponse,
)
from app.schemas.user import UserLocationUpdate, UserResponse
