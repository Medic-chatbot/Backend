"""
메인 라우터 설정
"""

from app.api.endpoints import auth, health, users
from fastapi import APIRouter

# API 라우터 생성
api_router = APIRouter()

# 각 엔드포인트 라우터 포함
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
