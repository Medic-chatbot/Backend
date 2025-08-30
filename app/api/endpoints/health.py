"""
헬스체크 엔드포인트
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "service": "medical-chatbot-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check():
    """준비 상태 체크 (Load Balancer용)"""
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/live")
async def liveness_check():
    """생존 상태 체크 (Load Balancer용)"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
    }
