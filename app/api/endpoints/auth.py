"""
인증 관련 엔드포인트
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Any

from app.api.deps import authenticate_user, get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin
from app.schemas.user import UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 로거 설정
logger = logging.getLogger("auth")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """새로운 사용자 등록"""
    try:
        print(f"[Register] Starting registration for email: {user_in.email}")
        logger.debug(f"[Register] Starting registration for email: {user_in.email}")

        user = db.query(User).filter(User.email == user_in.email).first()
        if user:
            print(f"[Register] User already exists: {user_in.email}")
            logger.debug(f"[Register] User already exists: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        hashed_password = get_password_hash(user_in.password)
        print(f"[Register] Generated password hash: {hashed_password}")
        logger.debug(f"[Register] Generated password hash: {hashed_password}")

        user = User(
            email=user_in.email,
            password_hash=hashed_password,
            nickname=user_in.nickname,
            age=user_in.age,
            gender=user_in.gender,
            road_address=user_in.road_address,
            latitude=user_in.latitude,
            longitude=user_in.longitude,
        )

        print(f"[Register] Adding user to database: {user.email}")
        logger.debug(f"[Register] Adding user to database: {user.email}")
        db.add(user)

        print("[Register] Committing transaction...")
        logger.debug("[Register] Committing transaction...")
        db.commit()

        print("[Register] Refreshing user object...")
        logger.debug("[Register] Refreshing user object...")
        db.refresh(user)

        print(f"[Register] Successfully registered user: {user.email}")
        logger.debug(f"[Register] Successfully registered user: {user.email}")

        # DB에 실제로 저장되었는지 확인
        check_user = db.query(User).filter(User.email == user_in.email).first()
        print(f"[Register] Verification - User in DB: {check_user is not None}")
        logger.debug(f"[Register] Verification - User in DB: {check_user is not None}")

        return user

    except Exception as e:
        print(f"[Register] Error during registration: {str(e)}")
        logger.error(f"[Register] Error during registration: {str(e)}")
        db.rollback()
        raise


@router.post("/login", response_model=Token)
def login(
    *,
    db: Session = Depends(get_db),
    login_data: UserLogin,
) -> Any:
    """사용자 로그인 및 액세스 토큰 발급"""
    try:
        print(f"[Login] Attempt for email: {login_data.email}")
        logger.debug(f"[Login] Attempt for email: {login_data.email}")

        # 사용자 조회
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user:
            print(f"[Login] User not found: {login_data.email}")
            logger.debug(f"[Login] User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        print(f"[Login] Found user: {user.email}")
        print(f"[Login] Stored password hash: {user.password_hash}")
        logger.debug(f"[Login] Found user: {user.email}")
        logger.debug(f"[Login] Stored password hash: {user.password_hash}")

        # 비밀번호 검증
        from app.core.security import verify_password

        if not verify_password(login_data.password, str(user.password_hash)):
            print("[Login] Password verification failed")
            logger.debug("[Login] Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 로그인 시간 업데이트
        setattr(user, "last_login_at", datetime.utcnow())
        db.commit()

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )

        print("[Login] Login successful, token generated")
        logger.debug("[Login] Login successful, token generated")

        # UserResponse 변환을 위해 user 객체를 dict로 변환
        user_dict = {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "age": user.age,
            "gender": user.gender,
            "road_address": getattr(user, "road_address", None),
            "latitude": getattr(user, "latitude", None),
            "longitude": getattr(user, "longitude", None),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        return {"access_token": access_token, "token_type": "bearer", "user": user_dict}

    except Exception as e:
        print(f"[Login] Error during login: {str(e)}")
        logger.error(f"[Login] Error during login: {str(e)}")
        raise


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """현재 로그인한 사용자 정보 조회"""
    return current_user


@router.post("/logout")
def logout() -> Any:
    """사용자 로그아웃"""
    return {"message": "성공적으로 로그아웃되었습니다."}
