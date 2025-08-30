"""
의존성 주입 관련 함수
"""

from typing import Optional

from app.core.config import settings
from app.core.security import verify_password
from app.db.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

security = HTTPBearer()


def get_token_from_cookie(request: Request) -> Optional[str]:
    """쿠키에서 토큰 추출"""
    cookie_authorization: str = request.cookies.get(settings.COOKIE_NAME)
    if not cookie_authorization:
        return None
    
    scheme, _, token = cookie_authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    
    return token


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """현재 인증된 사용자 정보 조회 (쿠키 기반)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_token_from_cookie(request)
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user