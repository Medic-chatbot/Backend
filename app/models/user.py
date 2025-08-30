"""
사용자 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(
        String, nullable=False
    )  # 변경: hashed_password -> password_hash
    nickname = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # 'MALE', 'FEMALE', 'OTHER'
    last_login_at = Column(DateTime, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)
