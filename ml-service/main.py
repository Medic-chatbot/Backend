"""
Medical AI Service - 의료 증상 분석 및 질병 예측 서비스
형태소 분석 + BERT 모델 + 병원 추천 통합 서비스
"""

import logging
import os
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

import httpx
import torch
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from konlpy.tag import Okt
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 내부 서비스 앱(실제 라우트가 등록되는 앱)
ml_api = FastAPI(
    title="Medic AI Service",
    description="한국어 의료 증상 분석 및 질병 예측 서비스",
    version="2.0.0",
)

# 환경 변수
MODEL_NAME = os.getenv("MODEL_NAME", "unu-dev/krbert_ms2d_v1")
DEVICE = (
    "cuda"
    if torch.cuda.is_available() and os.getenv("DEVICE", "cpu") == "cuda"
    else "cpu"
)
API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://localhost:8000")

# 전역 변수로 모델과 분석기 저장
tokenizer = None
model = None
pipeline_model = None
morph_analyzer = None


class KoreanStemExtractor:
    """한국어 형태소 분석 및 어간 추출 (OKT)"""

    def __init__(self):
        self.analyzer_name = "okt"
        self.analyzer = Okt()

    def extract_stems(self, text, min_length=1, include_pos=False):
        """
        텍스트에서 어간/어근 추출
        """
        if not text or not text.strip():
            return []

        try:
            # 형태소 분석
            morphs = self.analyzer.pos(text, norm=True, stem=True)

            stems = []
            for word, pos in morphs:
                # 동사(V), 형용사(A), 명사(N) 처리
                if pos.startswith("V") or pos.startswith("A"):
                    # 동사/형용사의 어간 추출
                    if len(word) >= min_length:
                        if include_pos:
                            stems.append((word, pos))
                        else:
                            stems.append(word)
                elif pos.startswith("N"):
                    # 명사의 어근 추출
                    if len(word) >= min_length:
                        if include_pos:
                            stems.append((word, pos))
                        else:
                            stems.append(word)

            return stems

        except Exception as e:
            logger.error(f"형태소 분석 중 오류: {str(e)}")
            return []

    def extract_morphs_for_model(self, text):
        """
        BERT 모델 입력을 위한 형태소 추출 및 정제
        """
        stems = self.extract_stems(text, min_length=1)

        # 중복 제거 및 의미있는 형태소만 선택
        filtered_stems = []
        for stem in stems:
            # 길이가 1 이상이고 한글이 포함된 경우만
            if len(stem) >= 1 and re.search(r"[ㄱ-ㅎㅏ-ㅣ가-힣]", stem):
                filtered_stems.append(stem)

        # 중복 제거하되 순서 유지
        seen = set()
        unique_stems = []
        for stem in filtered_stems:
            if stem not in seen:
                seen.add(stem)
                unique_stems.append(stem)

        return " ".join(unique_stems)


# Pydantic 모델들
class SymptomRequest(BaseModel):
    """증상 분석 요청"""

    text: str
    user_id: Optional[str] = None
    chat_room_id: Optional[int] = None
    max_length: int = 512


class DiseaseClassification(BaseModel):
    """질병 분류 결과"""

    label: str
    score: float


class SymptomResponse(BaseModel):
    """증상 분석 응답"""

    original_text: str
    processed_text: str
    disease_classifications: List[DiseaseClassification]
    top_disease: str
    confidence: float
    user_id: Optional[str] = None
    chat_room_id: Optional[int] = None


class HospitalRecommendationRequest(BaseModel):
    """병원 추천 요청 (토큰 기반 사용자 식별)"""

    disease_name: str
    chat_room_id: int
    user_location: Optional[str] = None


class HealthResponse(BaseModel):
    """헬스체크 응답"""

    status: str
    model_loaded: bool
    device: str
    model_name: str
    analyzer: str


@ml_api.on_event("startup")
async def load_model():
    """애플리케이션 시작 시 모델 및 분석기 로드"""
    global tokenizer, model, pipeline_model, morph_analyzer

    try:
        logger.info(f"모델 로딩 시작: {MODEL_NAME}")
        logger.info(f"사용 디바이스: {DEVICE}")

        # 형태소 분석기 초기화
        logger.info("형태소 분석기 초기화...")
        morph_analyzer = KoreanStemExtractor()

        # BERT 모델 로드 (Pipeline 방식)
        logger.info("BERT 모델 로딩...")
        # Transformers deprecation 대응: return_all_scores → top_k=None 사용
        pipeline_model = pipeline(
            "text-classification",
            model=MODEL_NAME,
            device=0 if DEVICE == "cuda" else -1,
            top_k=None,  # 모든 라벨 스코어 반환
        )

        # Direct 모델 로드 (백업용)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        model.to(DEVICE)
        model.eval()

        logger.info("모든 모델 및 분석기 로딩 완료")

    except Exception as e:
        logger.error(f"모델 로딩 실패: {str(e)}")
        raise e


router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        model_loaded=pipeline_model is not None and morph_analyzer is not None,
        device=DEVICE,
        model_name=MODEL_NAME,
        analyzer=morph_analyzer.analyzer_name if morph_analyzer else "none",
    )


