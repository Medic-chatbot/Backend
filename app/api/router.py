"""
API 라우터
"""

from app.api.endpoints import auth, chat, health
from fastapi import APIRouter

# API 라우터 생성
api_router = APIRouter()

# 엔드포인트 라우터 등록
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
