"""
사용자 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # 'MALE', 'FEMALE', 'OTHER'
    last_login_at = Column(DateTime, nullable=True)

    # 사용자 위치 정보 (카카오 지오코딩 결과)
    road_address = Column(Text, nullable=True)  # 도로명 주소
    latitude = Column(Float, nullable=True)  # 위도
    longitude = Column(Float, nullable=True)  # 경도

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    chat_rooms = relationship("ChatRoom", back_populates="user")
    hospital_recommendations = relationship(
        "HospitalRecommendation", back_populates="user"
    )
    inference_results = relationship("ModelInferenceResult", back_populates="user")
