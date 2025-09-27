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
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    message: MessageResponse
    bot_response: Optional[MessageResponse] = None


class WebSocketMessage(BaseModel):
    type: str
    content: str
    room_id: int
    user_id: Optional[str] = None
    message_id: Optional[int] = None

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
        """채팅방의 모든 사용자에게 JSON 브로드캐스트 (특정 사용자 제외 가능)"""
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
        # 사용자가 해당 채팅방에 접근 권한이 있는지 확인
        user_uuid = UUID(str(current_user.id))
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room or chat_room.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 채팅방에 접근할 권한이 없습니다.",
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
    """채팅방에 메시지 전송"""
    try:
        # 사용자가 해당 채팅방에 접근 권한이 있는지 확인
        user_uuid = UUID(str(current_user.id))
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room or chat_room.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 채팅방에 접근할 권한이 없습니다.",
            )

        # 사용자 메시지 저장
        user_message = ChatService.create_chat_message(
            db, room_id, "USER", message_data.content
        )

        # ML 서비스를 통한 증상 분석
        bot_content = "분석 중입니다..."

        # 먼저 "분석 중" 메시지 저장
        analyzing_message = ChatService.create_chat_message(
            db, room_id, "BOT", bot_content
        )

        try:
            # ML 서비스 호출
            ml_result = await ml_client.analyze_symptom(message_data.content)

            # ML 결과 처리
            if ml_result and "disease_classifications" in ml_result:
                diseases = ml_result["disease_classifications"]
                if diseases:
                    # 가장 높은 확률의 질병 선택
                    top_disease = diseases[0]
                    disease_id = top_disease.get("disease_id")
                    confidence = top_disease.get("score", 0)  # score로 변경

                    # 질병 정보 조회
                    from app.models.medical import Disease

                    disease = db.query(Disease).filter(Disease.id == disease_id).first()

                    if disease:
                        # 질병 정보를 포함한 봇 응답 생성
                        bot_content = f"분석 결과: {disease.name} (신뢰도: {confidence:.1%})\n\n{disease.description}"

                        # 병원 추천 결과 처리
                        hospital_result = ml_result.get("hospital_recommendations")
                        if hospital_result:
                            from app.services.hospital_recommendation_service import (
                                HospitalRecommendationService,
                            )

                            try:
                                hospital_recommendations = (
                                    HospitalRecommendationService.recommend_hospitals(
                                        db, user_uuid, disease_id, limit=3
                                    )
                                )

                                if hospital_recommendations:
                                    hospital_names = [
                                        h.name for h in hospital_recommendations
                                    ]
                                    bot_content += (
                                        f"\n\n추천 병원: {', '.join(hospital_names)}"
                                    )

                            except Exception as e:
                                logger.warning(f"병원 추천 영속화 실패(무시): {e}")
                else:
                    bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."
            else:
                bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."

        except Exception as e:
            logger.error(f"ML 분석 중 오류: {str(e)}")
            bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."

        # 봇 메시지 저장
        bot_message = ChatService.create_chat_message(db, room_id, "BOT", bot_content)

        return ChatResponse(message=user_message, bot_response=bot_message)

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
    """채팅방 삭제"""
    try:
        # 사용자가 해당 채팅방에 접근 권한이 있는지 확인
        user_uuid = UUID(str(current_user.id))
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room or chat_room.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 채팅방에 접근할 권한이 없습니다.",
            )

        ChatService.delete_chat_room(db, room_id)
        return {"message": "채팅방이 성공적으로 삭제되었습니다."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채팅방 삭제 중 오류가 발생했습니다: {str(e)}",
        )


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """WebSocket 채팅 엔드포인트"""
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

        # 채팅방 권한 확인
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room or chat_room.user_id != user_id:
            logger.warning(
                f"WebSocket connection rejected: No access to room {room_id} for user {user_id}"
            )
            await websocket.close(code=1008, reason="Access denied")
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

                message_content = data.get("content", "")
                if not message_content:
                    continue

                # 사용자 메시지 저장
                user_message = ChatService.create_chat_message(
                    db, room_id, "USER", message_content
                )

                # 사용자 메시지 전송
                await websocket.send_json(
                    {
                        "type": "user_message",
                        "message": {
                            "id": user_message.id,
                            "content": user_message.content,
                            "message_type": user_message.message_type,
                            "created_at": user_message.created_at.isoformat(),
                        },
                        "room_id": room_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # ML 서비스를 통한 증상 분석
                bot_content = "분석 중입니다..."

                # 먼저 "분석 중" 메시지 저장 및 전송
                analyzing_message = ChatService.create_chat_message(
                    db, room_id, "BOT", bot_content
                )

                await websocket.send_json(
                    {
                        "type": "bot_message",
                        "message": {
                            "id": analyzing_message.id,
                            "content": analyzing_message.content,
                            "message_type": analyzing_message.message_type,
                            "created_at": analyzing_message.created_at.isoformat(),
                        },
                        "room_id": room_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                try:
                    # ML 서비스 호출
                    ml_result = await ml_client.analyze_symptom(message_content)

                    # ML 결과 처리
                    if ml_result and "disease_classifications" in ml_result:
                        diseases = ml_result["disease_classifications"]
                        if diseases:
                            # 가장 높은 확률의 질병 선택
                            top_disease = diseases[0]
                            disease_id = top_disease.get("disease_id")
                            confidence = top_disease.get("score", 0)  # score로 변경

                            # 질병 정보 조회
                            from app.models.medical import Disease

                            disease = (
                                db.query(Disease)
                                .filter(Disease.id == disease_id)
                                .first()
                            )

                            if disease:
                                # 질병 정보를 포함한 봇 응답 생성
                                bot_content = f"분석 결과: {disease.name} (신뢰도: {confidence:.1%})\n\n{disease.description}"

                                # 병원 추천 결과 처리
                                hospital_result = ml_result.get(
                                    "hospital_recommendations"
                                )
                                if hospital_result:
                                    from app.services.hospital_recommendation_service import (
                                        HospitalRecommendationService,
                                    )

                                    try:
                                        hospital_recommendations = HospitalRecommendationService.recommend_hospitals(
                                            db, user_id, disease_id, limit=3
                                        )

                                        if hospital_recommendations:
                                            hospital_names = [
                                                h.name for h in hospital_recommendations
                                            ]
                                            bot_content += f"\n\n추천 병원: {', '.join(hospital_names)}"

                                    except Exception as e:
                                        logger.warning(
                                            f"병원 추천 영속화 실패(무시): {e}"
                                        )
                        else:
                            bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."
                    else:
                        bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."

                except Exception as e:
                    logger.error(f"ML 분석 중 오류: {str(e)}")
                    bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."

                # 최종 봇 메시지 저장 및 전송
                bot_message = ChatService.create_chat_message(
                    db, room_id, "BOT", bot_content
                )

                await websocket.send_json(
                    {
                        "type": "bot_message",
                        "message": {
                            "id": bot_message.id,
                            "content": bot_message.content,
                            "message_type": bot_message.message_type,
                            "created_at": bot_message.created_at.isoformat(),
                        },
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
