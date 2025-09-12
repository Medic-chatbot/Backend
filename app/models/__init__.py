"""
모델 모듈 초기화
"""

from app.models.chat import ChatMessage, ChatRoom
from app.models.department import Department, DepartmentDisease, HospitalDepartment
from app.models.equipment import (
    EquipmentDisease,
    MedicalEquipmentCategory,
    MedicalEquipmentSubcategory,
)
from app.models.hospital import Hospital, HospitalEquipment, HospitalRecommendation, HospitalType
from app.models.medical import Disease
from app.models.model_inference import ModelInferenceResult
from app.models.user import User
from app.models.disease_equipment import DiseaseEquipmentCategory
