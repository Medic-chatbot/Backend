"""
ML 서비스 관련 엔드포인트
"""

import logging
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.ml_service import ml_client
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()


class SymptomAnalysisRequest(BaseModel):
    """증상 분석 요청"""

    text: str
    chat_room_id: Optional[int] = None
    use_context: bool = True  # 이전 메시지와 결합 여부 (기본값: True)
    start_new_session: bool = False  # 새로운 증상 세션 시작 여부 (기본값: False)


class SymptomAnalysisWithRetryRequest(BaseModel):
    """재질문 포함 증상 분석 요청"""

    text: str
    chat_room_id: int  # 필수
    max_retries: Optional[int] = 3  # 최대 재질문 횟수
    retry_message: Optional[str] = "더 자세한 증상을 설명해주세요."


class SymptomAnalysisResponse(BaseModel):
    """증상 분석 응답"""

    original_text: str
    processed_text: str
    disease_classifications: (
        list  # [{"disease_id": str, "label": str, "score": float}, ...]
    )
    top_disease: dict  # {"disease_id": str, "label": str, "score": float}
    user_id: str
    chat_room_id: Optional[int] = None
    inference_result_id: Optional[int] = None  # 병원 추천을 위해 추가
    confidence_threshold_met: Optional[bool] = None  # 임계치 달성 여부
    confidence_threshold: Optional[float] = None  # 현재 임계치 값


def clean_symptom_text(text: str) -> str:
    """
    프론트엔드에서 오염된 텍스트를 정리하는 함수

    제거할 패턴들:
    - 0_USER_, 1_USER_ 등의 prefix
    - "메시지를 받았습니다. 증상 분석을 위해 잠시만 기다려주세요."
    - "분석 중입니다..."
    - 기타 시스템 메시지들
    """
    import re

    if not text:
        return text

    # 패턴들을 정의
    patterns_to_remove = [
        r"\d+_USER_",  # 0_USER_, 1_USER_ 등
        r"메시지를 받았습니다\.?\s*증상 분석을 위해 잠시만 기다려주세요\.?",
        r"분석 중입니다\.{0,3}",
        r"증상 분석을 위해 잠시만 기다려주세요\.?",
        r"메시지를 받았습니다\.?",
        r"더 자세한 증상을 설명해주세요\.?",
    ]

    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)

    # 여러 공백을 하나로 정리하고 앞뒤 공백 제거
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text


