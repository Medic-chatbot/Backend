"""
지오코딩 서비스 로직
"""

import logging
from typing import Dict, Optional, Tuple

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeocodingService:
    """카카오 지오코딩 서비스"""

    KAKAO_GEOCODING_URL = "https://dapi.kakao.com/v2/local/search/address.json"

    @classmethod
    async def geocode_address(cls, address: str) -> Optional[Tuple[float, float]]:
        """
        도로명 주소를 위도/경도로 변환

        Args:
            address: 도로명 주소

        Returns:
            Tuple[float, float]: (위도, 경도) 또는 None
        """
        if not settings.KAKAO_REST_API_KEY:
            logger.error("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
            return None

        try:
            headers = {
                "Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}",
                "Content-Type": "application/json",
            }

            params = {"query": address}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    cls.KAKAO_GEOCODING_URL, headers=headers, params=params
                )

            if response.status_code != 200:
                logger.error(f"카카오 지오코딩 API 오류: {response.status_code}")
                return None

            data = response.json()
            documents = data.get("documents", [])

            if not documents:
                logger.warning(f"주소를 찾을 수 없습니다: {address}")
                return None

            # 첫 번째 결과 사용
            first_result = documents[0]
            latitude = float(first_result["y"])
            longitude = float(first_result["x"])

            logger.info(f"지오코딩 성공: {address} -> ({latitude}, {longitude})")
            return (latitude, longitude)

        except Exception as e:
            logger.error(f"지오코딩 중 오류 발생: {str(e)}")
            return None

    @classmethod
    async def geocode_address_with_details(cls, address: str) -> Optional[Dict]:
        """
        도로명 주소를 위도/경도로 변환 (상세 정보 포함)

        Args:
            address: 도로명 주소

        Returns:
            Dict: 지오코딩 결과 상세 정보 또는 None
        """
        if not settings.KAKAO_REST_API_KEY:
            logger.error("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
            return None

        try:
            headers = {
                "Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}",
                "Content-Type": "application/json",
            }

            params = {"query": address}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    cls.KAKAO_GEOCODING_URL, headers=headers, params=params
                )

            if response.status_code != 200:
                logger.error(f"카카오 지오코딩 API 오류: {response.status_code}")
                return None

            data = response.json()
            documents = data.get("documents", [])

            if not documents:
                logger.warning(f"주소를 찾을 수 없습니다: {address}")
                return None

            # 첫 번째 결과 사용
            first_result = documents[0]

            result = {
                "latitude": float(first_result["y"]),
                "longitude": float(first_result["x"]),
                "road_address": first_result.get("road_address", {}).get(
                    "address_name", address
                ),
                "address": first_result.get("address", {}).get("address_name", ""),
                "region_1depth": first_result.get("address", {}).get(
                    "region_1depth_name", ""
                ),
                "region_2depth": first_result.get("address", {}).get(
                    "region_2depth_name", ""
                ),
                "region_3depth": first_result.get("address", {}).get(
                    "region_3depth_name", ""
                ),
            }

            logger.info(f"지오코딩 성공: {address} -> {result}")
            return result

        except Exception as e:
            logger.error(f"지오코딩 중 오류 발생: {str(e)}")
            return None
