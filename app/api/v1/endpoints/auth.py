"""
인증 관련 엔드포인트
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

router = APIRouter()

# Request/Response 모델
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    age: int
    gender: str  # 'MALE', 'FEMALE', 'OTHER'

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    nickname: str
    age: int
    gender: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister):
    """사용자 회원가입"""
    # 임시 구현 (실제로는 DB에 저장)
    if user_data.email == "test@example.com":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다."
        )
    
    # 임시 사용자 데이터
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": user_data.email,
        "nickname": user_data.nickname,
        "age": user_data.age,
        "gender": user_data.gender,
        "created_at": datetime.now(),
    }
    
    return UserResponse(**fake_user)

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """사용자 로그인"""
    # 임시 구현 (실제로는 DB에서 사용자 확인 및 비밀번호 검증)
    if login_data.email != "test@example.com" or login_data.password != "password123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 임시 토큰 및 사용자 데이터
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.temporary_token"
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": login_data.email,
        "nickname": "테스트 사용자",
        "age": 25,
        "gender": "MALE",
        "created_at": datetime.now(),
    }
    
    return TokenResponse(
        access_token=fake_token,
        token_type="bearer",
        user=UserResponse(**fake_user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user():
    """현재 사용자 정보 조회"""
    # 임시 구현 (실제로는 JWT 토큰에서 사용자 정보 추출)
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "nickname": "테스트 사용자",
        "age": 25,
        "gender": "MALE",
        "created_at": datetime.now(),
    }
    
    return UserResponse(**fake_user)

@router.post("/logout")
async def logout_user():
    """사용자 로그아웃"""
    return {"message": "성공적으로 로그아웃되었습니다."}
