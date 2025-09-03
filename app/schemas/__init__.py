"""
스키마 모듈 초기화
"""

from app.schemas.auth import Token, UserCreate, UserLogin, UserUpdate
from app.schemas.medical import (
    DepartmentResponse,
    DiseaseResponse,
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    HospitalResponse,
    ModelInferenceRequest,
    ModelInferenceResponse,
)
from app.schemas.user import UserLocationUpdate, UserResponse
