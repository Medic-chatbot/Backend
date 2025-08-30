"""
채팅 관련 엔드포인트
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


# Request/Response 모델
class ChatRoomCreate(BaseModel):
    title: str


class ChatRoomResponse(BaseModel):
    id: str
    title: str
    is_active: bool
    created_at: datetime


class MessageSend(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    message_type: str  # 'USER' or 'BOT'
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    user_message: MessageResponse
    bot_message: MessageResponse


@router.get("/rooms", response_model=List[ChatRoomResponse])
async def get_chat_rooms():
    """사용자의 채팅방 목록 조회"""
    # 임시 데이터
    fake_rooms = [
        {
            "id": str(uuid.uuid4()),
            "title": "두통과 발열 증상",
            "is_active": True,
            "created_at": datetime.now(),
        },
        {
            "id": str(uuid.uuid4()),
            "title": "복통 관련 상담",
            "is_active": True,
            "created_at": datetime.now(),
        },
    ]

    return [ChatRoomResponse(**room) for room in fake_rooms]


@router.post("/rooms", response_model=ChatRoomResponse)
async def create_chat_room(room_data: ChatRoomCreate):
    """새 채팅방 생성"""
    # 임시 구현
    fake_room = {
        "id": str(uuid.uuid4()),
        "title": room_data.title,
        "is_active": True,
        "created_at": datetime.now(),
    }

    return ChatRoomResponse(**fake_room)


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(room_id: str):
    """채팅방의 메시지 목록 조회"""
    # 임시 데이터
    fake_messages = [
        {
            "id": str(uuid.uuid4()),
            "message_type": "USER",
            "content": "안녕하세요, 두통이 심해서 문의드려요.",
            "created_at": datetime.now(),
        },
        {
            "id": str(uuid.uuid4()),
            "message_type": "BOT",
            "content": "안녕하세요! 두통 증상에 대해 도움을 드리겠습니다. 언제부터 두통이 시작되셨나요?",
            "created_at": datetime.now(),
        },
    ]

    return [MessageResponse(**msg) for msg in fake_messages]


@router.post("/rooms/{room_id}/messages", response_model=ChatResponse)
async def send_message(room_id: str, message_data: MessageSend):
    """메시지 전송 및 챗봇 응답"""
    # 사용자 메시지 생성
    user_message = {
        "id": str(uuid.uuid4()),
        "message_type": "USER",
        "content": message_data.content,
        "created_at": datetime.now(),
    }

    # 임시 챗봇 응답 (실제로는 ML 서비스 호출)
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

    bot_message = {
        "id": str(uuid.uuid4()),
        "message_type": "BOT",
        "content": bot_content,
        "created_at": datetime.now(),
    }

    return ChatResponse(
        user_message=MessageResponse(**user_message),
        bot_message=MessageResponse(**bot_message),
    )


@router.delete("/rooms/{room_id}")
async def delete_chat_room(room_id: str):
    """채팅방 삭제"""
    return {"message": "채팅방이 삭제되었습니다."}


@router.get("/test")
async def test_chat():
    """채팅 API 테스트"""
    return {
        "message": "채팅 API가 정상적으로 작동합니다.",
        "timestamp": datetime.now().isoformat(),
        "available_endpoints": [
            "GET /api/v1/chat/rooms - 채팅방 목록",
            "POST /api/v1/chat/rooms - 채팅방 생성",
            "GET /api/v1/chat/rooms/{room_id}/messages - 메시지 목록",
            "POST /api/v1/chat/rooms/{room_id}/messages - 메시지 전송",
            "DELETE /api/v1/chat/rooms/{room_id} - 채팅방 삭제",
        ],
    }
