"""
사용자 관련 서비스 로직
"""

import logging
from typing import Optional

from app.models.user import User
from app.schemas.user import UserLocationUpdate
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관련 비즈니스 로직"""

    @staticmethod
    def update_user_location(
        db: Session, user: User, location_data: UserLocationUpdate
    ) -> User:
        """
        사용자 위치 정보 업데이트

        Args:
            db: 데이터베이스 세션
            user: 사용자 객체
            location_data: 위치 정보 데이터

        Returns:
            User: 업데이트된 사용자 객체
        """
        try:
            logger.info(f"Updating location for user {user.id}")

            # 사용자 위치 정보 업데이트
            setattr(user, "road_address", location_data.road_address)
            setattr(user, "latitude", location_data.latitude)
            setattr(user, "longitude", location_data.longitude)

            db.commit()
            db.refresh(user)

            logger.info(f"Successfully updated location for user {user.id}")
            return user

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
