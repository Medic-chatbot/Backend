"""
Base 모델 정의
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """타임스탬프 Mixin 클래스"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)


class UUIDMixin:
    """UUID Primary Key Mixin 클래스"""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
