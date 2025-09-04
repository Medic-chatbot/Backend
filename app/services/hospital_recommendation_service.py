"""
병원 추천 서비스 로직
"""

import logging
import math
from typing import List, Optional, Tuple

from app.models.department import Department, DepartmentDisease, HospitalDepartment
from app.models.equipment import EquipmentDisease, MedicalEquipmentSubcategory
from app.models.hospital import Hospital, HospitalEquipment, HospitalRecommendation
from app.models.medical import Disease
from app.models.model_inference import ModelInferenceResult
from app.models.user import User
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class HospitalRecommendationService:
    """병원 추천 비즈니스 로직"""

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        하버사인 공식을 사용한 두 지점 간 거리 계산 (km)

        Args:
            lat1, lon1: 첫 번째 지점의 위도, 경도
            lat2, lon2: 두 번째 지점의 위도, 경도

        Returns:
            float: 거리 (km)
        """
        # 지구 반지름 (km)
        R = 6371.0

        # 라디안으로 변환
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 위도, 경도 차이
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # 하버사인 공식
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    @staticmethod
    def calculate_recommendation_score(
        distance_km: float, required_equipment: List[str], hospital_equipment: List[str]
    ) -> Tuple[float, str]:
        """
        병원 추천 점수 계산

        Args:
            distance_km: 사용자로부터의 거리 (km)
            required_equipment: 질환별 필수장비 리스트
            hospital_equipment: 병원 보유장비 리스트

        Returns:
            Tuple[float, str]: (점수, 설명)
        """

        # 1. 장비 점수 계산 (70점)
        if required_equipment:
            # 필수장비가 있는 경우: 보유율 계산
            matched_equipment = set(required_equipment) & set(hospital_equipment)
            equipment_score = (len(matched_equipment) / len(required_equipment)) * 70
            equipment_reason = (
                f"필수장비 {len(matched_equipment)}/{len(required_equipment)} 보유"
            )
        else:
            # 필수장비가 없는 경우: 보유장비 수로 점수
            equipment_count = len(hospital_equipment)
            equipment_score = min(equipment_count * 5, 70)  # 장비 1개당 5점, 최대 70점
            equipment_reason = f"장비 {equipment_count}개 보유"

        # 2. 거리 점수 계산 (30점)
        # 20km 이내에서 가까울수록 높은 점수
        distance_score = max(0, (20 - distance_km) / 20) * 30

        # 3. 최종 점수
        final_score = equipment_score + distance_score
        full_reason = f"{equipment_reason}, 거리 {distance_km:.1f}km"

        return final_score, full_reason

    @staticmethod
    def get_required_equipment_for_disease(db: Session, disease_id: int) -> List[str]:
        """
        질환에 필요한 필수장비 목록 조회

        Args:
            db: 데이터베이스 세션
            disease_id: 질환 ID

        Returns:
            List[str]: 필수장비명 리스트
        """
        equipment_list = (
            db.query(MedicalEquipmentSubcategory.name)
            .join(EquipmentDisease)
            .filter(EquipmentDisease.disease_id == disease_id)
            .all()
        )

        return [equipment[0] for equipment in equipment_list]

    @staticmethod
    def get_hospital_equipment(db: Session, hospital_id: int) -> List[str]:
        """
        병원 보유 장비 목록 조회

        Args:
            db: 데이터베이스 세션
            hospital_id: 병원 ID

        Returns:
            List[str]: 보유장비명 리스트
        """
        equipment_list = (
            db.query(MedicalEquipmentSubcategory.name)
            .join(HospitalEquipment)
            .filter(
                and_(
                    HospitalEquipment.hospital_id == hospital_id,
                    HospitalEquipment.is_operational == True,
                )
            )
            .all()
        )

        return [equipment[0] for equipment in equipment_list]

    @staticmethod
    def get_hospitals_by_disease_and_location(
        db: Session,
        disease_id: int,
        user_latitude: float,
        user_longitude: float,
        max_distance_km: float = 20.0,
    ) -> List[Hospital]:
        """
        질환과 위치를 기준으로 병원 필터링

        Args:
            db: 데이터베이스 세션
            disease_id: 질환 ID
            user_latitude: 사용자 위도
            user_longitude: 사용자 경도
            max_distance_km: 최대 검색 거리 (km)

        Returns:
            List[Hospital]: 필터링된 병원 리스트
        """

        # 1단계: 질환 → 진료과 매핑
        department_ids = (
            db.query(DepartmentDisease.department_id)
            .filter(DepartmentDisease.disease_id == disease_id)
            .subquery()
        )

        # 2단계: 진료과 보유 병원 조회
        hospitals_with_departments = (
            db.query(Hospital)
            .join(HospitalDepartment)
            .filter(HospitalDepartment.department_id.in_(department_ids))
            .options(joinedload(Hospital.equipment))
            .distinct()
            .all()
        )

        # 3단계: 거리 기준 필터링
        nearby_hospitals = []
        for hospital in hospitals_with_departments:
            distance = HospitalRecommendationService.calculate_distance(
                user_latitude, user_longitude, hospital.latitude, hospital.longitude
            )

            if distance <= max_distance_km:
                # 병원 객체에 거리 정보 추가 (임시)
                hospital._calculated_distance = distance
                nearby_hospitals.append(hospital)

        logger.info(
            f"Disease {disease_id}: Found {len(nearby_hospitals)} hospitals within {max_distance_km}km"
        )

        return nearby_hospitals

    @staticmethod
    def recommend_hospitals(
        db: Session,
        inference_result_id: int,
        user_id: str,  # UUID string으로 유지
        max_distance_km: float = 20.0,
        limit: int = 3,
    ) -> List[HospitalRecommendation]:
        """
        병원 추천 메인 로직

        Args:
            db: 데이터베이스 세션
            inference_result_id: 모델 추론 결과 ID
            user_id: 사용자 ID
            max_distance_km: 최대 검색 거리 (km)
            limit: 추천 병원 수

        Returns:
            List[HospitalRecommendation]: 추천 병원 리스트
        """

        # 1. 모델 추론 결과 조회
        inference_result = (
            db.query(ModelInferenceResult)
            .filter(ModelInferenceResult.id == inference_result_id)
            .first()
        )
        if not inference_result:
            raise ValueError(f"Inference result not found: {inference_result_id}")

        # 2. 사용자 위치 정보 조회
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.latitude or not user.longitude:
            raise ValueError(f"User location not found: {user_id}")

        # 3. 1순위 질환 확정
        final_disease_id = inference_result.first_disease_id
        if not final_disease_id:
            raise ValueError("No primary disease found in inference result")

        logger.info(f"Recommending hospitals for disease {final_disease_id}")

        # 4. 해당 질환과 위치 기준으로 병원 필터링
        candidate_hospitals = (
            HospitalRecommendationService.get_hospitals_by_disease_and_location(
                db, final_disease_id, user.latitude, user.longitude, max_distance_km
            )
        )

        if not candidate_hospitals:
            logger.warning("No hospitals found matching criteria")
            return []

        # 5. 필수장비 목록 조회
        required_equipment = (
            HospitalRecommendationService.get_required_equipment_for_disease(
                db, final_disease_id
            )
        )

        # 6. 각 병원에 대해 점수 계산
        scored_hospitals = []
        for hospital in candidate_hospitals:
            # 병원 보유 장비 조회
            hospital_equipment = HospitalRecommendationService.get_hospital_equipment(
                db, hospital.id
            )

            # 점수 계산
            score, reason = (
                HospitalRecommendationService.calculate_recommendation_score(
                    hospital._calculated_distance,
                    required_equipment,
                    hospital_equipment,
                )
            )

            scored_hospitals.append(
                {
                    "hospital": hospital,
                    "score": score,
                    "reason": reason,
                    "distance": hospital._calculated_distance,
                    "department_match": True,  # 이미 진료과 필터링을 통과함
                    "equipment_match": (
                        len(set(required_equipment) & set(hospital_equipment)) > 0
                        if required_equipment
                        else True
                    ),
                }
            )

        # 7. 점수 순으로 정렬 후 상위 병원 선택
        scored_hospitals.sort(key=lambda x: x["score"], reverse=True)
        top_hospitals = scored_hospitals[:limit]

        # 8. HospitalRecommendation 객체 생성
        recommendations = []
        for rank, hospital_data in enumerate(top_hospitals, 1):
            recommendation = HospitalRecommendation(
                inference_result_id=inference_result_id,
                hospital_id=hospital_data["hospital"].id,
                user_id=user_id,
                distance=hospital_data["distance"],
                rank=rank,
                recommendation_score=hospital_data["score"],
                department_match=hospital_data["department_match"],
                equipment_match=hospital_data["equipment_match"],
                recommended_reason=hospital_data["reason"],
            )

            db.add(recommendation)
            recommendations.append(recommendation)

        # 9. 데이터베이스 저장
        db.commit()

        # 10. 관계 데이터 로드
        for rec in recommendations:
            db.refresh(rec)

        logger.info(f"Created {len(recommendations)} hospital recommendations")
        return recommendations
