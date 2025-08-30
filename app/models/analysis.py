"""
분석 시스템 관련 모델
"""

from sqlalchemy import Column, Float, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, UUIDMixin


class SymptomAnalysis(Base, UUIDMixin, TimestampMixin):
    """증상 분석 결과 테이블"""
    
    __tablename__ = "symptom_analysis"
    
    chat_message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False, unique=True, index=True)
    predicted_disease_id = Column(UUID(as_uuid=True), ForeignKey("diseases.id"), nullable=True, index=True)
    confidence_score = Column(Float, nullable=True)
    raw_bert_output = Column(JSON, nullable=True)
    
    # 관계 설정
    chat_message = relationship("ChatMessage", back_populates="symptom_analysis")
    predicted_disease = relationship("Disease", back_populates="symptom_analyses")
    analysis_symptoms = relationship("AnalysisSymptom", back_populates="symptom_analysis")
    hospital_recommendations = relationship("HospitalRecommendation", back_populates="symptom_analysis")


class AnalysisSymptom(Base, UUIDMixin, TimestampMixin):
    """분석된 증상들 테이블"""
    
    __tablename__ = "analysis_symptoms"
    
    symptom_analysis_id = Column(UUID(as_uuid=True), ForeignKey("symptom_analysis.id"), nullable=False, index=True)
    symptom_id = Column(UUID(as_uuid=True), ForeignKey("symptoms.id"), nullable=False, index=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    
    # 관계 설정
    symptom_analysis = relationship("SymptomAnalysis", back_populates="analysis_symptoms")
    symptom = relationship("Symptom", back_populates="analysis_symptoms")


class HospitalRecommendation(Base, UUIDMixin, TimestampMixin):
    """병원 추천 결과 테이블"""
    
    __tablename__ = "hospital_recommendations"
    
    symptom_analysis_id = Column(UUID(as_uuid=True), ForeignKey("symptom_analysis.id"), nullable=False, index=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False, index=True)
    distance = Column(Float, nullable=False)
    recommended_reason = Column(Text, nullable=True)
    recommendation_score = Column(Float, nullable=True)
    
    # 관계 설정
    symptom_analysis = relationship("SymptomAnalysis", back_populates="hospital_recommendations")
    hospital = relationship("Hospital", back_populates="hospital_recommendations")
