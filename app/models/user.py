"""
사용자 관련 모델
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """사용자 테이블"""
    
    __tablename__ = "users"
    
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # 'MALE', 'FEMALE', 'OTHER'
    last_login_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    chat_rooms = relationship("ChatRoom", back_populates="user")
    user_location = relationship("UserLocation", back_populates="user", uselist=False)


class UserLocation(Base, UUIDMixin, TimestampMixin):
    """사용자 위치 정보 테이블"""
    
    __tablename__ = "user_locations"
    
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)
    
    # 관계 설정
    user = relationship("User", back_populates="user_location")
