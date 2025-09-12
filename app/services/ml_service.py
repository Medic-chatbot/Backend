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
        if confidence >= 0.9:
            confidence_msg = "높은 확률로"
        elif confidence >= 0.77:
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
        """병원 추천 결과를 사용자 친화적인 메시지로 변환(반경/장비 상세 포함)."""
        if not hospital_result:
            return ""

        # 반경 정보
        radius = None
        try:
            radius = hospital_result.get("search_criteria", {}).get("max_distance")
        except Exception:
            radius = None

        header = "\n\n🏥 **추천 병원 정보**"
        if radius:
            try:
                header += f" (반경 {float(radius):.0f}km 내)"
            except Exception:
                pass
        header += "\n"
        message = header

        # 백엔드 응답 호환: recommendations(라이트) 우선, 없으면 hospitals 키 사용
        items = hospital_result.get("recommendations") or hospital_result.get("hospitals") or []
        if items:
            # 필수 장비 목록(있을 때만 표출)
            req_equips = hospital_result.get("required_equipment") or []
            if req_equips:
                message += "필수 장비: " + ", ".join(req_equips) + "\n"

            for i, h in enumerate(items[:3], 1):  # 상위 3개만
                name = h.get("name") or h.get("hospital", {}).get("name") or "병원명 불명"
                address = h.get("address") or h.get("hospital", {}).get("address") or "주소 정보 없음"
                phone = h.get("phone") or h.get("hospital", {}).get("phone") or "전화번호 정보 없음"

                message += f"\n{i}. **{name}**\n   📍 {address}\n"
                if phone and phone != "전화번호 정보 없음":
                    message += f"   📞 {phone}\n"

                # 병원별 장비 상세(있을 때만)
                if req_equips:
                    details = h.get("equipment_details") or []
                    if details:
                        parts = []
                        for d in details:
                            n = d.get("name")
                            q = d.get("quantity")
                            if n and q is not None:
                                parts.append(f"{n} x {q}")
                        if parts:
                            message += f"   🔧 장비: " + ", ".join(parts) + "\n"

                # 랭킹 이유(점수 요약)
                sb = h.get("score_breakdown") or {}
                if sb:
                    try:
                        es = sb.get("equipment_score")
                        ss = sb.get("specialist_score")
                        ds = sb.get("distance_score")
                        fs = sb.get("final_score")
                        mc = sb.get("matched_equipment_count")
                        tr = sb.get("total_required_equipment")
                        weights = sb.get("weights", {})
                        w_e = weights.get("equip")
                        w_s = weights.get("spec")
                        w_d = weights.get("dist")
                        if fs is not None:
                            message += f"   ⭐ 총점: {fs}"
                            # 가장 큰 기여 요인 표시
                            comps = [("장비", es or 0), ("전문의", ss or 0), ("거리", ds or 0)]
                            comps.sort(key=lambda x: x[1], reverse=True)
                            top_name, top_val = comps[0]
                            message += f" (최대 기여: {top_name} {top_val})\n"
                        # 상세 점수 표기
                        if es is not None and ss is not None and ds is not None and w_e and w_s and w_d:
                            message += (
                                f"   📊 점수: 장비 {es}/{w_e}, 전문의 {ss}/{w_s}, 거리 {ds}/{w_d}\n"
                            )
                        # 우선순위 보너스는 사용자 메시지에서 비노출 (불확정 요인)
                        if tr:
                            message += f"   📌 필수장비 매칭: {mc}/{tr}\n"
                    except Exception:
                        pass
        else:
            message += "해당 질병에 대한 병원 정보를 찾을 수 없습니다."

        return message


# ML 서비스 클라이언트 인스턴스
ml_client = MLServiceClient()
