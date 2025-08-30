"""
애플리케이션 설정
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 기본 설정
    PROJECT_NAME: str = "Medical Chatbot API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 데이터베이스 설정
    DATABASE_URL: Optional[str] = None

    # Redis 설정
    REDIS_URL: Optional[str] = None

    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS 설정
    ALLOWED_HOSTS: list = [
        "https://v0-medical-chatbot-ui-xi.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # ML 서비스 설정
    ML_SERVICE_URL: str = "http://ml:8001"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스
settings = Settings()
