"""
채팅 관련 모델
"""

from app.db.base import Base, TimestampMixin, UUIDMixin
from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ChatRoom(Base, UUIDMixin, TimestampMixin):
    """채팅방 테이블"""

    __tablename__ = "chat_rooms"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    title = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="chat_rooms")
    messages = relationship("ChatMessage", back_populates="chat_room")


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    """채팅 메시지 테이블"""

    __tablename__ = "chat_messages"

    chat_room_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False, index=True
    )
    message_type = Column(String, nullable=False)  # 'USER', 'BOT'
    content = Column(Text, nullable=False)

    # 관계 설정
    chat_room = relationship("ChatRoom", back_populates="messages")
    symptom_analysis = relationship(
        "SymptomAnalysis", back_populates="chat_message", uselist=False
    )
