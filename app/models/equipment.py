"""
의료장비 관련 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class MedicalEquipmentCategory(Base):
    """의료장비 대분류"""

    __tablename__ = "medical_equipment_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    subcategories = relationship(
        "MedicalEquipmentSubcategory", back_populates="category"
    )


class MedicalEquipmentSubcategory(Base):
    """의료장비 세분류"""

    __tablename__ = "medical_equipment_subcategories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medical_equipment_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    category = relationship("MedicalEquipmentCategory", back_populates="subcategories")
    hospital_equipment = relationship(
        "HospitalEquipment", back_populates="equipment_subcategory"
    )
    equipment_diseases = relationship(
        "EquipmentDisease", back_populates="equipment_subcategory"
    )


class EquipmentDisease(Base):
    """의료장비-질환 매핑"""

    __tablename__ = "equipment_diseases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_subcategory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medical_equipment_subcategories.id", ondelete="CASCADE"),
        nullable=False,
    )
    disease_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    equipment_subcategory = relationship(
        "MedicalEquipmentSubcategory", back_populates="equipment_diseases"
    )
    disease = relationship("Disease", back_populates="equipment_diseases")
