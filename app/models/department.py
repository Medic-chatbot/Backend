"""
진료과 관련 모델
"""

import uuid
from datetime import datetime

from app.db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Department(Base):
    """진료과 정보"""

    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    department_diseases = relationship("DepartmentDisease", back_populates="department")
    hospital_departments = relationship(
        "HospitalDepartment", back_populates="department"
    )


class DepartmentDisease(Base):
    """진료과-질환 매핑"""

    __tablename__ = "department_diseases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    disease_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    department = relationship("Department", back_populates="department_diseases")
    disease = relationship("Disease", back_populates="department_diseases")


class HospitalDepartment(Base):
    """병원-진료과 매핑"""

    __tablename__ = "hospital_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정
    hospital = relationship("Hospital", back_populates="hospital_departments")
    department = relationship("Department", back_populates="hospital_departments")
