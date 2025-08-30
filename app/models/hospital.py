"""
병원 관련 모델
"""

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, UUIDMixin


class Hospital(Base, UUIDMixin, TimestampMixin):
    """병원 정보 테이블"""
    
    __tablename__ = "hospitals"
    
    name = Column(String, nullable=False, index=True)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    type = Column(String, nullable=True)  # 종합병원, 의원 등
    department = Column(String, nullable=True)  # 진료과목
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    operating_hours = Column(JSON, nullable=True)
    
    # 관계 설정
    hospital_equipment = relationship("HospitalEquipment", back_populates="hospital")
    hospital_recommendations = relationship("HospitalRecommendation", back_populates="hospital")


class HospitalEquipment(Base, UUIDMixin, TimestampMixin):
    """병원-의료장비 보유 현황 테이블"""
    
    __tablename__ = "hospital_equipment"
    
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False, index=True)
    equipment_subcategory_id = Column(UUID(as_uuid=True), ForeignKey("medical_equipment_subcategories.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    installation_date = Column(Date, nullable=True)
    is_operational = Column(Boolean, default=True, nullable=False)
    
    # 관계 설정
    hospital = relationship("Hospital", back_populates="hospital_equipment")
    equipment_subcategory = relationship("MedicalEquipmentSubcategory", back_populates="hospital_equipment")
