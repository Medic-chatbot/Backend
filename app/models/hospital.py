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


class HospitalType(Base):
    """병원 종별 코드/명 테이블 (요양기호명/코드 아님)"""

    __tablename__ = "hospital_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)  # 종별코드 (예: 31, 21)
    name = Column(String, nullable=False)  # 종별코드명 (예: 의원, 병원, 종합병원, 상급종합병원)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

class Hospital(Base):
    """병원 정보"""

    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    # 시드 데이터 추가 필드들
    opening_date = Column(Date, nullable=True)  # 개설일자
    total_doctors = Column(Integer, nullable=True)  # 총의사수
    dong_name = Column(String, nullable=True)  # 읍면동

    # 주차 정보
    parking_slots = Column(Integer, nullable=True)  # 주차_가능대수
    parking_fee_required = Column(String, nullable=True)  # 주차_비용 부담여부 (Y/N)
    parking_notes = Column(Text, nullable=True)  # 주차_기타 안내사항

    # 휴진 안내
    closed_sunday = Column(String, nullable=True)  # 휴진안내_일요일
    closed_holiday = Column(String, nullable=True)  # 휴진안내_공휴일

    # 응급실 운영
    emergency_day_available = Column(String, nullable=True)  # 응급실_주간_운영여부
    emergency_day_phone1 = Column(String, nullable=True)  # 응급실_주간_전화번호1
    emergency_day_phone2 = Column(String, nullable=True)  # 응급실_주간_전화번호2
    emergency_night_available = Column(String, nullable=True)  # 응급실_야간_운영여부
    emergency_night_phone1 = Column(String, nullable=True)  # 응급실_야간_전화번호1
    emergency_night_phone2 = Column(String, nullable=True)  # 응급실_야간_전화번호2

    # 점심시간 및 접수시간
    lunch_time_weekday = Column(String, nullable=True)  # 점심시간_평일
    lunch_time_saturday = Column(String, nullable=True)  # 점심시간_토요일
    reception_time_weekday = Column(String, nullable=True)  # 접수시간_평일
    reception_time_saturday = Column(String, nullable=True)  # 접수시간_토요일

    # 진료시간 (요일별)
    treatment_hours = Column(JSON, nullable=True)  # 진료시간 전체를 JSON으로 저장

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 새로운 대분류 기반 필드들 (올바른 구조)
    hospital_name = Column(String, nullable=True)  # 병원명 (조회 편의성)
    equipment_category_id = Column(
        Integer,
        ForeignKey("medical_equipment_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_category_name = Column(String, nullable=True)  # 장비 대분류명
    equipment_category_code = Column(String, nullable=True)  # 장비 대분류코드
    quantity = Column(Integer, default=1, nullable=False)  # 장비수

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # 관계 설정 (올바른 구조)
    hospital = relationship("Hospital", back_populates="equipment")
    equipment_category = relationship(
        "MedicalEquipmentCategory", back_populates="hospital_equipment"
    )


class HospitalRecommendation(Base):
    """병원 추천 결과"""

    __tablename__ = "hospital_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 정수형 ID로 변경
    inference_result_id = Column(
        Integer,  # ModelInferenceResult의 id가 정수형으로 변경됨
        ForeignKey("model_inference_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id = Column(
        Integer,  # Hospital의 id가 정수형으로 변경됨
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),  # user 관련은 UUID 유지
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
