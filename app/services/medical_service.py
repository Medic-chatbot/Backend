"""
의료 정보 관련 서비스 로직
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from app.models.department import Department, DepartmentDisease
from app.models.equipment import EquipmentDisease, MedicalEquipmentSubcategory
from app.models.medical import Disease
from app.models.model_inference import ModelInferenceResult
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class MedicalService:
    """의료 정보 관련 비즈니스 로직"""

    @staticmethod
    def get_disease_by_id(db: Session, disease_id: UUID) -> Optional[Disease]:
        """질환 ID로 질환 정보 조회"""
        return db.query(Disease).filter(Disease.id == disease_id).first()

    @staticmethod
    def get_diseases_by_name(db: Session, name: str) -> List[Disease]:
        """질환 이름으로 검색"""
        return db.query(Disease).filter(Disease.name.ilike(f"%{name}%")).all()

    @staticmethod
    def get_all_diseases(db: Session, limit: int = 100) -> List[Disease]:
        """모든 질환 목록 조회"""
        return db.query(Disease).limit(limit).all()

    @staticmethod
    def get_departments_by_disease(db: Session, disease_id: UUID) -> List[Department]:
        """질환 ID로 관련 진료과 조회"""
        return (
            db.query(Department)
            .join(DepartmentDisease)
            .filter(DepartmentDisease.disease_id == disease_id)
            .all()
        )

    @staticmethod
    def get_diseases_by_department(db: Session, department_id: UUID) -> List[Disease]:
        """진료과 ID로 관련 질환 조회"""
        return (
            db.query(Disease)
            .join(DepartmentDisease)
            .filter(DepartmentDisease.department_id == department_id)
            .all()
        )

    @staticmethod
    def get_all_departments(db: Session) -> List[Department]:
        """모든 진료과 목록 조회"""
        return db.query(Department).all()

    @staticmethod
    def get_department_by_id(db: Session, department_id: UUID) -> Optional[Department]:
        """진료과 ID로 진료과 정보 조회"""
        return db.query(Department).filter(Department.id == department_id).first()

    @staticmethod
    def get_equipment_by_disease(
        db: Session, disease_id: UUID
    ) -> List[MedicalEquipmentSubcategory]:
        """질환 ID로 관련 의료장비 조회"""
        return (
            db.query(MedicalEquipmentSubcategory)
            .join(EquipmentDisease)
            .filter(EquipmentDisease.disease_id == disease_id)
            .options(joinedload(MedicalEquipmentSubcategory.category))
            .all()
        )

    @staticmethod
    def get_diseases_by_equipment(db: Session, equipment_id: UUID) -> List[Disease]:
        """의료장비 ID로 관련 질환 조회"""
        return (
            db.query(Disease)
            .join(EquipmentDisease)
            .filter(EquipmentDisease.equipment_subcategory_id == equipment_id)
            .all()
        )

    @staticmethod
    def get_inference_result_by_id(
        db: Session, result_id: UUID
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
        chat_message_id: UUID,
        input_text: str,
        first_disease_id: UUID,
        first_score: float,
        second_disease_id: Optional[UUID] = None,
        second_score: Optional[float] = None,
        third_disease_id: Optional[UUID] = None,
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

    @staticmethod
    def get_disease_with_departments(
        db: Session, disease_id: UUID
    ) -> Optional[Tuple[Disease, List[Department]]]:
        """질환과 관련 진료과를 함께 조회"""
        disease = MedicalService.get_disease_by_id(db, disease_id)
        if not disease:
            return None

        departments = MedicalService.get_departments_by_disease(db, disease_id)
        return disease, departments

    @staticmethod
    def search_diseases_with_departments(
        db: Session, query: str, limit: int = 10
    ) -> List[Tuple[Disease, List[Department]]]:
        """질환 검색과 함께 관련 진료과 조회"""
        diseases = (
            db.query(Disease)
            .filter(Disease.name.ilike(f"%{query}%"))
            .limit(limit)
            .all()
        )

        results = []
        for disease in diseases:
            departments = MedicalService.get_departments_by_disease(db, disease.id)
            results.append((disease, departments))

        return results
