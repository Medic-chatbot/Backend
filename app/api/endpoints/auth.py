"""
인증 관련 엔드포인트
"""

from datetime import datetime, timedelta
from typing import Any

from app.api.deps import authenticate_user, get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@router.post("/register", response_model=UserResponse)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """새로운 사용자 등록"""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다.",
        )

    hashed_password = get_password_hash(user_in.password)
    logger.debug(f"Registering user with email: {user_in.email}")
    logger.debug(f"Password hash: {hashed_password}")

    user = User(
        email=user_in.email,
        password_hash=hashed_password,
        nickname=user_in.nickname,
        age=user_in.age,
        gender=user_in.gender,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    *,
    db: Session = Depends(get_db),
    login_data: UserLogin,
) -> Any:
    """사용자 로그인 및 액세스 토큰 발급"""
    logger.debug(f"Login attempt for email: {login_data.email}")
    
    # 사용자 조회
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        logger.debug(f"User not found: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Found user: {user.email}")
    logger.debug(f"Stored password hash: {user.password_hash}")
    
    # 비밀번호 검증
    from app.core.security import verify_password
    if not verify_password(login_data.password, user.password_hash):
        logger.debug("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 로그인 시간 업데이트
    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    logger.debug("Login successful, token generated")
    return {"access_token": access_token, "token_type": "bearer", "user": user}


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