"""
ML 서비스와의 통신을 담당하는 클라이언트 서비스
"""

import logging
from typing import Dict, List, Optional

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class MLServiceClient:
    """ML 서비스 클라이언트"""

    def __init__(self):
        self.timeout = 30.0

    @property
    def base_url(self) -> str:
        # 항상 최신 환경 설정을 반영
        return getattr(settings, "ML_SERVICE_URL", "http://ml-service:8001")

    async def analyze_symptom(
        self,
        text: str,
        chat_room_id: Optional[int] = None,
        authorization: Optional[str] = None,
    ) -> Dict:
        """
        증상 텍스트를 분석하여 질병 예측 결과 반환
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/analyze",
                    json={
                        "text": text,
                        "chat_room_id": chat_room_id,
                    },
                    headers={
                        "Content-Type": "application/json",
                        **({"Authorization": authorization} if authorization else {}),
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(
                        f"ML 분석 성공 - 예측 질병: {result.get('top_disease')}"
                    )
                    return result
                else:
                    logger.error(
                        f"ML 서비스 오류: {response.status_code} - {response.text}"
                    )
                    return None

        except httpx.RequestError as e:
            logger.error(f"ML 서비스 연결 실패: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"ML 분석 중 예상치 못한 오류: {str(e)}")
            return None

    async def get_full_analysis(
        self,
        text: str,
        chat_room_id: Optional[int] = None,
        authorization: Optional[str] = None,
    ) -> Dict:
        """
        전체 분석: 증상 분석 + 병원 추천
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/full-analysis",
                    json={
                        "text": text,
                        "chat_room_id": chat_room_id,
                    },
                    headers={
                        "Content-Type": "application/json",
                        **({"Authorization": authorization} if authorization else {}),
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"전체 분석 성공")
                    return result
                else:
                    logger.error(
                        f"ML 서비스 오류: {response.status_code} - {response.text}"
                    )
                    return None

        except httpx.RequestError as e:
            logger.error(f"ML 서비스 연결 실패: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"전체 분석 중 예상치 못한 오류: {str(e)}")
            return None

    async def health_check(self) -> bool:
        """
        ML 서비스 상태 확인
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

    def format_disease_results(self, ml_result: Dict) -> str:
        """
        ML 분석 결과를 사용자 친화적인 메시지로 변환
        """
        if not ml_result:
            return "죄송합니다. 증상 분석 중 오류가 발생했습니다."

        symptom_analysis = ml_result.get("symptom_analysis", ml_result)

        top_disease = symptom_analysis.get("top_disease", "알 수 없음")
        confidence = symptom_analysis.get("confidence", 0.0)
        disease_classifications = symptom_analysis.get("disease_classifications", [])

        # 신뢰도에 따른 메시지 조정
        confidence_msg = ""
        if confidence >= 0.8:
            confidence_msg = "높은 확률로"
        elif confidence >= 0.6:
            confidence_msg = "어느 정도 확률로"
        elif confidence >= 0.4:
            confidence_msg = "가능성이 있는"
        else:
            confidence_msg = "낮은 확률이지만"

        # 기본 메시지
        message = f"분석 결과, {confidence_msg} **{top_disease}**와 관련된 증상으로 보입니다. (신뢰도: {confidence:.1%})\n\n"

        # 상위 3개 질병 정보 추가
        if len(disease_classifications) > 1:
            message += "기타 가능한 질병들:\n"
            for i, disease in enumerate(disease_classifications[1:4], 1):
                message += f"{i}. {disease['label']} ({disease['score']:.1%})\n"

        message += "\n⚠️ 이는 AI 분석 결과이며, 정확한 진단을 위해서는 반드시 의료진과 상담하시기 바랍니다."

        return message

    def format_hospital_results(self, hospital_result: Dict) -> str:
        """
        병원 추천 결과를 사용자 친화적인 메시지로 변환
        """
        if not hospital_result:
            return ""

        message = "\n\n🏥 **추천 병원 정보**\n"

        # 병원 목록이 있는 경우
        hospitals = hospital_result.get("hospitals", [])
        if hospitals:
            for i, hospital in enumerate(hospitals[:3], 1):  # 상위 3개만
                name = hospital.get("name", "병원명 불명")
                address = hospital.get("address", "주소 정보 없음")
                phone = hospital.get("phone", "전화번호 정보 없음")

                message += f"\n{i}. **{name}**\n"
                message += f"   📍 {address}\n"
                if phone != "전화번호 정보 없음":
                    message += f"   📞 {phone}\n"
        else:
            message += "해당 질병에 대한 병원 정보를 찾을 수 없습니다."

        return message


# ML 서비스 클라이언트 인스턴스
ml_client = MLServiceClient()
