"""
의료 정보 관련 엔드포인트 - 리팩토링 버전
"""

import logging
from typing import Any, List, Optional

from app.api.deps import get_db
from app.schemas.medical import (
    DepartmentDetailResponse,
    DepartmentResponse,
    DiseaseDetailResponse,
    DiseaseResponse,
    EquipmentCategoryDetailResponse,
    EquipmentCategoryResponse,
    EquipmentSubcategoryDetailResponse,
    EquipmentSubcategoryResponse,
    HospitalDetailResponse,
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    HospitalRecommendationByDiseaseRequest,
    HospitalRecommendationByDiseaseResponse,
    HospitalResponse,
    MedicalEquipmentCategoryResponse,
    MedicalEquipmentSubcategoryResponse,
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
    search: Optional[str] = Query(None, description="질환 이름 검색어"),
) -> List[DiseaseResponse]:
    """
    질환 전체 조회

    - search: 질환 이름으로 검색 (선택)
    """
    try:
        if search:
            diseases = MedicalService.get_diseases_by_name(db, search)
        else:
            diseases = MedicalService.get_all_diseases(db)

        return [DiseaseResponse.from_orm(disease) for disease in diseases]

    except Exception as e:
        logger.error(f"Error fetching diseases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="질환 정보를 가져오는 중 오류가 발생했습니다.",
        )


@router.get("/diseases/{disease_id}", response_model=DiseaseDetailResponse)
def get_disease_detail(
    *,
    db: Session = Depends(get_db),
    disease_id: int,
) -> Any:
    """
    질환 상세 조회 (진료과 정보 포함)

    - disease_id: 질환의 ID (정수)
    """
    try:
        disease_detail = MedicalService.get_disease_detail_by_id(db, disease_id)

        if not disease_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="질환을 찾을 수 없습니다."
            )

        return DiseaseDetailResponse(**disease_detail)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid parameter for disease detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 파라미터입니다.",
        )
    except ConnectionError as e:
        logger.error(f"Database connection error for disease detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="데이터베이스 연결에 문제가 있습니다.",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error fetching disease detail: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


# ===== 진료과 관련 엔드포인트 =====


@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(
    *,
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="진료과 이름 검색어"),
) -> List[DepartmentResponse]:
    """
    진료과 전체 조회

    - search: 진료과 이름으로 검색 (선택)
    """
    try:
        if search:
            departments = MedicalService.get_departments_by_name(db, search)
        else:
            departments = MedicalService.get_all_departments(db)

        return [DepartmentResponse.from_orm(dept) for dept in departments]

    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="진료과 정보를 가져오는 중 오류가 발생했습니다.",
        )


@router.get("/departments/{department_id}", response_model=DepartmentDetailResponse)
def get_department_detail(
    *,
    db: Session = Depends(get_db),
    department_id: int,
) -> Any:
    """
    진료과 상세 조회 (해당 질환, 해당 병원 포함)

    - department_id: 진료과의 ID (정수)
    """
    try:
        result = MedicalService.get_department_detail_by_id(db, department_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="진료과를 찾을 수 없습니다.",
            )

        return DepartmentDetailResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid parameter for department detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 파라미터입니다.",
        )
    except ConnectionError as e:
        logger.error(f"Database connection error for department detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="데이터베이스 연결에 문제가 있습니다.",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error fetching department detail: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


# ===== 병원 관련 엔드포인트 =====


@router.get("/hospitals", response_model=List[HospitalResponse])
def get_hospitals(
    *,
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="병원 이름 검색어"),
    department_id: Optional[int] = Query(None, description="진료과 ID로 필터링"),
    disease_id: Optional[int] = Query(None, description="질환 ID로 필터링"),
) -> List[HospitalResponse]:
    """
    병원 전체 조회 (다중 필터링 지원)

    - search: 병원 이름으로 검색 (선택)
    - department_id: 특정 진료과의 병원만 조회 (선택)
    - disease_id: 특정 질환 치료 가능한 병원만 조회 (선택)
    """
    try:
        hospitals = MedicalService.get_hospitals_with_filters(
            db=db,
            search=search,
            department_id=department_id,
            disease_id=disease_id,
        )

        return [HospitalResponse.from_orm(hospital) for hospital in hospitals]

    except Exception as e:
        logger.error(f"Error fetching hospitals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="병원 정보를 가져오는 중 오류가 발생했습니다.",
        )


