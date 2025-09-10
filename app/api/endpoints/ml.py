"""
ML 서비스 관련 엔드포인트
"""

import logging
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.ml_service import ml_client
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()


class SymptomAnalysisRequest(BaseModel):
    """증상 분석 요청"""

    text: str
    chat_room_id: Optional[int] = None


class SymptomAnalysisResponse(BaseModel):
    """증상 분석 응답"""

    original_text: str
    processed_text: str
    disease_classifications: list
    top_disease: str
    confidence: float
    formatted_message: str


@router.post("/analyze-symptom", response_model=SymptomAnalysisResponse)
async def analyze_symptom(
    request: SymptomAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    증상 텍스트 분석 API 엔드포인트
    """
    try:
        # ML 서비스 호출
        ml_result = await ml_client.analyze_symptom(
            text=request.text,
            user_id=str(current_user.id),
            chat_room_id=request.chat_room_id,
        )

        if not ml_result:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML 서비스에 연결할 수 없습니다",
            )

        # 결과 포맷팅
        formatted_message = ml_client.format_disease_results(
            {"symptom_analysis": ml_result}
        )

        return SymptomAnalysisResponse(
            original_text=ml_result.get("original_text", request.text),
            processed_text=ml_result.get("processed_text", ""),
            disease_classifications=ml_result.get("disease_classifications", []),
            top_disease=ml_result.get("top_disease", "알 수 없음"),
            confidence=ml_result.get("confidence", 0.0),
            formatted_message=formatted_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"증상 분석 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="증상 분석 중 오류가 발생했습니다",
        )


@router.post("/full-analysis")
async def get_full_analysis(
    request: SymptomAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    전체 분석: 증상 분석 + 병원 추천
    """
    try:
        # ML 서비스 호출
        ml_result = await ml_client.get_full_analysis(
            text=request.text,
            user_id=str(current_user.id),
            chat_room_id=request.chat_room_id,
        )

        if not ml_result:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML 서비스에 연결할 수 없습니다",
            )

        return ml_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전체 분석 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전체 분석 중 오류가 발생했습니다",
        )


@router.get("/health")
async def ml_health_check():
    """
    ML 서비스 상태 확인
    """
    try:
        is_healthy = await ml_client.health_check()

        return {
            "ml_service_status": "healthy" if is_healthy else "unhealthy",
            "ml_service_url": ml_client.base_url,
        }

    except Exception as e:
        return {
            "ml_service_status": "error",
            "ml_service_url": ml_client.base_url,
            "error": str(e),
        }
