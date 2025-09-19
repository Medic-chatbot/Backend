"""
메인 라우터 설정
"""

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.chat import websocket_endpoint
from app.api.endpoints.health import router as health_router
from app.api.endpoints.medical import router as medical_router
from app.api.endpoints.ml import router as ml_router
from app.api.endpoints.users import router as users_router
from fastapi import APIRouter

# API 라우터 생성
api_router = APIRouter()

# 각 엔드포인트 라우터 포함
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(medical_router, prefix="/medical", tags=["medical"])
api_router.include_router(ml_router, prefix="/ml", tags=["ml"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])

# 웹소켓 엔드포인트를 직접 추가 (임시 해결책)
api_router.add_api_websocket_route("/ws/{room_id}", websocket_endpoint)
