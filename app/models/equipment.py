"""
의료장비 관련 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class MedicalEquipmentCategory(Base):
    """의료장비 대분류"""

    __tablename__ = "medical_equipment_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(
        String, unique=True, nullable=False
    )  # 장비대분류명 (예: 제세동기, 일반엑스선촬영장치)
    code = Column(
        String, unique=True, nullable=False
    )  # 장비대분류코드 (예: D205, B101)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(
        Integer,
        ForeignKey("medical_equipment_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(
        String, nullable=False
    )  # 장비세분류명 (예: 제세동기, 일반엑스선촬영장치(아날로그))
    code = Column(String, nullable=False)  # 장비세분류코드 (예: D20500, B10101)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_subcategory_id = Column(
        Integer,
        ForeignKey("medical_equipment_subcategories.id", ondelete="CASCADE"),
        nullable=False,
    )
    disease_id = Column(
        Integer,
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
