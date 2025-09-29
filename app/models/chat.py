"""
채팅 관련 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ChatRoom(Base):
    """채팅방"""

    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True)  # 정수형 ID로 변경
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # 최종 진단 정보 (채팅에서 마지막으로 진단된 질환)
    final_disease_id = Column(
        Integer,  # medical 관련은 정수형으로 변경
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="chat_rooms")
    messages = relationship("ChatMessage", back_populates="chat_room")
    final_disease = relationship("Disease", back_populates="chat_rooms")
    inference_results = relationship("ModelInferenceResult", back_populates="chat_room")
    # 추천 컨텍스트 경계: 직전 추천을 유발한 USER 메시지 ID
    last_recommendation_message_id = Column(Integer, nullable=True)
    # 현재 진행 중인 증상 세션의 시작 메시지 ID
    current_session_start_message_id = Column(Integer, nullable=True)


class ChatMessage(Base):
    """채팅 메시지"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 정수형 ID로 변경
    chat_room_id = Column(
        Integer,  # ChatRoom의 id가 Integer로 변경됨
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_type = Column(String, nullable=False)  # USER, BOT
    content = Column(Text, nullable=False)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    chat_room = relationship("ChatRoom", back_populates="messages")
    inference_result = relationship(
        "ModelInferenceResult", back_populates="chat_message", uselist=False
    )
