"""
모델 추론 결과 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ModelInferenceResult(Base):
    """모델 추론 결과"""

    __tablename__ = "model_inference_results"

    id = Column(Integer, primary_key=True)

    # 사용자 및 채팅방 정보 (채팅 메시지와 연결되지 않은 경우)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # 채팅 메시지와 연결된 경우에는 선택적
    )
    chat_room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=True,  # 채팅 메시지와 연결된 경우에는 선택적
    )

    # 채팅 메시지 연결 (기존 방식과의 호환성)
    chat_message_id = Column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=True,  # 독립적인 추론 결과도 허용
    )

    input_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=True)  # 형태소 분석된 텍스트

    # 1순위 예측
    first_disease_id = Column(
        Integer,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,  # 질병 매핑이 없는 경우도 허용
    )
    first_disease_score = Column(Float, nullable=False)
    first_disease_label = Column(String, nullable=True)  # 질병명 저장

    # 2순위 예측
    second_disease_id = Column(
        Integer,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,
    )
    second_disease_score = Column(Float, nullable=True)
    second_disease_label = Column(String, nullable=True)

    # 3순위 예측
    third_disease_id = Column(
        Integer,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,
    )
    third_disease_score = Column(Float, nullable=True)
    third_disease_label = Column(String, nullable=True)

    inference_time = Column(Float, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="inference_results")
    chat_room = relationship("ChatRoom", back_populates="inference_results")
    chat_message = relationship("ChatMessage", back_populates="inference_result")
    first_disease = relationship(
        "Disease", foreign_keys=[first_disease_id], back_populates="first_predictions"
    )
    second_disease = relationship(
        "Disease", foreign_keys=[second_disease_id], back_populates="second_predictions"
    )
    third_disease = relationship(
        "Disease", foreign_keys=[third_disease_id], back_populates="third_predictions"
    )
    hospital_recommendations = relationship(
        "HospitalRecommendation", back_populates="inference_result"
    )
