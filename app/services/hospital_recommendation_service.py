"""
병원 추천 서비스 로직
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Union

from app.models.department import Department, DepartmentDisease, HospitalDepartment
from app.models.disease_equipment import DiseaseEquipmentCategory
from app.models.equipment import MedicalEquipmentCategory
from app.models.hospital import Hospital, HospitalEquipment, HospitalRecommendation
from app.models.medical import Disease
from app.models.model_inference import ModelInferenceResult
from app.models.user import User
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class HospitalRecommendationService:
    """병원 추천 비즈니스 로직"""

    # 병원 종별 우선순위 (상급종합병원/요양병원/치과 계열 제외)
    HOSPITAL_TYPE_EXCLUDE = {"상급종합병원", "요양병원", "치과의원", "치과병원"}
    HOSPITAL_TYPE_PRIORITY = {
        # 높은 우선순위일수록 큰 값
        "의원": 5,
        "병원": 5,
        "보건지소": 4,
        "보건소": 4,
        "종합병원": 3,
        "한의원": 1,
        "한방병원": 1,
        # 제외 대상은 별도 처리
    }

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
        distance_km: float,
        required_equipment: List[str],
        hospital_equipment: List[str],
        specialist_count: int = 0,
        hospital_type_name: Optional[str] = None,
        max_distance_km: float = 5.0,
    ) -> Tuple[float, str, float, Dict[str, Union[int, float, str]]]:
        """
        병원 추천 점수 계산

        Args:
            distance_km: 사용자로부터의 거리 (km)
            required_equipment: 질환별 필수장비 리스트
            hospital_equipment: 병원 보유장비 리스트

        Returns:
            Tuple[float, str]: (점수, 설명)
        """

        # 가중치 설정: 필수 장비 없으면 (장비 30 / 전문의 40 / 거리 30), 있으면 (장비 50 / 전문의 30 / 거리 20)
        if required_equipment:
            W_EQUIP, W_SPEC, W_DIST = 50.0, 30.0, 20.0
        else:
            W_EQUIP, W_SPEC, W_DIST = 30.0, 40.0, 30.0

        # 1. 장비 점수 계산 (가중치 W_EQUIP)
        matched_count = 0
        total_required = len(required_equipment or [])
        matched_names: List[str] = []
        if required_equipment:
            # 필수장비가 있는 경우: 보유율 계산
            matched_equipment = set(required_equipment) & set(hospital_equipment)
            matched_count = len(matched_equipment)
            matched_names = sorted(list(matched_equipment))
            equipment_score = (
                matched_count / max(1, len(required_equipment))
            ) * W_EQUIP
            equipment_reason = (
                f"필수장비 {matched_count}/{len(required_equipment)} 보유"
            )
        else:
            # 필수장비가 없는 경우: 보유장비 수로 점수 (과도한 영향 방지)
            equipment_count = len(hospital_equipment)
            per_item = max(W_EQUIP / 12.0, 2.0)  # 대략 12개에서 상한 도달, 최소 2점
            equipment_score = min(equipment_count * per_item, W_EQUIP)
            equipment_reason = f"장비 {equipment_count}개"

        # 2. 전문의 수 점수 (가중치 W_SPEC)
        try:
            sc_val = int(specialist_count) if specialist_count is not None else 0
        except Exception:
            sc_val = 0
        specialist_score = min(max(sc_val, 0), 100)
        # log1p 근사: 루트 기반 완만 상승 (전문의 9명≈30점 상한에 맞춤)
        specialist_score = min((specialist_score**0.5) * (W_SPEC / 3.0), W_SPEC)

        # 3. 거리 점수 계산 (가중치 W_DIST)
        R = max_distance_km if max_distance_km and max_distance_km > 0 else 5.0
        distance_score = max(0.0, (R - distance_km) / R) * W_DIST

        base_score = equipment_score + specialist_score + distance_score

        # 4. 병원 종별 우선순위 보너스 (소폭)
        priority = 0
        if hospital_type_name:
            priority = HospitalRecommendationService.HOSPITAL_TYPE_PRIORITY.get(
                hospital_type_name, 2
            )
        priority_bonus = (priority - 2) * 0.5  # 최대 +1.5점 수준

        final_score = base_score + priority_bonus
        full_reason = (
            f"{equipment_reason}, 전문의수 {sc_val}명, 거리 {distance_km:.1f}km"
        )

        # 상세 로그 (디버그)
        logger.debug(
            {
                "tag": "recommend_score_components",
                "distance_km": round(distance_km, 3),
                "weights": {"equip": W_EQUIP, "spec": W_SPEC, "dist": W_DIST},
                "equipment_reason": equipment_reason,
                "specialist_count": specialist_count,
                "hospital_type": hospital_type_name,
                "scores": {
                    "equipment": round(equipment_score, 3),
                    "specialist": round(specialist_score, 3),
                    "distance": round(distance_score, 3),
                    "priority_bonus": round(priority_bonus, 3),
                    "final": round(final_score, 3),
                },
            }
        )
        breakdown = {
            "weights": {"equip": W_EQUIP, "spec": W_SPEC, "dist": W_DIST},
            "equipment_score": round(equipment_score, 3),
            "specialist_score": round(specialist_score, 3),
            "distance_score": round(distance_score, 3),
            "priority_bonus": round(priority_bonus, 3),
            "final_score": round(final_score, 3),
            "matched_equipment_count": matched_count,
            "total_required_equipment": total_required,
        }
        return final_score, full_reason, priority, breakdown

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
        names = (
            db.query(DiseaseEquipmentCategory.equipment_category_name)
            .filter(DiseaseEquipmentCategory.disease_id == int(disease_id))
            .all()
        )
        return [n[0] for n in names]

    @staticmethod
    def get_hospital_equipment(db: Session, hospital_id: int) -> List[str]:
        """
        병원 보유 장비 목록 조회 (대분류 기준)

        Args:
            db: 데이터베이스 세션
            hospital_id: 병원 ID

        Returns:
            List[str]: 보유장비명 리스트 (대분류)
        """
        equipment_list = (
            db.query(HospitalEquipment.equipment_category_name)
            .filter(
                and_(
                    HospitalEquipment.hospital_id == hospital_id,
                    HospitalEquipment.deleted_at.is_(None),
                )
            )
            .all()
        )

        return [equipment[0] for equipment in equipment_list if equipment[0]]

    @staticmethod
    def get_hospitals_by_disease_and_location(
        db: Session,
        disease_id: int,
        user_latitude: float,
        user_longitude: float,
        max_distance_km: float = 5.0,
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

        # 2단계: 진료과 보유 병원 조회 (JSON 컬럼 DISTINCT 이슈 회피)
        hospital_id_rows = (
            db.query(Hospital.id)
            .join(HospitalDepartment)
            .filter(HospitalDepartment.department_id.in_(department_ids))
            .filter(
                ~Hospital.hospital_type_name.in_(
                    HospitalRecommendationService.HOSPITAL_TYPE_EXCLUDE
                )
            )
            .distinct()
            .all()
        )
        hospital_ids = [r[0] for r in hospital_id_rows]
        if not hospital_ids:
            return []

        hospitals_with_departments = (
            db.query(Hospital)
            .filter(Hospital.id.in_(hospital_ids))
            .options(joinedload(Hospital.equipment))
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
        from uuid import UUID

        user_id_uuid = UUID(user_id)
        user = db.query(User).filter(User.id == user_id_uuid).first()
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

        # 5. 필수장비 목록 조회 (대분류 기준, 공란은 없음 처리)
        required_equipment = (
            HospitalRecommendationService.get_required_equipment_for_disease(
                db, final_disease_id
            )
        )

        # 5-1. 가중치 선택(로그용 미리 계산)
        if required_equipment:
            w_preview = {"equip": 50.0, "spec": 30.0, "dist": 20.0}
        else:
            w_preview = {"equip": 30.0, "spec": 40.0, "dist": 30.0}
        logger.info(
            {
                "tag": "recommend_context",
                "disease_id": final_disease_id,
                "radius_km": max_distance_km,
                "required_equipment": required_equipment,
                "weights": w_preview,
                "candidates": len(candidate_hospitals),
            }
        )

        # 6. 각 병원에 대해 점수 계산
        scored_hospitals = []
        for hospital in candidate_hospitals:
            # 병원 보유 장비 조회
            hospital_equipment = HospitalRecommendationService.get_hospital_equipment(
                db, hospital.id
            )

            # 병원 전문의 수(질환 관련 진료과 합) 계산
            specialist_count = HospitalRecommendationService.get_specialist_count_for_hospital_and_disease(
                db, hospital.id, final_disease_id
            )

            # 점수 계산
            score, reason, priority, breakdown = (
                HospitalRecommendationService.calculate_recommendation_score(
                    hospital._calculated_distance,
                    required_equipment,
                    hospital_equipment,
                    specialist_count,
                    hospital.hospital_type_name,
                    max_distance_km,
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
                    "priority": priority,
                    "specialist_count": specialist_count,
                    "score_breakdown": breakdown,
                }
            )

        # 7. 점수 + 우선순위 정렬 후 상위 병원 선택
        scored_hospitals.sort(
            key=lambda x: (x["score"], x.get("priority", 0)), reverse=True
        )

        # limit이 None이거나 0 이하일 경우 모든 병원 반환
        if limit is None or limit <= 0:
            top_hospitals = scored_hospitals
        else:
            top_hospitals = scored_hospitals[:limit]

        # 8. HospitalRecommendation 객체 생성
        recommendations = []
        for rank, hospital_data in enumerate(top_hospitals, 1):
            recommendation = HospitalRecommendation(
                inference_result_id=inference_result_id,
                hospital_id=hospital_data["hospital"].id,
                user_id=user_id_uuid,
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

    @staticmethod
    def get_specialist_count_for_hospital_and_disease(
        db: Session, hospital_id: int, disease_id: int
    ) -> int:
        """해당 질환과 매핑된 진료과에 대해 병원-진료과 specialist_count 합계를 반환."""
        dept_ids = (
            db.query(DepartmentDisease.department_id)
            .filter(DepartmentDisease.disease_id == disease_id)
            .all()
        )
        dept_id_list = [row[0] for row in dept_ids]
        if not dept_id_list:
            return 0
        total = (
            db.query(func.coalesce(func.sum(HospitalDepartment.specialist_count), 0))
            .filter(
                HospitalDepartment.hospital_id == hospital_id,
                HospitalDepartment.department_id.in_(dept_id_list),
            )
            .scalar()
        )
        try:
            return int(total or 0)
        except Exception:
            return 0

    @staticmethod
    def get_equipment_details_for_hospital(
        db: Session, hospital_id: int, required_equipment_names: List[str]
    ) -> List[Dict[str, Union[str, int]]]:
        """병원이 보유한 '필수 장비(대분류)'에 대한 상세 목록(이름/코드/수량)을 반환.
        required_equipment_names가 비어있으면 빈 리스트 반환.
        """
        if not required_equipment_names:
            return []
        rows = (
            db.query(
                HospitalEquipment.equipment_category_name,
                HospitalEquipment.equipment_category_code,
                func.coalesce(func.sum(HospitalEquipment.quantity), 0).label("qty"),
            )
            .filter(
                HospitalEquipment.hospital_id == hospital_id,
                HospitalEquipment.deleted_at.is_(None),
                HospitalEquipment.equipment_category_name.in_(required_equipment_names),
            )
            .group_by(
                HospitalEquipment.equipment_category_name,
                HospitalEquipment.equipment_category_code,
            )
            .all()
        )
        return [
            {
                "name": name,
                "code": code,
                "quantity": int(qty or 0),
            }
            for (name, code, qty) in rows
        ]
