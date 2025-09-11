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
            logger.warning(f"Unauthorized access to chat room {room_id} by user {current_user.id}")
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


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """WebSocket 채팅 엔드포인트"""
    # JWT 토큰 검증 및 사용자 인증
    if not token:
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

        except JWTError:
            await websocket.close(code=1008, reason="Token validation failed")
            return

        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
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

                message_type = data.get("type")
                content = data.get("content", "")

                if message_type == "user_message":
                    # 사용자 메시지 처리
                    user_message = ChatService.create_chat_message(
                        db, room_id, "USER", content
                    )

                    # 채팅방의 다른 사용자들에게 브로드캐스트
                    await manager.broadcast_json_to_room(
                        {
                            "type": "user_message",
                            "content": content,
                            "room_id": room_id,
                            "user_id": user_id,
                            "message_id": user_message.id,
                            "timestamp": user_message.created_at.isoformat(),
                        },
                        room_id,
                        exclude_user=str(user_id),
                    )

                    # ML 서비스를 통한 증상 분석
                    bot_content = "분석 중입니다..."

                    # 먼저 "분석 중" 메시지 전송
                    analyzing_message = ChatService.create_chat_message(
                        db, room_id, "BOT", bot_content
                    )

                    await manager.broadcast_json_to_room(
                        {
                            "type": "bot_message",
                            "content": bot_content,
                            "room_id": room_id,
                            "message_id": analyzing_message.id,
                            "timestamp": analyzing_message.created_at.isoformat(),
                            "status": "analyzing",
                        },
                        room_id,
                    )

                    # ML 서비스 호출
                    try:
                        # 1단계: 증상 분석 먼저 수행 (트래픽 감소 및 임계치 분기)
                        # WebSocket 쿼리 파라미터의 토큰을 Bearer로 전달
                        bearer = f"Bearer {token}" if token else None
                        analysis_result = await ml_client.analyze_symptom(
                            text=content,
                            user_id=str(user_id),
                            chat_room_id=room_id,
                            authorization=bearer,
                        )

                        ml_result = None
                        if analysis_result:
                            # 상위 스코어 확인 후 0.8 이상일 때만 병원 추천 포함한 전체 분석 수행
                            top_score = 0.0
                            disease_classifications = analysis_result.get(
                                "disease_classifications", []
                            )
                            if disease_classifications:
                                top_score = (
                                    disease_classifications[0].get("score", 0.0)
                                    if isinstance(disease_classifications[0], dict)
                                    else disease_classifications[0].score
                                )

                            if top_score >= 0.8:
                                ml_result = await ml_client.get_full_analysis(
                                    text=content,
                                    user_id=str(user_id),
                                    chat_room_id=room_id,
                                    authorization=bearer,
                                )
                            else:
                                # 임계치 미만일 경우 전체 분석은 생략하고 분석 결과만 전달
                                ml_result = analysis_result

                        if ml_result:
                            # ML 결과 DB 저장
                            from app.models.medical import Disease
                            from app.models.model_inference import ModelInferenceResult

                            # 증상 분석 결과 추출
                            symptom_analysis = ml_result.get(
                                "symptom_analysis", ml_result
                            )
                            disease_classifications = symptom_analysis.get(
                                "disease_classifications", []
                            )
                            processed_text = symptom_analysis.get(
                                "processed_text", content
                            )

                            # ModelInferenceResult 저장
                            if disease_classifications:
                                # 상위 3개 질병 정보 추출
                                first_disease = (
                                    disease_classifications[0]
                                    if len(disease_classifications) > 0
                                    else None
                                )
                                second_disease = (
                                    disease_classifications[1]
                                    if len(disease_classifications) > 1
                                    else None
                                )
                                third_disease = (
                                    disease_classifications[2]
                                    if len(disease_classifications) > 2
                                    else None
                                )

                                # Disease ID 조회 (label -> id 변환)
                                first_disease_record = None
                                if first_disease:
                                    first_disease_record = (
                                        db.query(Disease)
                                        .filter(
                                            Disease.name.ilike(
                                                f"%{first_disease['label']}%"
                                            )
                                        )
                                        .first()
                                    )

                                if first_disease_record:
                                    inference_result = ModelInferenceResult(
                                        chat_message_id=user_message.id,
                                        input_text=content,
                                        processed_text=processed_text,
                                        first_disease_id=first_disease_record.id,
                                        first_disease_score=first_disease["score"],
                                        second_disease_id=None,  # TODO: 구현 필요
                                        second_disease_score=(
                                            second_disease["score"]
                                            if second_disease
                                            else None
                                        ),
                                        third_disease_id=None,  # TODO: 구현 필요
                                        third_disease_score=(
                                            third_disease["score"]
                                            if third_disease
                                            else None
                                        ),
                                        inference_time=ml_result.get(
                                            "inference_time", 0
                                        ),
                                    )
                                    db.add(inference_result)
                                    db.commit()
                                    db.refresh(inference_result)
                            # 증상 분석 결과 메시지 생성
                            symptom_msg = ml_client.format_disease_results(ml_result)

                            # 병원 추천 결과 메시지 추가
                            hospital_result = ml_result.get("hospital_recommendations")
                            if hospital_result:
                                hospital_msg = ml_client.format_hospital_results(
                                    hospital_result
                                )
                                bot_content = symptom_msg + hospital_msg
                            else:
                                # 임계치 미만이면 추가 정보 요청 메시지 부가
                                bot_content = (
                                    symptom_msg
                                    + "\n\n더 정확한 추천을 위해 증상을 조금만 더 자세히 알려주세요."
                                )
                        else:
                            bot_content = "죄송합니다. 증상 분석 중 오류가 발생했습니다. 다시 시도해주세요."

                    except Exception as e:
                        logger.error(f"[WebSocket] ML 분석 중 오류: {str(e)}")
                        bot_content = "증상에 대해 더 자세히 알려주시면 보다 정확한 정보를 제공해드릴 수 있습니다."

                    # 봇 메시지 저장
                    bot_message = ChatService.create_chat_message(
                        db, room_id, "BOT", bot_content
                    )

                    # 채팅방의 모든 사용자에게 봇 응답 브로드캐스트
                    await manager.broadcast_json_to_room(
                        {
                            "type": "bot_message",
                            "content": bot_content,
                            "room_id": room_id,
                            "message_id": bot_message.id,
                            "timestamp": bot_message.created_at.isoformat(),
                        },
                        room_id,
                    )

            except Exception as e:
                # 메시지 처리 중 오류 발생
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": f"메시지 처리 중 오류가 발생했습니다: {str(e)}",
                        "room_id": room_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(room_id, str(user_id))
        # 연결 해제 메시지를 다른 사용자들에게 알릴 수 있음
        await manager.broadcast_json_to_room(
            {
                "type": "system",
                "content": f"사용자가 채팅방에서 나갔습니다.",
                "room_id": room_id,
                "timestamp": datetime.now().isoformat(),
            },
            room_id,
        )

    except Exception as e:
        await websocket.close(code=1011, reason=f"Internal server error: {str(e)}")


@router.get("/test")
async def test_chat():
    """채팅 API 테스트"""
    return {
        "message": "채팅 API가 정상적으로 작동합니다.",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "available_endpoints": [
            "GET /api/chat/rooms - 채팅방 목록 조회",
            "POST /api/chat/rooms - 새 채팅방 생성",
            "GET /api/chat/rooms/{room_id}/messages - 채팅방 메시지 목록 조회",
            "POST /api/chat/rooms/{room_id}/messages - 메시지 전송 및 봇 응답",
            "DELETE /api/chat/rooms/{room_id} - 채팅방 삭제",
            "WS /api/chat/ws/{room_id} - 실시간 WebSocket 채팅",
        ],
        "status": "websocket_integration_complete",
        "active_connections": len(manager.active_connections),
    }
