"""
의존성 주입 관련 함수
"""

from typing import Optional

from app.core.config import settings
from app.core.security import verify_password
from app.db.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """현재 인증된 사용자 정보 조회"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
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
    if not verify_password(
        password, user.password_hash
    ):  # 변경: hashed_password -> password_hash
        return None
    return user
