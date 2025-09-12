"""
의료 정보 관련 서비스 로직 - 리팩토링 버전
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.models.department import Department, DepartmentDisease, HospitalDepartment
from app.models.equipment import (
    EquipmentDisease,
    MedicalEquipmentCategory,
    MedicalEquipmentSubcategory,
)
from app.models.hospital import Hospital, HospitalEquipment
from app.models.medical import Disease
from app.models.model_inference import ModelInferenceResult
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

logger = logging.getLogger(__name__)


class MedicalService:
    """의료 정보 관련 비즈니스 로직 - 타입 안전성 강화"""

    # ===== 기본 조회 메서드들 =====

    @staticmethod
    def get_disease_by_id(db: Session, disease_id: int) -> Optional[Disease]:
        """질환 ID로 질환 정보 조회"""
        return db.query(Disease).filter(Disease.id == disease_id).first()

    @staticmethod
    def get_department_by_id(db: Session, department_id: int) -> Optional[Department]:
        """진료과 ID로 진료과 정보 조회"""
        return db.query(Department).filter(Department.id == department_id).first()

    @staticmethod
    def get_hospital_by_id(db: Session, hospital_id: int) -> Optional[Hospital]:
        """병원 ID로 병원 정보 조회"""
        return db.query(Hospital).filter(Hospital.id == hospital_id).first()

    @staticmethod
    def get_all_diseases(db: Session) -> List[Disease]:
        """모든 질환 목록 조회"""
        return db.query(Disease).all()

    @staticmethod
    def get_diseases_by_name(db: Session, name: str) -> List[Disease]:
        """질환 이름으로 검색"""
        return db.query(Disease).filter(Disease.name.ilike(f"%{name}%")).all()

    @staticmethod
    def get_all_departments(db: Session) -> List[Department]:
        """모든 진료과 목록 조회"""
        return db.query(Department).all()

    @staticmethod
    def get_departments_by_name(db: Session, name: str) -> List[Department]:
        """진료과 이름으로 검색"""
        return db.query(Department).filter(Department.name.ilike(f"%{name}%")).all()

    @staticmethod
    def get_departments_by_disease(db: Session, disease_id: int) -> List[Department]:
        """질환 ID로 관련 진료과 조회"""
        # department_diseases 테이블을 통해 조회
        return (
            db.query(Department)
            .join(DepartmentDisease)
            .filter(DepartmentDisease.disease_id == disease_id)
            .all()
        )

    @staticmethod
    def get_diseases_by_department(db: Session, department_id: int) -> List[Disease]:
        """진료과 ID로 관련 질환 조회"""
        # department_diseases 테이블을 통해 조회
        return (
            db.query(Disease)
            .join(DepartmentDisease)
            .filter(DepartmentDisease.department_id == department_id)
            .all()
        )

    @staticmethod
    def get_hospitals_by_department(db: Session, department_id: int) -> List[Hospital]:
        """진료과 ID로 관련 병원 조회"""
        # hospital_departments 테이블을 통해 조회
        return (
            db.query(Hospital)
            .join(HospitalDepartment)
            .filter(HospitalDepartment.department_id == department_id)
            .all()
        )

    @staticmethod
    def get_disease_detail_by_id(
        db: Session, disease_id: int
    ) -> Optional[Dict[str, Any]]:
        """ID로 질환 상세 정보 조회 (진료과 포함)"""
        disease = MedicalService.get_disease_by_id(db, disease_id)
        if not disease:
            return None

        # 관련 진료과들 조회
        departments = MedicalService.get_departments_by_disease(db, int(disease.id))

        # Dict로 변환
        department_dicts = [
            {
                "id": dept.id,
                "name": dept.name,
                "created_at": dept.created_at,
            }
            for dept in departments
        ]

        return {
            "id": disease.id,
            "name": disease.name,
            "description": disease.description,
            "created_at": disease.created_at,
            "departments": department_dicts,
        }

    @staticmethod
    def get_department_detail_by_id(
        db: Session, department_id: int
    ) -> Optional[Dict[str, Any]]:
        """ID로 진료과 상세 정보 조회 (관련 질환, 병원 포함)"""
        department = MedicalService.get_department_by_id(db, department_id)
        if not department:
            return None

        # 관련 질환들 조회
        diseases = MedicalService.get_diseases_by_department(db, int(department.id))

        # 관련 병원들 조회(+ specialist_count)
        from app.models.department import HospitalDepartment as HD
        hospital_rows = (
            db.query(Hospital, HD.specialist_count)
            .join(HD, HD.hospital_id == Hospital.id)
            .filter(HD.department_id == department.id)
            .all()
        )

        # Dict로 변환
        disease_dicts = [
            {
                "id": disease.id,
                "name": disease.name,
                "description": disease.description,
                "created_at": disease.created_at,
            }
            for disease in diseases
        ]

        hospital_dicts = [
            {
                "id": h.id,
                "name": h.name,
                "address": h.address,
                "hospital_type_name": h.hospital_type_name,
                "phone": h.phone,
                "created_at": h.created_at,
                "specialist_count": sc,
            }
            for (h, sc) in hospital_rows
        ]

        return {
            "id": department.id,
            "name": department.name,
            "created_at": department.created_at,
            "diseases": disease_dicts,
            "hospitals": hospital_dicts,
        }

    @staticmethod
    def get_hospital_detail_by_id(
        db: Session, hospital_id: int
    ) -> Optional[Dict[str, Any]]:
        """ID로 병원 상세 정보 조회 (모든 정보 포함)"""
        hospital = MedicalService.get_hospital_by_id(db, hospital_id)
        if not hospital:
            return None

        # 관련 진료과들 조회(+ specialist_count)
        dept_rows = (
            db.query(Department, HospitalDepartment.specialist_count)
            .join(HospitalDepartment)
            .filter(HospitalDepartment.hospital_id == hospital.id)
            .all()
        )

        # 보유 장비들 조회 (대분류 기준 구조로 변경)
        equipment_rows = (
            db.query(HospitalEquipment)
            .filter(
                HospitalEquipment.hospital_id == hospital.id,
                HospitalEquipment.deleted_at.is_(None),
            )
            .all()
        )

        # Dict로 변환
        department_dicts = [
            {
                "id": dept.id,
                "name": dept.name,
                "created_at": dept.created_at,
                "specialist_count": sc,
            }
            for (dept, sc) in dept_rows
        ]

        equipment_dicts = [
            {
                "category_id": row.equipment_category_id,
                "category_name": row.equipment_category_name,
                "category_code": row.equipment_category_code,
                "quantity": row.quantity,
            }
            for row in equipment_rows
        ]

        return {
            "id": hospital.id,
            "name": hospital.name,
            "address": hospital.address,
            "latitude": hospital.latitude,
            "longitude": hospital.longitude,
            "encrypted_code": hospital.encrypted_code,
            "hospital_type_code": hospital.hospital_type_code,
            "hospital_type_name": hospital.hospital_type_name,
            "region_code": hospital.region_code,
            "region_name": hospital.region_name,
            "district_code": hospital.district_code,
            "district_name": hospital.district_name,
            "postal_code": hospital.postal_code,
            "phone": hospital.phone,
            "website": hospital.website,
            "created_at": hospital.created_at,
            "departments": department_dicts,
            "equipment": equipment_dicts,
        }

    # ===== 검색 및 필터링 메서드들 =====

    @staticmethod
    def get_hospitals_with_filters(
        db: Session,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        disease_id: Optional[int] = None,
    ) -> List[Hospital]:
        """다중 필터링으로 병원 조회"""
        query = db.query(Hospital)

        # 병원 이름 검색
        if search:
            query = query.filter(Hospital.name.ilike(f"%{search}%"))

        # 진료과 필터링
        if department_id:
            department = MedicalService.get_department_by_id(db, department_id)
            if department:
                query = query.join(HospitalDepartment).filter(
                    HospitalDepartment.department_id == department.id
                )

        # 질환 필터링 (질환 -> 진료과 -> 병원)
        if disease_id:
            disease = MedicalService.get_disease_by_id(db, disease_id)
            if disease:
                # 질환과 관련된 진료과들
                dept_ids = (
                    db.query(DepartmentDisease.department_id)
                    .filter(DepartmentDisease.disease_id == disease.id)
                    .all()
                )
                dept_id_list = [row[0] for row in dept_ids]
                query = query.join(HospitalDepartment).filter(
                    HospitalDepartment.department_id.in_(dept_id_list)
                )

        return query.all()

    # ===== 모델 추론 관련 메서드들 =====

    @staticmethod
    def get_inference_result_by_id(
        db: Session, result_id: int
    ) -> Optional[ModelInferenceResult]:
        """모델 추론 결과 ID로 조회"""
        return (
            db.query(ModelInferenceResult)
            .filter(ModelInferenceResult.id == result_id)
            .options(
                joinedload(ModelInferenceResult.first_disease),
                joinedload(ModelInferenceResult.second_disease),
                joinedload(ModelInferenceResult.third_disease),
            )
            .first()
        )

    @staticmethod
    def create_inference_result(
        db: Session,
        chat_message_id: int,
        input_text: str,
        first_disease_id: int,
        first_score: float,
        second_disease_id: Optional[int] = None,
        second_score: Optional[float] = None,
        third_disease_id: Optional[int] = None,
        third_score: Optional[float] = None,
        inference_time: Optional[float] = None,
    ) -> ModelInferenceResult:
        """모델 추론 결과 생성"""
        inference_result = ModelInferenceResult(
            chat_message_id=chat_message_id,
            input_text=input_text,
            first_disease_id=first_disease_id,
            first_disease_score=first_score,
            second_disease_id=second_disease_id,
            second_disease_score=second_score,
            third_disease_id=third_disease_id,
            third_disease_score=third_score,
            inference_time=inference_time,
        )

        db.add(inference_result)
        db.commit()
        db.refresh(inference_result)

        return inference_result

    # ===== 통합 검색 메서드들 =====

    @staticmethod
    def get_disease_with_departments(
        db: Session, disease_id: int
    ) -> Optional[Tuple[Disease, List[Department]]]:
        """질환과 관련 진료과를 함께 조회"""
        disease = MedicalService.get_disease_by_id(db, disease_id)
        if not disease:
            return None

        departments = MedicalService.get_departments_by_disease(db, disease_id)
        return disease, departments

    @staticmethod
    def search_diseases_with_departments(
        db: Session, query_text: str, limit: int = 10
    ) -> List[Tuple[Disease, List[Department]]]:
        """질환 검색과 함께 관련 진료과 조회"""
        diseases = (
            db.query(Disease)
            .filter(Disease.name.ilike(f"%{query_text}%"))
            .limit(limit)
            .all()
        )

        results = []
        for disease in diseases:
            departments = MedicalService.get_departments_by_disease(db, int(disease.id))
            results.append((disease, departments))

        return results

    # ===== 장비 관련 서비스 메서드 =====

    @staticmethod
    def get_all_equipment_categories(db: Session) -> List[MedicalEquipmentCategory]:
        """모든 장비 대분류 조회"""
        return (
            db.query(MedicalEquipmentCategory)
            .filter(MedicalEquipmentCategory.deleted_at.is_(None))
            .order_by(MedicalEquipmentCategory.name)
            .all()
        )

    @staticmethod
    def get_all_hospital_types(db: Session):
        from app.models.hospital import HospitalType
        return db.query(HospitalType).all()

    @staticmethod
    def get_hospitals_by_type(
        db: Session, type_code: str | None = None, type_name: str | None = None
    ) -> List[Hospital]:
        query = db.query(Hospital)
        if type_code:
            query = query.filter(Hospital.hospital_type_code == str(type_code))
        if type_name:
            query = query.filter(Hospital.hospital_type_name == str(type_name))
        return query.all()

    @staticmethod
    def get_all_equipment_subcategories(
        db: Session,
    ) -> List[MedicalEquipmentSubcategory]:
        """모든 장비 세분류 조회"""
        return (
            db.query(MedicalEquipmentSubcategory)
            .options(joinedload(MedicalEquipmentSubcategory.category))
            .filter(MedicalEquipmentSubcategory.deleted_at.is_(None))
            .order_by(MedicalEquipmentSubcategory.name)
            .all()
        )

    @staticmethod
    def get_equipment_category_by_id(
        db: Session, category_id: int
    ) -> Optional[MedicalEquipmentCategory]:
        """장비 대분류 ID로 조회"""
        return (
            db.query(MedicalEquipmentCategory)
            .options(joinedload(MedicalEquipmentCategory.subcategories))
            .filter(
                MedicalEquipmentCategory.id == category_id,
                MedicalEquipmentCategory.deleted_at.is_(None),
            )
            .first()
        )

    @staticmethod
    def get_equipment_subcategory_by_id(
        db: Session, subcategory_id: int
    ) -> Optional[MedicalEquipmentSubcategory]:
        """장비 세분류 ID로 조회"""
        return (
            db.query(MedicalEquipmentSubcategory)
            .options(
                joinedload(MedicalEquipmentSubcategory.category),
                # NOTE: hospital_equipment 관계가 제거되어 주석 처리
                # joinedload(MedicalEquipmentSubcategory.hospital_equipment).joinedload(
                #     HospitalEquipment.hospital
                # ),
            )
            .filter(
                MedicalEquipmentSubcategory.id == subcategory_id,
                MedicalEquipmentSubcategory.deleted_at.is_(None),
            )
            .first()
        )

    @staticmethod
    def get_hospitals_by_equipment_category(
        db: Session, category_id: int
    ) -> List[Hospital]:
        """특정 장비 대분류를 보유한 병원 목록 조회 (새로운 구조)"""
        return (
            db.query(Hospital)
            .join(HospitalEquipment)
            .filter(
                HospitalEquipment.equipment_category_id == category_id,
                Hospital.deleted_at.is_(None),
                HospitalEquipment.deleted_at.is_(None),
            )
            .distinct()
            .all()
        )

    @staticmethod
    def get_hospitals_by_equipment_subcategory(
        db: Session, subcategory_id: int
    ) -> List[Hospital]:
        """특정 장비 세분류를 보유한 병원 목록 조회 (레거시 지원)"""
        # 세분류 ID로 대분류 찾기
        subcategory = (
            db.query(MedicalEquipmentSubcategory)
            .filter(MedicalEquipmentSubcategory.id == subcategory_id)
            .first()
        )

        if not subcategory:
            return []

        # 대분류 ID로 병원 조회
        return MedicalService.get_hospitals_by_equipment_category(
            db, subcategory.category_id
        )

    @staticmethod
    def get_equipment_subcategory_detail(
        db: Session, subcategory_id: int
    ) -> Optional[Dict[str, Any]]:
        """장비 세분류 상세 정보 조회 (병원 정보 포함)"""
        subcategory = MedicalService.get_equipment_subcategory_by_id(db, subcategory_id)
        if not subcategory:
            return None

        hospitals = MedicalService.get_hospitals_by_equipment_subcategory(
            db, subcategory_id
        )

        # 총 수량 계산 (대분류 기준으로 합산)
        from app.models.hospital import HospitalEquipment

        total_quantity = (
            db.query(func.coalesce(func.sum(HospitalEquipment.quantity), 0))
            .filter(
                HospitalEquipment.equipment_category_id == subcategory.category_id,
                HospitalEquipment.deleted_at.is_(None),
            )
            .scalar()
        )

        return {
            "id": subcategory.id,
            "name": subcategory.name,
            "code": subcategory.code,
            "category": {
                "id": subcategory.category.id,
                "name": subcategory.category.name,
                "code": subcategory.category.code,
            },
            "quantity": total_quantity,
            "created_at": subcategory.created_at,
            "updated_at": subcategory.updated_at,
            "hospitals": [
                {"id": hospital.id, "name": hospital.name} for hospital in hospitals
            ],
        }
