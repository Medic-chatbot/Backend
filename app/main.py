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

# CORS 설정 (프론트엔드 연결용) - config.py에서 로딩
allowed_origins = settings.ALLOWED_HOSTS

# 개발 환경에서는 모든 origin 허용
if settings.DEBUG:
    allowed_origins = ["*"]

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

from app.api.deps import get_db

# 웹소켓 엔드포인트 직접 등록 (라우터를 통한 등록이 실패할 경우를 대비)
from app.api.endpoints.chat import manager, websocket_endpoint
from fastapi import Depends, Query, WebSocket
from sqlalchemy.orm import Session


@app.websocket("/api/chat/ws/{room_id}")
async def main_websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(None),
    db: Session = Depends(get_db),
):
    """메인 앱에 직접 등록된 웹소켓 엔드포인트"""
    import logging
    from uuid import UUID

    from app.core.config import settings
    from app.models.user import User
    from jose import JWTError, jwt

    logger = logging.getLogger(__name__)
    logger.info(
        f"WebSocket connection attempt: room_id={room_id}, token={token[:20] if token else None}..."
    )

    # JWT 토큰 검증 및 사용자 인증
    if not token:
        logger.warning("WebSocket connection rejected: No token provided")
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        # JWT 토큰 디코딩 및 사용자 정보 추출
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id_str = payload.get("sub")
            if user_id_str is None:
                await websocket.close(code=1008, reason="Invalid token")
                return

            # UUID로 변환
            user_id = UUID(user_id_str)

        except JWTError as e:
            logger.warning(
                f"WebSocket connection rejected: JWT validation failed - {str(e)}"
            )
            await websocket.close(code=1008, reason="Token validation failed")
            return

        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"WebSocket connection rejected: User not found - {user_id}")
            await websocket.close(code=1008, reason="User not found")
            return

        await manager.connect(websocket, room_id, str(user_id))

        # 연결 성공 메시지
        await websocket.send_json(
            {
                "type": "system",
                "content": f"채팅방 {room_id}에 연결되었습니다.",
                "room_id": room_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_json()
                logger.info(f"Received message: {data}")

                # 간단한 에코 응답
                await websocket.send_json(
                    {
                        "type": "echo",
                        "content": f"Echo: {data.get('content', '')}",
                        "room_id": room_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        manager.disconnect(room_id, str(user_id))


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
    # 로컬 개발 전용
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug",  # 모든 로그 출력
    )
