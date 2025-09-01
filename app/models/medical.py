"""
의료 관련 모델
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Disease(Base):
    """질환 정보"""

    __tablename__ = "diseases"

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
    first_predictions = relationship(
        "ModelInferenceResult",
        foreign_keys="ModelInferenceResult.first_disease_id",
        back_populates="first_disease",
    )
    second_predictions = relationship(
        "ModelInferenceResult",
        foreign_keys="ModelInferenceResult.second_disease_id",
        back_populates="second_disease",
    )
    third_predictions = relationship(
        "ModelInferenceResult",
        foreign_keys="ModelInferenceResult.third_disease_id",
        back_populates="third_disease",
    )
    equipment_diseases = relationship("EquipmentDisease", back_populates="disease")