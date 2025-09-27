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
    DEBUG: bool = True  # 모든 로그 출력 (개발/디버깅용)

    # 데이터베이스 설정 (환경변수에서 로딩)
    DB_HOST: str = ""  # .env에서 로드
    DB_PORT: int = 5432  # .env에서 로드
    DB_NAME: str = ""  # .env에서 로드
    DB_USER: str = ""  # .env에서 로드
    DB_PASSWORD: str = ""  # .env에서 로드

    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 URL 생성"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis 설정
    REDIS_URL: Optional[str] = None

    # JWT 설정
    SECRET_KEY: str = ""  # .env에서 로드
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7일 (7 * 24 * 60 = 10080분)

    # CORS 설정 (환경변수에서 로딩, 콤마로 구분)
    ALLOWED_HOSTS_STRING: str = ""  # .env에서 로드

    @property
    def ALLOWED_HOSTS(self) -> list:
        """CORS 허용 호스트 목록 (환경변수에서 콤마 구분으로 로딩)"""
        hosts = self.ALLOWED_HOSTS_STRING.split(",")
        return [host.strip() for host in hosts if host.strip()]

    # 서비스 URL 설정 (환경변수에서 로딩)
    ML_SERVICE_URL: str = "http://ml-service:8001"  # 내부 서비스 직접 통신
    API_SERVICE_URL: str = ""  # .env에서 로드
    ALB_HOST: str = ""  # .env에서 로드

    # 추천 관련 공통 설정(로깅/분기 통일성)
    RECOMMEND_CONFIDENCE_THRESHOLD: float = 0.8  # .env에서 로드
    RECOMMEND_LIMIT: int = 3  # .env에서 로드
    SYMPTOM_HISTORY_UTTERANCES: int = 5  # .env에서 로드

    @property
    def ML_SERVICE_URL_ALB(self) -> str:
        """ALB 경유 ML 서비스 URL (프로덕션용)"""
        return f"http://{self.ALB_HOST}/ml"

    @property
    def API_SERVICE_URL_ALB(self) -> str:
        """ALB 경유 API 서비스 URL (프로덕션용)"""
        return f"http://{self.ALB_HOST}/api"

    # 카카오 API 설정
    KAKAO_REST_API_KEY: Optional[str] = None

    # AWS 관련 설정 (배포용)
    AWS_ACCOUNT_ID: Optional[str] = None
    ECR_REGISTRY: Optional[str] = None
    ECR_API_SERVICE: Optional[str] = None
    ECR_ML_SERVICE: Optional[str] = None
    ECR_NGINX: Optional[str] = None

    # 서비스 호스트 설정 (ECS용)
    API_SERVICE_HOST: Optional[str] = None
    ML_SERVICE_HOST: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 필드 무시


# 설정 인스턴스
settings = Settings()
