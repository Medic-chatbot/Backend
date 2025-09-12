"""
질환-장비(대분류) 매핑 모델
"""

from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class DiseaseEquipmentCategory(Base):
    __tablename__ = "disease_equipment_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    disease_id = Column(Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False)
    equipment_category_id = Column(
        Integer, ForeignKey("medical_equipment_categories.id", ondelete="CASCADE"), nullable=False
    )

    # 중복 데이터 방지 및 조회 편의용 필드
    disease_name = Column(String, nullable=False)
    equipment_category_name = Column(String, nullable=False)
    equipment_category_code = Column(String, nullable=False)
    source = Column(String, nullable=True)  # 예: seed_fin_v1

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # 관계 (옵션)
    disease = relationship("Disease", back_populates="equipment_diseases_categories", lazy="joined")
    equipment_category = relationship(
        "MedicalEquipmentCategory", back_populates="disease_mappings", lazy="joined"
    )

