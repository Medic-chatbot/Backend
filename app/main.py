"""
의료 챗봇 서비스 FastAPI 애플리케이션
"""

import logging
import os
from datetime import datetime

import uvicorn
from app.api.router import api_router
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Medical Chatbot API",
    description="의료 챗봇 서비스 백엔드 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정 (프론트엔드 연결용)
allowed_origins = [
    "https://v0-medical-chatbot-ui-xi.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://13.125.229.157",
    "http://13.125.229.157:80",
    "https://13.125.229.157",
]

# 개발 환경에서는 모든 origin 허용
if settings.DEBUG:
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
    expose_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api")


# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Medical Chatbot API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
    }


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "medical-chatbot-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


# CORS preflight는 CORSMiddleware가 처리하므로 별도 핸들러 불필요


# 예외 처리
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "요청한 리소스를 찾을 수 없습니다.",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "서버 내부 오류가 발생했습니다.",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="debug",
    )
