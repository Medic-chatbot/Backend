"""
채팅 관련 엔드포인트
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# 로거 설정
logger = logging.getLogger(__name__)

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.ml_service import ml_client
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


# Request/Response 모델
class ChatRoomCreate(BaseModel):
    title: str


class ChatRoomResponse(BaseModel):
    id: int
    title: str
    is_active: bool
    created_at: datetime
    final_disease_id: Optional[int] = None

    class Config:
        from_attributes = True


class MessageSend(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    message_type: str  # 'USER' or 'BOT'
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    user_message: MessageResponse
    bot_message: MessageResponse


# WebSocket 관련 스키마
class WebSocketMessage(BaseModel):
    """WebSocket 메시지 스키마"""

    type: str  # 'user_message', 'bot_message', 'system'
    content: str
    room_id: int
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 채팅방별 연결 관리: room_id -> {user_id: websocket}
        self.active_connections: dict[int, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: str):
        """WebSocket 연결"""
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

        self.active_connections[room_id][user_id] = websocket

    def disconnect(self, room_id: int, user_id: str):
        """WebSocket 연결 해제"""
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]

            # 채팅방에 연결된 사용자가 없으면 채팅방 제거
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, message: str, room_id: int, user_id: str):
        """특정 사용자에게 메시지 전송"""
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                websocket = self.active_connections[room_id][user_id]
                await websocket.send_text(message)

    async def broadcast_to_room(
        self, message: str, room_id: int, exclude_user: Optional[str] = None
    ):
        """채팅방의 모든 사용자에게 브로드캐스트 (특정 사용자 제외 가능)"""
        if room_id in self.active_connections:
            for user_id, websocket in self.active_connections[room_id].items():
                if exclude_user is None or user_id != exclude_user:
                    await websocket.send_text(message)

    async def broadcast_json_to_room(
        self, data: dict, room_id: int, exclude_user: Optional[str] = None
    ):
        """채팅방의 모든 사용자에게 JSON 데이터 브로드캐스트"""
        if room_id in self.active_connections:
            for user_id, websocket in self.active_connections[room_id].items():
                if exclude_user is None or user_id != exclude_user:
                    await websocket.send_json(data)


# Connection Manager 인스턴스 생성
manager = ConnectionManager()


@router.get("/rooms", response_model=List[ChatRoomResponse])
async def get_chat_rooms(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자의 채팅방 목록 조회"""
    try:
        # UUID 객체로 변환
        user_uuid = UUID(str(current_user.id))
        chat_rooms = ChatService.get_user_chat_rooms(db, user_uuid)
        return chat_rooms
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채팅방 목록 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/rooms", response_model=ChatRoomResponse)
async def create_chat_room(
    room_data: ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """새 채팅방 생성"""
    try:
        # UUID 객체로 변환
        user_uuid = UUID(str(current_user.id))
        chat_room = ChatService.create_chat_room(db, user_uuid, room_data.title)
        return chat_room
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채팅방 생성 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """채팅방의 메시지 목록 조회"""
    try:
        # 채팅방 존재 및 권한 확인
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            logger.warning(f"Chat room not found: {room_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채팅방을 찾을 수 없습니다.",
            )

        # 채팅방이 현재 사용자의 것인지 확인
        if str(chat_room.user_id) != str(current_user.id):
            logger.warning(
                f"Unauthorized access to chat room {room_id} by user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 채팅방에 접근할 권한이 없습니다.",
            )

        messages = ChatService.get_chat_messages(db, room_id)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메시지 목록 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/rooms/{room_id}/messages", response_model=ChatResponse)
async def send_message(
    room_id: int,
    message_data: MessageSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """메시지 전송 및 챗봇 응답"""
    try:
        # 채팅방 존재 및 권한 확인
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채팅방을 찾을 수 없습니다.",
            )

        # 채팅방이 현재 사용자의 것인지 확인
        if str(chat_room.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 채팅방에 메시지를 보낼 권한이 없습니다.",
            )

        # 사용자 메시지 저장
        user_message = ChatService.create_chat_message(
            db, room_id, "USER", message_data.content
        )

        # 임시 챗봇 응답 생성 (나중에 ML 서비스로 교체)
        bot_responses = {
            "두통": "두통의 원인은 다양할 수 있습니다. 스트레스, 수면 부족, 탈수 등이 주요 원인입니다. 증상이 지속되면 신경과 진료를 받아보시기 바랍니다.",
            "복통": "복통의 위치와 정도에 따라 원인이 다를 수 있습니다. 지속적인 복통이라면 내과나 소화기내과 진료를 권장드립니다.",
            "발열": "발열은 감염이나 염증의 신호일 수 있습니다. 38도 이상의 고열이 지속되면 즉시 의료진의 진료를 받으시기 바랍니다.",
        }

        # 키워드 기반 간단한 응답 생성
        bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다. 지속적인 증상이 있으시면 전문의 진료를 받아보시기 바랍니다."

        for keyword, response in bot_responses.items():
            if keyword in message_data.content:
                bot_content = response
                break

        # 봇 메시지 저장
        bot_message = ChatService.create_chat_message(db, room_id, "BOT", bot_content)

        return ChatResponse(
            user_message=user_message,
            bot_message=bot_message,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메시지 전송 중 오류가 발생했습니다: {str(e)}",
        )


@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """채팅방 삭제 (비활성화)"""
    try:
        # 채팅방 존재 및 권한 확인
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채팅방을 찾을 수 없습니다.",
            )

        # 채팅방이 현재 사용자의 것인지 확인
        if str(chat_room.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 채팅방을 삭제할 권한이 없습니다.",
            )

        # 채팅방 비활성화 (소프트 삭제)
        success = ChatService.deactivate_chat_room(db, room_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="채팅방 삭제 중 오류가 발생했습니다.",
            )

        return {"message": "채팅방이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채팅방 삭제 중 오류가 발생했습니다: {str(e)}",
        )