@router.post("/analyze-symptom", response_model=SymptomAnalysisResponse)
async def analyze_symptom(
    request: SymptomAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(default=None),
):
    """
    증상 텍스트 분석 API 엔드포인트 (채팅과 연동)
    """
    try:
        # 채팅방이 지정된 경우 권한 확인
        if request.chat_room_id:
            from uuid import UUID

            from app.services.chat_service import ChatService

            user_uuid = UUID(str(current_user.id))
            chat_room = ChatService.get_chat_room(db, request.chat_room_id)
            if not chat_room or chat_room.user_id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="해당 채팅방에 접근할 권한이 없습니다.",
                )

        # 먼저 입력 텍스트를 정리
        cleaned_input_text = clean_symptom_text(request.text)

        # 채팅방이 지정된 경우 사용자 메시지 저장
        user_message = None
        if request.chat_room_id:
            from app.services.chat_service import ChatService

            # 사용자 메시지 저장 (텍스트 정리 후)
            user_message = ChatService.create_chat_message(
                db, request.chat_room_id, "USER", cleaned_input_text
            )

            # 새로운 세션 시작 요청 시 세션 포인터 업데이트
            if request.start_new_session:
                ChatService.start_new_symptom_session(
                    db, request.chat_room_id, user_message.id
                )

        # 분석할 텍스트 결정 (채팅방 컨텍스트 포함)
        analysis_text = cleaned_input_text

        if request.chat_room_id and request.use_context:
            from app.services.chat_service import ChatService

            if request.start_new_session:
                # 새 세션 시작: 현재 메시지만 사용 (이미 정리된 텍스트)
                analysis_text = cleaned_input_text
            else:
                # 기존 세션 또는 전체 컨텍스트 사용
                if hasattr(ChatService, "get_session_user_messages"):
                    # 세션 기반 메시지 조회 시도
                    session_messages = ChatService.get_session_user_messages(
                        db, request.chat_room_id, limit=5
                    )
                    if session_messages:
                        # 현재 메시지 제외하고 이전 세션 메시지들과 결합
                        previous_texts = [
                            clean_symptom_text(msg.content)  # 이전 메시지들도 정리
                            for msg in session_messages[:-1]  # 마지막(현재) 메시지 제외
                        ]
                        if previous_texts:
                            analysis_text = (
                                " ".join(previous_texts) + " " + cleaned_input_text
                            )
                    else:
                        # 세션 메시지가 없으면 전체 메시지에서 조회
                        recent_messages = ChatService.get_recent_user_messages(
                            db, request.chat_room_id, limit=5
                        )
                        if recent_messages:
                            previous_texts = [
                                clean_symptom_text(msg.content)  # 전체 메시지들도 정리
                                for msg in reversed(recent_messages[1:])
                            ]
                            if previous_texts:
                                analysis_text = (
                                    " ".join(previous_texts) + " " + cleaned_input_text
                                )
                else:
                    # 기존 로직 사용 (하위 호환)
                    recent_messages = ChatService.get_recent_user_messages(
                        db, request.chat_room_id, limit=5
                    )
                    if recent_messages:
                        previous_texts = [
                            clean_symptom_text(msg.content)  # 기존 로직에서도 정리
                            for msg in reversed(recent_messages[1:])
                        ]
                        if previous_texts:
                            analysis_text = (
                                " ".join(previous_texts) + " " + cleaned_input_text
                            )

        # ML 서비스 호출 (합친 텍스트로)
        ml_result = await ml_client.analyze_symptom(
            text=analysis_text,
            chat_room_id=request.chat_room_id,
            authorization=authorization,
        )

        if not ml_result:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML 서비스에 연결할 수 없습니다",
            )

        # 채팅방이 지정된 경우 봇 응답 저장 (임계치 이상일 때만)
        if request.chat_room_id:
            from app.services.chat_service import ChatService

            # 봇 응답 저장
            formatted_message = ml_client.format_disease_results(
                {"symptom_analysis": ml_result}
            )
            bot_message = ChatService.create_chat_message(
                db, request.chat_room_id, "BOT", formatted_message
            )
        else:
            # 결과 포맷팅만 수행
            formatted_message = ml_client.format_disease_results(
                {"symptom_analysis": ml_result}
            )

        # ML 결과에서 top_disease 추출
        disease_classifications = ml_result.get("disease_classifications", [])
        top_disease = (
            disease_classifications[0]
            if disease_classifications
            else {"disease_id": None, "label": "알 수 없음", "score": 0.0}
        )

        # 임계치 확인 (DB 저장 전에 확인)
        from app.core.config import settings

        confidence_threshold = settings.RECOMMEND_CONFIDENCE_THRESHOLD
        top_score = top_disease.get("score", 0.0)
        confidence_threshold_met = top_score >= confidence_threshold

        # 임계치 이하일 경우 증상 추가 요구 응답 (DB 저장 없음)
        if not confidence_threshold_met:
            # 채팅방이 지정된 경우 "증상 추가 요구" BOT 메시지 저장
            if request.chat_room_id:
                from app.services.chat_service import ChatService

                threshold_message = f"현재 증상으로는 정확한 진단이 어렵습니다. (신뢰도: {top_score:.1%})\n더 자세한 증상을 추가로 입력해주세요."
                ChatService.create_chat_message(
                    db, request.chat_room_id, "BOT", threshold_message
                )

            return SymptomAnalysisResponse(
                original_text=ml_result.get("original_text", analysis_text),
                processed_text=ml_result.get("processed_text", ""),
                disease_classifications=[],  # 빈 배열
                top_disease={
                    "label": "증상 추가 요구",
                    "score": top_score,
                },  # 특별한 응답
                user_id=str(current_user.id),
                chat_room_id=request.chat_room_id,
                inference_result_id=None,  # 임계치 이하이므로 저장하지 않음
                confidence_threshold_met=False,
                confidence_threshold=confidence_threshold,
            )

        # 임계치 이상일 경우에만 DB 저장
        from app.models.medical import Disease
        from app.models.model_inference import ModelInferenceResult

        # 질병 ID 매핑 (1, 2, 3순위 모두)
        def get_disease_id(disease_label):
            if disease_label:
                disease = (
                    db.query(Disease).filter(Disease.name == disease_label).first()
                )
                return disease.id if disease else None
            return None

        first_disease_id = get_disease_id(top_disease.get("label"))
        second_disease_id = get_disease_id(
            disease_classifications[1].get("label")
            if len(disease_classifications) > 1
            else None
        )
        third_disease_id = get_disease_id(
            disease_classifications[2].get("label")
            if len(disease_classifications) > 2
            else None
        )

        inference_result = ModelInferenceResult(
            user_id=current_user.id,
            chat_room_id=request.chat_room_id,
            chat_message_id=(
                user_message.id if user_message else None
            ),  # 사용자 메시지와 연결
            input_text=analysis_text,  # 합친 텍스트 사용
            processed_text=ml_result.get("processed_text", ""),
            first_disease_id=first_disease_id,  # 질병 ID 매핑
            first_disease_score=top_disease.get("score", 0.0),
            first_disease_label=top_disease.get("label"),
            second_disease_id=second_disease_id,  # 2순위 질병 ID 매핑
            second_disease_score=(
                disease_classifications[1].get("score", 0.0)
                if len(disease_classifications) > 1
                else None
            ),
            second_disease_label=(
                disease_classifications[1].get("label")
                if len(disease_classifications) > 1
                else None
            ),
            third_disease_id=third_disease_id,  # 3순위 질병 ID 매핑
            third_disease_score=(
                disease_classifications[2].get("score", 0.0)
                if len(disease_classifications) > 2
                else None
            ),
            third_disease_label=(
                disease_classifications[2].get("label")
                if len(disease_classifications) > 2
                else None
            ),
        )
        db.add(inference_result)
        db.commit()
        db.refresh(inference_result)

        logger.info(
            f"추론 결과 저장 완료 - ID: {inference_result.id}, 질병: {top_disease.get('label')}"
        )

        # 임계치 이상일 경우 정상 응답
        return SymptomAnalysisResponse(
            original_text=ml_result.get("original_text", analysis_text),
            processed_text=ml_result.get("processed_text", ""),
            disease_classifications=disease_classifications,
            top_disease=top_disease,
            user_id=str(current_user.id),
            chat_room_id=request.chat_room_id,
            inference_result_id=inference_result.id,  # 병원 추천을 위해 추가
            confidence_threshold_met=True,
            confidence_threshold=confidence_threshold,
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
    authorization: Optional[str] = Header(default=None),
):
    """
    전체 분석: 증상 분석 + 병원 추천
    """
    try:
        # ML 서비스 호출 (텍스트 정리 후)
        cleaned_text = clean_symptom_text(request.text)
        ml_result = await ml_client.get_full_analysis(
            text=cleaned_text,
            chat_room_id=request.chat_room_id,
            authorization=authorization,
        )

        if not ml_result:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML 서비스에 연결할 수 없습니다",
            )

        # 추론 결과를 DB에 저장
        import json

        from app.models.model_inference import ModelInferenceResult

        symptom_analysis = ml_result.get("symptom_analysis", {})
        disease_classifications = symptom_analysis.get("disease_classifications", [])
        top_disease = (
            disease_classifications[0]
            if disease_classifications
            else {"label": "알 수 없음", "score": 0.0}
        )

        inference_result = ModelInferenceResult(
            user_id=current_user.id,
            chat_room_id=request.chat_room_id,
            chat_message_id=None,  # 채팅 메시지와 연결되지 않은 경우
            input_text=clean_symptom_text(request.text),
            processed_text=symptom_analysis.get("processed_text", ""),
            first_disease_id=None,  # 질병 ID는 나중에 매핑 필요
            first_disease_score=top_disease.get("score", 0.0),
            first_disease_label=top_disease.get("label"),
            second_disease_id=None,
            second_disease_score=(
                disease_classifications[1].get("score", 0.0)
                if len(disease_classifications) > 1
                else None
            ),
            second_disease_label=(
                disease_classifications[1].get("label")
                if len(disease_classifications) > 1
                else None
            ),
            third_disease_id=None,
            third_disease_score=(
                disease_classifications[2].get("score", 0.0)
                if len(disease_classifications) > 2
                else None
            ),
            third_disease_label=(
                disease_classifications[2].get("label")
                if len(disease_classifications) > 2
                else None
            ),
        )
        db.add(inference_result)
        db.commit()
        db.refresh(inference_result)

        logger.info(
            f"전체 분석 추론 결과 저장 완료 - ID: {inference_result.id}, 질병: {top_disease.get('label')}"
        )

        # user_id를 최상위에 포함하여 반환 (프론트 요구사항 반영)
        if isinstance(ml_result, dict):
            ml_result["user_id"] = str(current_user.id)
            if request.chat_room_id is not None:
                ml_result["chat_room_id"] = request.chat_room_id
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
