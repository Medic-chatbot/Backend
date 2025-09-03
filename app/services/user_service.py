"""
사용자 관련 서비스 로직
"""

import logging
from typing import Optional

from app.models.user import User
from app.schemas.user import UserLocationUpdate
from app.services.geocoding_service import GeocodingService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관련 비즈니스 로직"""

    @staticmethod
    async def update_user_location(
        db: Session, user: User, location_data: UserLocationUpdate
    ) -> User:
        """
        사용자 위치 정보 업데이트 (자동 지오코딩)

        Args:
            db: 데이터베이스 세션
            user: 사용자 객체
            location_data: 위치 정보 데이터 (도로명 주소만)

        Returns:
            User: 업데이트된 사용자 객체

        Raises:
            ValueError: 지오코딩 실패 시
        """
        try:
            logger.info(
                f"Geocoding address for user {user.id}: {location_data.road_address}"
            )

            # 카카오 지오코딩으로 위도/경도 변환
            coordinates = await GeocodingService.geocode_address(
                location_data.road_address
            )

            if not coordinates:
                raise ValueError(
                    f"주소를 찾을 수 없습니다: {location_data.road_address}"
                )

            latitude, longitude = coordinates

            # 사용자 위치 정보 업데이트
            setattr(user, "road_address", location_data.road_address)
            setattr(user, "latitude", latitude)
            setattr(user, "longitude", longitude)

            db.commit()
            db.refresh(user)

            logger.info(
                f"Successfully updated location for user {user.id}: ({latitude}, {longitude})"
            )
            return user

        except ValueError:
            # 지오코딩 실패는 그대로 다시 발생
            raise
        except Exception as e:
            logger.error(f"Error updating user location: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    def get_user_location(user: User) -> Optional[dict]:
        """
        사용자 위치 정보 조회

        Args:
            user: 사용자 객체

        Returns:
            dict: 위치 정보 딕셔너리 또는 None
        """
        if getattr(user, "latitude", None) and getattr(user, "longitude", None):
            return {
                "road_address": getattr(user, "road_address", None),
                "latitude": getattr(user, "latitude", None),
                "longitude": getattr(user, "longitude", None),
            }
        return None

    @staticmethod
    def has_location_info(user: User) -> bool:
        """
        사용자가 위치 정보를 가지고 있는지 확인

        Args:
            user: 사용자 객체

        Returns:
            bool: 위치 정보 존재 여부
        """
        return (
            getattr(user, "latitude", None) is not None
            and getattr(user, "longitude", None) is not None
        )