@router.post("/analyze", response_model=SymptomResponse)
async def analyze_symptom(request: SymptomRequest):
    """
    증상 텍스트 분석 및 질병 예측
    1. 형태소 분석으로 텍스트 전처리
    2. BERT 모델로 질병 분류
    3. 결과 반환
    """
    if pipeline_model is None or morph_analyzer is None:
        raise HTTPException(status_code=503, detail="모델이 아직 로드되지 않았습니다")

    try:
        # 1. 형태소 분석 및 전처리
        logger.info(f"입력 텍스트: {request.text}")
        processed_text = morph_analyzer.extract_morphs_for_model(request.text)
        logger.info(f"전처리된 텍스트: {processed_text}")

        if not processed_text.strip():
            raise HTTPException(
                status_code=400, detail="유효한 증상 텍스트를 입력해주세요"
            )

        # 2. BERT 모델 예측
        # 단일 입력에도 결과 shape를 일정하게 만들기 위해 리스트 입력으로 호출
        predictions = pipeline_model([processed_text])

        # 3. 결과 정리 (top_k=None 사용 시 [[{label,score}...]] 형태 기대)
        disease_classifications: List[DiseaseClassification] = []
        try:
            pred_list = predictions[0] if isinstance(predictions, list) else predictions
            # pred_list가 dict의 리스트라고 가정. 아니면 보수적으로 변환
            if isinstance(pred_list, dict):
                pred_iter = [pred_list]
            else:
                pred_iter = list(pred_list)

            for pred in pred_iter:
                if isinstance(pred, dict) and "label" in pred and "score" in pred:
                    disease_classifications.append(
                        DiseaseClassification(label=str(pred["label"]), score=float(pred["score"]))
                    )
        except Exception as _:
            logger.warning("예측 결과 파싱 중 포맷 이슈 발생, 빈 결과로 처리")

        # 상위 질병 추출
        disease_classifications.sort(key=lambda x: x.score, reverse=True)
        top_disease = (
            disease_classifications[0].label
            if disease_classifications
            else "알 수 없음"
        )
        confidence = (
            disease_classifications[0].score if disease_classifications else 0.0
        )

        response = SymptomResponse(
            original_text=request.text,
            processed_text=processed_text,
            disease_classifications=disease_classifications,
            top_disease=top_disease,
            confidence=confidence,
            user_id=request.user_id,
            chat_room_id=request.chat_room_id,
        )

        logger.info(f"분석 완료 - 예측 질병: {top_disease} (신뢰도: {confidence:.4f})")
        return response

    except Exception as e:
        logger.error(f"증상 분석 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"증상 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/recommend-hospitals")
async def recommend_hospitals(
    request: HospitalRecommendationRequest,
    authorization: Optional[str] = None,
):
    """
    질병명을 기반으로 병원 추천 요청
    API 서비스의 병원 추천 엔드포인트 호출
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 라이트 추천 엔드포인트 사용 (질환명 기반)
            headers = {"Content-Type": "application/json"}
            if authorization:
                headers["Authorization"] = authorization

            response = await client.post(
                f"{API_SERVICE_URL}/api/medical/recommend-by-disease",
                json={
                    "disease_name": request.disease_name,
                    "chat_room_id": request.chat_room_id,
                },
                headers=headers,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"병원 추천 API 오류: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="병원 추천 서비스에서 오류가 발생했습니다",
                )

    except httpx.RequestError as e:
        logger.error(f"병원 추천 요청 실패: {str(e)}")
        raise HTTPException(
            status_code=503, detail="병원 추천 서비스에 연결할 수 없습니다"
        )


from fastapi import Header


@router.post("/full-analysis")
async def full_analysis(request: SymptomRequest, authorization: Optional[str] = Header(default=None)):
    """
    완전한 분석: 증상 분석 + (임계치 기반) 병원 추천

    - 증상 분석을 먼저 수행
    - 최상위 질환 신뢰도(confidence)가 0.8 이상이고 user_id/chat_room_id가 있을 때만
      병원 추천 API를 호출하여 결과를 포함
    """
    try:
        # 1. 증상 분석
        symptom_result = await analyze_symptom(request)

        # 2. 임계치 기반 병원 추천
        hospital_result = None
        try:
            confidence = getattr(symptom_result, "confidence", 0.0) or 0.0
        except Exception:
            confidence = 0.0

        if (
            confidence >= 0.8
            and request.chat_room_id
            and getattr(symptom_result, "top_disease", None)
            and authorization
        ):
            hospital_request = HospitalRecommendationRequest(
                disease_name=symptom_result.top_disease,
                chat_room_id=request.chat_room_id,
            )
            try:
                hospital_result = await recommend_hospitals(
                    hospital_request, authorization=authorization
                )
            except Exception as e:
                logger.warning(f"병원 추천 실패: {str(e)}")

        return {
            "symptom_analysis": symptom_result,
            "hospital_recommendations": hospital_result,
        }

    except Exception as e:
        logger.error(f"전체 분석 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Medic AI Service",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "recommend-hospitals": "/recommend-hospitals",
            "full-analysis": "/full-analysis",
            "docs": "/docs",
        },
    }

# 디버그: 등록된 라우트 확인용
@router.get("/routes")
async def list_routes():
    try:
        return [
            getattr(r, "path", None) or getattr(r, "path_format", None) for r in ml_api.router.routes
        ]
    except Exception:
        return []


# 앱 노출: 동일 엔드포인트를 / 와 /ml 모두에서 제공
app = ml_api
# 라우터 이중 등록: /, /ml
app.include_router(router)
app.include_router(router, prefix="/ml")

# Docs under /ml as well
@app.get("/ml/openapi.json", include_in_schema=False)
async def ml_openapi():
    return JSONResponse(app.openapi())

@app.get("/ml/docs", response_class=HTMLResponse, include_in_schema=False)
async def ml_docs():
    return get_swagger_ui_html(
        openapi_url="/ml/openapi.json",
        title="Medic AI Service (ML) - Docs",
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
