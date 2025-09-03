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
    # 실제 데이터 기반 필드들
    encrypted_code = Column(String, unique=True, nullable=False)  # 암호화된요양기호
    hospital_type_code = Column(String, nullable=True)  # 종별코드
    hospital_type_name = Column(
        String, nullable=True
    )  # 종별코드명 (의원, 병원, 종합병원)
    region_code = Column(String, nullable=True)  # 시도코드
    region_name = Column(String, nullable=True)  # 시도명
    district_code = Column(String, nullable=True)  # 시군구코드
    district_name = Column(String, nullable=True)  # 시군구명
    postal_code = Column(String, nullable=True)  # 우편번호
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    equipment = relationship("HospitalEquipment", back_populates="hospital")
    recommendations = relationship("HospitalRecommendation", back_populates="hospital")
    hospital_departments = relationship("HospitalDepartment", back_populates="hospital")


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
    # 실제 데이터 기반 필드들
    model_name = Column(String, nullable=True)  # 모델명 (예: HeartOn A15-G4)
    license_number = Column(String, nullable=True)  # 장비허가번호 (예: 제허14-1593호)
    quantity = Column(Integer, default=1, nullable=False)  # 장비수
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
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    distance = Column(Float, nullable=False)  # 사용자 위치로부터의 거리 (km)
    rank = Column(Integer, nullable=False)  # 추천 순위 (1, 2, 3)
    recommendation_score = Column(Float, nullable=True)  # 종합 추천 점수
    department_match = Column(Boolean, default=False)  # 진료과 매칭 여부
    equipment_match = Column(Boolean, default=False)  # 장비 매칭 여부
    recommended_reason = Column(Text, nullable=True)  # 추천 이유

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
    user = relationship("User", back_populates="hospital_recommendations")