@router.get("/hospitals/{hospital_id}", response_model=HospitalDetailResponse)
def get_hospital_detail(
    *,
    db: Session = Depends(get_db),
    hospital_id: int,
) -> Any:
    """
    병원 상세 조회 (모든 테이블 정보 포함)

    - hospital_id: 병원의 ID (정수)
    """
    try:
        result = MedicalService.get_hospital_detail_by_id(db, hospital_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="병원을 찾을 수 없습니다."
            )

        return HospitalDetailResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid parameter for hospital detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 파라미터입니다.",
        )
    except ConnectionError as e:
        logger.error(f"Database connection error for hospital detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="데이터베이스 연결에 문제가 있습니다.",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error fetching hospital detail: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


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
            user_id=request_data.user_id,
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

        # 사용자 정보 조회
        from uuid import UUID

        user_uuid = UUID(request_data.user_id)
        from app.models.user import User

        user = db.query(User).filter(User.id == user_uuid).first()

        return {
            "inference_result_id": request_data.inference_result_id,
            "chat_room_id": request_data.chat_room_id,
            "user_id": request_data.user_id,
            "user_nickname": user.nickname if user else "",
            "user_location": user.road_address if user and user.road_address else "",
            "final_disease": {
                "id": final_disease.id,
                "name": final_disease.name,
                "description": final_disease.description,
                "created_at": final_disease.created_at,
            },
            "total_candidates": len(recommended_hospitals),
            "recommendations": recommended_hospitals,
            "search_criteria": {
                "max_distance": request_data.max_distance,
                "limit": request_data.limit,
            },
        }

    except ValueError as e:
        logger.warning(f"Invalid parameter in hospital recommendation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 파라미터입니다.",
        )
    except LookupError as e:
        logger.warning(f"Resource not found in hospital recommendation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="요청한 리소스를 찾을 수 없습니다.",
        )
    except ConnectionError as e:
        logger.error(f"Database connection error in hospital recommendation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="데이터베이스 연결에 문제가 있습니다.",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in hospital recommendation: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


# ===== 장비 관련 API 엔드포인트 =====


@router.post("/recommend-by-disease", response_model=HospitalRecommendationByDiseaseResponse)
def recommend_by_disease(
    *,
    db: Session = Depends(get_db),
    request_data: HospitalRecommendationByDiseaseRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    질환명 + 사용자 위치 기반의 라이트 병원 추천

    - inference_result_id 없이도 추천 가능하도록 설계
    - 병원 추천 결과는 DB에 저장하지 않고 계산 결과만 응답
    """
    try:
        # 사용자 조회 및 위치 확인 (토큰 기반)
        from app.models.user import User

        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or user.latitude is None or user.longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 위치 정보가 없습니다.",
            )

        # 질환명 → 질환 레코드 조회
        from app.models.medical import Disease

        disease = (
            db.query(Disease)
            .filter(Disease.name.ilike(f"%{request_data.disease_name}%"))
            .first()
        )
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 질환을 찾을 수 없습니다.",
            )

        # 후보 병원 조회(진료과/거리 기준)
        candidates = HospitalRecommendationService.get_hospitals_by_disease_and_location(
            db,
            int(disease.id),
            float(user.latitude),
            float(user.longitude),
            float(request_data.max_distance or 20.0),
        )

        # 필수 장비/병원 보유 장비 기반 점수 계산
        required_equipment = HospitalRecommendationService.get_required_equipment_for_disease(
            db, int(disease.id)
        )

        scored = []
        for h in candidates:
            he = HospitalRecommendationService.get_hospital_equipment(db, h.id)
            score, reason = HospitalRecommendationService.calculate_recommendation_score(
                getattr(h, "_calculated_distance", 0.0), required_equipment, he
            )
            scored.append(
                {
                    "hospital": h,
                    "score": score,
                    "reason": reason,
                    "distance": getattr(h, "_calculated_distance", 0.0),
                    "department_match": True,
                    "equipment_match": (
                        len(set(required_equipment) & set(he)) > 0 if required_equipment else True
                    ),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[: int(request_data.limit or 3)]

        recommendations = []
        for rank, item in enumerate(top, 1):
            h = item["hospital"]
            recommendations.append(
                {
                    "id": h.id,
                    "name": h.name,
                    "address": h.address,
                    "hospital_type_name": h.hospital_type_name,
                    "phone": h.phone,
                    "distance": item["distance"],
                    "rank": rank,
                    "recommendation_score": item["score"],
                    "department_match": item["department_match"],
                    "equipment_match": item["equipment_match"],
                    "recommended_reason": item["reason"],
                }
            )

        return {
            "chat_room_id": request_data.chat_room_id,
            "user_id": str(current_user.id),
            "user_nickname": user.nickname or "",
            "user_location": user.road_address or "",
            "final_disease": {
                "id": int(disease.id),
                "name": disease.name,
                "description": getattr(disease, "description", ""),
                "created_at": getattr(disease, "created_at", None),
            },
            "total_candidates": len(candidates),
            "recommendations": recommendations,
            "search_criteria": {
                "max_distance": request_data.max_distance or 20.0,
                "limit": request_data.limit or 3,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"recommend-by-disease error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="병원 추천 처리 중 오류가 발생했습니다.",
        )


@router.get("/equipment/categories", response_model=List[EquipmentCategoryResponse])
def get_equipment_categories(db: Session = Depends(get_db)):
    """
    장비 대분류 전체 조회

    Returns:
        List[EquipmentCategoryResponse]: 장비 대분류 목록
    """
    try:
        categories = MedicalService.get_all_equipment_categories(db)
        return [EquipmentCategoryResponse.from_orm(category) for category in categories]

    except Exception as exc:
        logger.error("장비 대분류 조회 중 오류 발생", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="장비 대분류 조회 중 오류가 발생했습니다.",
        )


@router.get(
    "/equipment/subcategories", response_model=List[EquipmentSubcategoryResponse]
)
def get_equipment_subcategories(db: Session = Depends(get_db)):
    """
    장비 세분류 전체 조회

    Returns:
        List[EquipmentSubcategoryResponse]: 장비 세분류 목록
    """
    try:
        subcategories = MedicalService.get_all_equipment_subcategories(db)
        return [
            EquipmentSubcategoryResponse.from_orm(subcategory)
            for subcategory in subcategories
        ]

    except Exception as exc:
        logger.error("장비 세분류 조회 중 오류 발생", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="장비 세분류 조회 중 오류가 발생했습니다.",
        )


@router.get(
    "/equipment/categories/{category_id}",
    response_model=EquipmentCategoryDetailResponse,
)
def get_equipment_category_detail(category_id: int, db: Session = Depends(get_db)):
    """
    장비 대분류 상세 조회

    Args:
        category_id: 장비 대분류 ID

    Returns:
        EquipmentCategoryDetailResponse: 장비 대분류 상세 정보 (세분류 포함)
    """
    try:
        category = MedicalService.get_equipment_category_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 장비 대분류를 찾을 수 없습니다.",
            )

        return EquipmentCategoryDetailResponse.from_orm(category)

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 장비 대분류 ID입니다.",
        )
    except Exception as exc:
        logger.error(
            f"장비 대분류 상세 조회 중 오류 발생 (ID: {category_id})", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="장비 대분류 상세 조회 중 오류가 발생했습니다.",
        )


@router.get(
    "/equipment/subcategories/{subcategory_id}",
    response_model=EquipmentSubcategoryDetailResponse,
)
def get_equipment_subcategory_detail(
    subcategory_id: str, db: Session = Depends(get_db)
):
    """
    장비 세분류 상세 조회

    Args:
        subcategory_id: 장비 세분류 ID

    Returns:
        EquipmentSubcategoryDetailResponse: 장비 세분류 상세 정보 (병원 정보 포함)
    """
    try:
        # 문자열을 정수로 변환
        try:
            subcategory_id_int = int(subcategory_id)
        except ValueError:
            raise ValueError(f"ID '{subcategory_id}'는 유효한 정수가 아닙니다")

        subcategory = MedicalService.get_equipment_subcategory_by_id(
            db, subcategory_id_int
        )
        if not subcategory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 장비 세분류를 찾을 수 없습니다.",
            )

        # 병원 정보 조회
        hospitals = MedicalService.get_hospitals_by_equipment_subcategory(
            db, subcategory_id_int
        )

        # 수량 계산
        total_quantity = sum(
            equipment.quantity
            for equipment in subcategory.hospital_equipment
            if equipment.deleted_at is None
        )

        # 응답 데이터 구성
        response_data = {
            "id": subcategory.id,
            "category_id": subcategory.category_id,
            "name": subcategory.name,
            "code": subcategory.code,
            "created_at": subcategory.created_at,
            "updated_at": subcategory.updated_at,
            "category": {
                "id": subcategory.category.id,
                "name": subcategory.category.name,
                "code": subcategory.category.code,
                "created_at": subcategory.category.created_at,
            },
            "quantity": total_quantity,
            "hospitals": [
                {"id": hospital.id, "name": hospital.name} for hospital in hospitals
            ],
        }

        
        return response_data

    except HTTPException:
        raise
    except ValueError as e:
        print(f"DEBUG ValueError: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 장비 세분류 ID입니다: {str(e)}",
        )
    except Exception as exc:
        logger.error(
            f"장비 세분류 상세 조회 중 오류 발생 (ID: {subcategory_id})", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="장비 세분류 상세 조회 중 오류가 발생했습니다.",
        )
