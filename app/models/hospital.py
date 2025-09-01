"""
병원 관련 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Hospital(Base):
    """병원 정보"""

    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    type = Column(String, nullable=True)
    department = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    operating_hours = Column(JSON, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    equipment = relationship("HospitalEquipment", back_populates="hospital")
    recommendations = relationship("HospitalRecommendation", back_populates="hospital")


class HospitalEquipment(Base):
    """병원 보유 장비 정보"""

    __tablename__ = "hospital_equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_subcategory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medical_equipment_subcategories.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity = Column(Integer, default=1, nullable=False)
    installation_date = Column(Date, nullable=True)
    is_operational = Column(Boolean, default=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    hospital = relationship("Hospital", back_populates="equipment")
    equipment_subcategory = relationship(
        "MedicalEquipmentSubcategory", back_populates="hospital_equipment"
    )


class HospitalRecommendation(Base):
    """병원 추천 결과"""

    __tablename__ = "hospital_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inference_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("model_inference_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    distance = Column(Float, nullable=False)
    recommended_reason = Column(Text, nullable=True)
    recommendation_score = Column(Float, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    inference_result = relationship(
        "ModelInferenceResult", back_populates="hospital_recommendations"
    )
    hospital = relationship("Hospital", back_populates="recommendations")
    user_location = relationship(
        "UserLocation", back_populates="hospital_recommendations"
    )
