"""
모든 모델을 import하는 패키지
"""

from app.models.analysis import AnalysisSymptom, HospitalRecommendation, SymptomAnalysis
from app.models.chat import ChatMessage, ChatRoom
from app.models.hospital import Hospital, HospitalEquipment
from app.models.medical import (
    Disease,
    DiseaseSymptom,
    EquipmentDisease,
    MedicalEquipmentCategory,
    MedicalEquipmentSubcategory,
    Symptom,
    SymptomSynonym,
)
from app.models.user import User, UserLocation

__all__ = [
    "User",
    "UserLocation",
    "ChatRoom",
    "ChatMessage",
    "Disease",
    "Symptom",
    "SymptomSynonym",
    "DiseaseSymptom",
    "MedicalEquipmentCategory",
    "MedicalEquipmentSubcategory",
    "EquipmentDisease",
    "Hospital",
    "HospitalEquipment",
    "SymptomAnalysis",
    "AnalysisSymptom",
    "HospitalRecommendation",
]
