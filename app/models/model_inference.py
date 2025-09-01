"""
모델 추론 결과 모델
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ModelInferenceResult(Base):
    """모델 추론 결과"""

    __tablename__ = "model_inference_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    input_text = Column(Text, nullable=False)
    
    # 1순위 예측
    first_disease_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=False,
    )
    first_disease_score = Column(Float, nullable=False)
    
    # 2순위 예측
    second_disease_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,
    )
    second_disease_score = Column(Float, nullable=True)
    
    # 3순위 예측
    third_disease_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,
    )
    third_disease_score = Column(Float, nullable=True)
    
    inference_time = Column(Float, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
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
    hospital_recommendations = relationship("HospitalRecommendation", back_populates="inference_result")
