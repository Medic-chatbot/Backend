"""
의료 정보 관련 엔드포인트
"""

import logging
from typing import Any, List
from uuid import UUID

from app.api.deps import get_db
from app.schemas.medical import (
    DepartmentResponse,
    DiseaseResponse,
    DiseaseWithDepartmentsResponse,
    EquipmentDiseaseResponse,
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    MedicalEquipmentSubcategoryResponse,
    RecommendedHospitalResponse,
)
from app.services.hospital_recommendation_service import HospitalRecommendationService
from app.services.medical_service import MedicalService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== 질환 관련 엔드포인트 =====


@router.get("/diseases", response_model=List[DiseaseResponse])
def get_diseases(
    *,
    db: Session = Depends(get_db),
    q: str = Query(None, description="질환 이름 검색어"),
    limit: int = Query(100, description="최대 조회 수"),
) -> Any:
    """질환 목록 조회 (검색 가능)"""
    try:
        if q:
            diseases = MedicalService.get_diseases_by_name(db, q)
        else:
            diseases = MedicalService.get_all_diseases(db, limit)

        return diseases

    except Exception as e:
        logger.error(f"Error fetching diseases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="질환 정보를 가져오는 중 오류가 발생했습니다.",
        )


@router.get("/diseases/{disease_id}", response_model=DiseaseResponse)
def get_disease(
    *,
    db: Session = Depends(get_db),
    disease_id: UUID,
) -> Any:
    """특정 질환 정보 조회"""
    disease = MedicalService.get_disease_by_id(db, disease_id)

    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="질환을 찾을 수 없습니다."
        )

    return disease


@router.get(
    "/diseases/{disease_id}/departments", response_model=List[DepartmentResponse]
)
def get_disease_departments(
    *,
    db: Session = Depends(get_db),
    disease_id: UUID,
) -> Any:
    """질환과 관련된 진료과 목록 조회"""
    # 질환 존재 여부 확인
    disease = MedicalService.get_disease_by_id(db, disease_id)
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="질환을 찾을 수 없습니다."
        )

    departments = MedicalService.get_departments_by_disease(db, disease_id)
    return departments


@router.get(
    "/diseases/{disease_id}/equipment",
    response_model=List[MedicalEquipmentSubcategoryResponse],
)
def get_disease_equipment(
    *,
    db: Session = Depends(get_db),
    disease_id: UUID,
) -> Any:
    """질환과 관련된 의료장비 목록 조회"""
    # 질환 존재 여부 확인
    disease = MedicalService.get_disease_by_id(db, disease_id)
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="질환을 찾을 수 없습니다."
        )

    equipment = MedicalService.get_equipment_by_disease(db, disease_id)
    return equipment


# 진료과 관련 엔드포인트는 질환 조회 시 함께 제공되므로 별도 구현하지 않음


# ===== 통합 검색 엔드포인트 =====


@router.get("/search/diseases", response_model=List[DiseaseWithDepartmentsResponse])
def search_diseases_with_departments(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., description="질환 검색어"),
    limit: int = Query(10, description="최대 조회 수"),
) -> Any:
    """질환 검색 (관련 진료과 포함)"""
    try:
        results = MedicalService.search_diseases_with_departments(db, q, limit)

        response_data = []
        for disease, departments in results:
            response_data.append({"disease": disease, "departments": departments})

        return response_data

    except Exception as e:
        logger.error(f"Error searching diseases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="질환 검색 중 오류가 발생했습니다.",
        )


@router.get(
    "/diseases/{disease_id}/complete", response_model=DiseaseWithDepartmentsResponse
)
def get_disease_complete_info(
    *,
    db: Session = Depends(get_db),
    disease_id: UUID,
) -> Any:
    """질환의 완전한 정보 조회 (진료과 포함)"""
    result = MedicalService.get_disease_with_departments(db, disease_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="질환을 찾을 수 없습니다."
        )

    disease, departments = result
    return {"disease": disease, "departments": departments}


# ===== 병원 추천 엔드포인트 =====


@router.post("/recommend-hospitals", response_model=HospitalRecommendationResponse)
def recommend_hospitals(
    *,
    db: Session = Depends(get_db),
    request_data: HospitalRecommendationRequest,
) -> Any:
    """
    모델 추론 결과를 기반으로 병원 추천

    **플로우:**
    1. 모델 추론 결과에서 1순위 질환 확정
    2. 질환 → 진료과 매핑
    3. 사용자 위치 기반 반경 검색
    4. 진료과 보유 병원 필터링
    5. 장비 보유 여부 + 거리 기반 점수 계산
    6. Top 3 병원 추천
    """
    try:
        # 병원 추천 로직 실행
        recommendations = HospitalRecommendationService.recommend_hospitals(
            db=db,
            inference_result_id=request_data.inference_result_id,
            user_id=request_data.user_id,  # 실제로는 JWT에서 가져와야 함
            max_distance_km=request_data.max_distance,
            limit=request_data.limit,
        )

        if not recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="추천할 수 있는 병원을 찾을 수 없습니다.",
            )

        # 추가 정보 조회
        inference_result = recommendations[0].inference_result
        final_disease = MedicalService.get_disease_by_id(
            db, inference_result.first_disease_id
        )

        # 응답 데이터 구성
        recommended_hospitals = []
        for rec in recommendations:
            hospital_data = {
                "id": rec.hospital.id,
                "name": rec.hospital.name,
                "address": rec.hospital.address,
                "hospital_type_name": rec.hospital.hospital_type_name,
                "phone": rec.hospital.phone,
                "distance": rec.distance,
                "rank": rec.rank,
                "recommendation_score": rec.recommendation_score,
                "department_match": rec.department_match,
                "equipment_match": rec.equipment_match,
                "recommended_reason": rec.recommended_reason,
            }
            recommended_hospitals.append(hospital_data)

        return {
            "inference_result_id": request_data.inference_result_id,
            "user_id": recommendations[0].user_id,
            "final_disease": final_disease,
            "total_candidates": len(
                recommended_hospitals
            ),  # 임시: 실제로는 전체 후보 수 계산 필요
            "recommendations": recommended_hospitals,
            "search_criteria": {
                "max_distance": request_data.max_distance,
                "limit": request_data.limit,
            },
        }

    except ValueError as e:
        logger.error(f"Validation error in hospital recommendation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in hospital recommendation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="병원 추천 중 오류가 발생했습니다.",
        )
