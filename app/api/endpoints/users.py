"""
사용자 관련 엔드포인트
"""

import logging
from typing import Any, Dict

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserLocationUpdate, UserResponse
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
) -> Any:
    """현재 사용자 프로필 조회"""
    return current_user


@router.put("/location", response_model=UserResponse)
async def update_user_location(
    *,
    db: Session = Depends(get_db),
    location_data: UserLocationUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 위치 정보 업데이트 (자동 지오코딩)

    프론트엔드에서 도로명 주소만 전송하면
    백엔드에서 카카오 지오코딩 API를 통해 자동으로 위도/경도를 변환하여 저장합니다.
    """
    try:
        logger.info(f"User {current_user.id} updating location with geocoding")

        updated_user = await UserService.update_user_location(
            db=db, user=current_user, location_data=location_data
        )

        return updated_user

    except ValueError as e:
        # 지오코딩 실패 (주소를 찾을 수 없음)
        logger.warning(f"Geocoding failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user location: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="위치 정보 업데이트 중 오류가 발생했습니다.",
        )


@router.get("/location")
def get_user_location(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """사용자 위치 정보 조회"""
    location_info = UserService.get_user_location(current_user)

    if not location_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="위치 정보가 설정되지 않았습니다.",
        )

    return {"message": "위치 정보 조회 성공", "data": location_info}


@router.get("/location/status")
def get_location_status(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """사용자 위치 정보 설정 상태 확인"""
    has_location = UserService.has_location_info(current_user)

    return {
        "has_location": has_location,
        "message": (
            "위치 정보가 설정되어 있습니다."
            if has_location
            else "위치 정보를 설정해주세요."
        ),
    }


@router.delete("/location")
def delete_user_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """사용자 위치 정보 삭제"""
    try:
        logger.info(f"User {current_user.id} deleting location")

        setattr(current_user, "road_address", None)
        setattr(current_user, "latitude", None)
        setattr(current_user, "longitude", None)

        db.commit()

        return {"message": "위치 정보가 성공적으로 삭제되었습니다."}

    except Exception as e:
        logger.error(f"Error deleting user location: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="위치 정보 삭제 중 오류가 발생했습니다.",
        )
