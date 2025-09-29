"""
채팅 관련 서비스 로직
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from app.models.chat import ChatMessage, ChatRoom
from app.models.medical import Disease
from app.services.medical_service import MedicalService
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class ChatService:
    """채팅 관련 비즈니스 로직"""

    @staticmethod
    def get_chat_room(db: Session, room_id: int) -> Optional[ChatRoom]:
        """채팅방 조회"""
        return (
            db.query(ChatRoom)
            .options(joinedload(ChatRoom.final_disease))
            .filter(ChatRoom.id == room_id)
            .first()
        )

    @staticmethod
    def create_chat_room(db: Session, user_id: UUID, title: str) -> ChatRoom:
        """새 채팅방 생성"""
        chat_room = ChatRoom(user_id=user_id, title=title, is_active=True)

        db.add(chat_room)
        db.commit()
        db.refresh(chat_room)

        return chat_room

    @staticmethod
    def create_chat_message(
        db: Session, chat_room_id: int, message_type: str, content: str
    ) -> ChatMessage:
        """채팅 메시지 생성"""
        message = ChatMessage(
            chat_room_id=chat_room_id,
            message_type=message_type,  # USER, BOT
            content=content,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def update_chat_room_final_disease(
        db: Session, room_id: int, disease_id: int
    ) -> Optional[ChatRoom]:
        """채팅방의 최종 질환 업데이트"""
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            return None

        setattr(chat_room, "final_disease_id", disease_id)
        db.commit()
        db.refresh(chat_room)

        return chat_room

    @staticmethod
    def get_chat_room_with_final_diagnosis(
        db: Session, room_id: int
    ) -> Optional[Tuple[ChatRoom, Optional[Disease], Optional[List]]]:
        """채팅방과 최종 진단 정보 조회"""
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            return None

        final_disease = None
        departments = None

        if chat_room.final_disease_id:
            final_disease = MedicalService.get_disease_by_id(
                db, chat_room.final_disease_id
            )
            if final_disease:
                departments = MedicalService.get_departments_by_disease(
                    db, chat_room.final_disease_id
                )

        return chat_room, final_disease, departments

    @staticmethod
    def get_user_chat_rooms(db: Session, user_id: UUID) -> List[ChatRoom]:
        """사용자의 채팅방 목록 조회"""
        return (
            db.query(ChatRoom)
            .filter(ChatRoom.user_id == user_id)
            .filter(ChatRoom.is_active == True)
            .options(joinedload(ChatRoom.final_disease))
            .order_by(ChatRoom.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_recent_user_messages(
        db: Session, room_id: int, limit: int = 5
    ) -> List[ChatMessage]:
        """최근 사용자 메시지들 조회 (시간순 정렬)"""
        return (
            db.query(ChatMessage)
            .filter(
                ChatMessage.chat_room_id == room_id, ChatMessage.message_type == "USER"
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_chat_messages(
        db: Session, room_id: int, limit: int = 50
    ) -> List[ChatMessage]:
        """채팅방의 메시지 목록 조회"""
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_room_id == room_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def deactivate_chat_room(db: Session, room_id: int) -> bool:
        """채팅방 비활성화"""
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            return False

        setattr(chat_room, "is_active", False)
        db.commit()

        return True

    @staticmethod
    def get_chat_room_by_id(db: Session, room_id: int) -> Optional[ChatRoom]:
        """채팅방 ID로 조회 (별칭 메서드)"""
        return ChatService.get_chat_room(db, room_id)

    @staticmethod
    def delete_chat_room(db: Session, room_id: int) -> bool:
        """채팅방 삭제 (비활성화)"""
        return ChatService.deactivate_chat_room(db, room_id)

    @staticmethod
    def start_new_symptom_session(db: Session, room_id: int, message_id: int) -> bool:
        """새로운 증상 세션 시작"""
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room:
            return False

        setattr(chat_room, "current_session_start_message_id", message_id)
        db.commit()
        return True

    @staticmethod
    def get_session_user_messages(
        db: Session, room_id: int, limit: int = 10
    ) -> List[ChatMessage]:
        """현재 세션의 사용자 메시지들 조회"""
        chat_room = ChatService.get_chat_room(db, room_id)
        if not chat_room or not chat_room.current_session_start_message_id:
            return []

        return (
            db.query(ChatMessage)
            .filter(
                ChatMessage.chat_room_id == room_id,
                ChatMessage.message_type == "USER",
                ChatMessage.id >= chat_room.current_session_start_message_id,
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )
