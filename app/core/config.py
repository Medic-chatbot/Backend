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
    EC2_PUBLIC_IP: str = "13.125.229.157"  # EC2 퍼블릭 IP

    # 데이터베이스 설정
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "medic_db"
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"

    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 URL 생성"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis 설정
    REDIS_URL: Optional[str] = None

    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS 설정
    ALLOWED_HOSTS: list = [
        "https://v0-medical-chatbot-ui-xi.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5173",
    ]

    # ML 서비스 설정
    ML_SERVICE_URL: str = "http://ml:8001"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스
settings = Settings()
