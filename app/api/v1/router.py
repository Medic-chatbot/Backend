"""
API v1 라우터
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, chat

# API 라우터 생성
api_router = APIRouter()

# 엔드포인트 라우터 등록
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
