"""
의료 관련 모델
"""

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, UUIDMixin


class Disease(Base, UUIDMixin, TimestampMixin):
    """질환 테이블"""
    
    __tablename__ = "diseases"
    
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 관계 설정
    disease_symptoms = relationship("DiseaseSymptom", back_populates="disease")
    equipment_diseases = relationship("EquipmentDisease", back_populates="disease")
    symptom_analyses = relationship("SymptomAnalysis", back_populates="predicted_disease")


class Symptom(Base, UUIDMixin, TimestampMixin):
    """증상 테이블"""
    
    __tablename__ = "symptoms"
    
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 관계 설정
    symptom_synonyms = relationship("SymptomSynonym", back_populates="symptom")
    disease_symptoms = relationship("DiseaseSymptom", back_populates="symptom")
    analysis_symptoms = relationship("AnalysisSymptom", back_populates="symptom")


class SymptomSynonym(Base, UUIDMixin, TimestampMixin):
    """증상 동의어 테이블"""
    
    __tablename__ = "symptom_synonyms"
    
    symptom_id = Column(UUID(as_uuid=True), ForeignKey("symptoms.id"), nullable=False, index=True)
    synonym = Column(String, unique=True, nullable=False, index=True)
    source = Column(String, nullable=True)  # 'USER_INPUT', 'PREDEFINED'
    frequency = Column(Integer, default=1, nullable=False)
    
    # 관계 설정
    symptom = relationship("Symptom", back_populates="symptom_synonyms")


class DiseaseSymptom(Base, UUIDMixin, TimestampMixin):
    """질환-증상 매핑 테이블"""
    
    __tablename__ = "disease_symptoms"
    
    disease_id = Column(UUID(as_uuid=True), ForeignKey("diseases.id"), nullable=False, index=True)
    symptom_id = Column(UUID(as_uuid=True), ForeignKey("symptoms.id"), nullable=False, index=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    
    # 관계 설정
    disease = relationship("Disease", back_populates="disease_symptoms")
    symptom = relationship("Symptom", back_populates="disease_symptoms")


class MedicalEquipmentCategory(Base, UUIDMixin, TimestampMixin):
    """의료장비 대분류 테이블"""
    
    __tablename__ = "medical_equipment_categories"
    
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 관계 설정
    subcategories = relationship("MedicalEquipmentSubcategory", back_populates="category")


class MedicalEquipmentSubcategory(Base, UUIDMixin, TimestampMixin):
    """의료장비 세분류 테이블"""
    
    __tablename__ = "medical_equipment_subcategories"
    
    category_id = Column(UUID(as_uuid=True), ForeignKey("medical_equipment_categories.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # 관계 설정
    category = relationship("MedicalEquipmentCategory", back_populates="subcategories")
    equipment_diseases = relationship("EquipmentDisease", back_populates="equipment_subcategory")
    hospital_equipment = relationship("HospitalEquipment", back_populates="equipment_subcategory")


class EquipmentDisease(Base, UUIDMixin, TimestampMixin):
    """의료장비-질환 매핑 테이블"""
    
    __tablename__ = "equipment_diseases"
    
    equipment_subcategory_id = Column(UUID(as_uuid=True), ForeignKey("medical_equipment_subcategories.id"), nullable=False, index=True)
    disease_id = Column(UUID(as_uuid=True), ForeignKey("diseases.id"), nullable=False, index=True)
    
    # 관계 설정
    equipment_subcategory = relationship("MedicalEquipmentSubcategory", back_populates="equipment_diseases")
    disease = relationship("Disease", back_populates="equipment_diseases")
