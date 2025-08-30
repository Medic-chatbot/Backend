"""
모든 모델을 import하는 패키지
"""

from app.models.user import User, UserLocation
from app.models.chat import ChatRoom, ChatMessage
from app.models.medical import (
    Disease, 
    Symptom, 
    SymptomSynonym, 
    DiseaseSymptom,
    MedicalEquipmentCategory,
    MedicalEquipmentSubcategory,
    EquipmentDisease
)
from app.models.hospital import Hospital, HospitalEquipment
from app.models.analysis import SymptomAnalysis, AnalysisSymptom, HospitalRecommendation

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
