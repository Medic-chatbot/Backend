"""
헬스체크 엔드포인트
"""

import os
from datetime import datetime

import psutil
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


@router.get("/detailed")
async def detailed_health_check():
    """상세 헬스체크"""
    try:
        # 시스템 정보
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "status": "healthy",
            "service": "medical-chatbot-api",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "system": {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%",
                "available_memory": f"{memory.available / (1024**3):.2f} GB",
            },
            "environment": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.name,
            },
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "medical-chatbot-api",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@router.get("/ready")
async def readiness_check():
    """준비 상태 체크 (Kubernetes 등에서 사용)"""
    # 여기서 DB 연결, Redis 연결 등을 체크할 수 있음
    checks = {
        "database": "healthy",  # 실제로는 DB 연결 테스트
        "redis": "healthy",  # 실제로는 Redis 연결 테스트
        "ml_service": "healthy",  # 실제로는 ML 서비스 연결 테스트
    }

    all_healthy = all(status == "healthy" for status in checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/live")
async def liveness_check():
    """생존 상태 체크 (Kubernetes 등에서 사용)"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
    }
