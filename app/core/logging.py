"""
로깅 설정 모듈
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    애플리케이션 로깅 설정

    Args:
        log_level: 로그 레벨 (debug, info, warning, error)
    """
    level = log_level or ("DEBUG" if settings.DEBUG else "INFO")

    # 로그 포맷 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 기본 로깅 설정
    logging.basicConfig(
        level=getattr(logging, level.upper()), format=log_format, stream=sys.stdout
    )

    # uvicorn 로그 레벨 조정
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # sqlalchemy 로그 레벨 조정 (너무 많은 SQL 로그 방지)
    if not settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# 애플리케이션 로거 생성
def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 생성"""
    return logging.getLogger(name)


# 주요 모듈별 로거들
api_logger = get_logger("medic.api")
db_logger = get_logger("medic.database")
ml_logger = get_logger("medic.ml")
auth_logger = get_logger("medic.auth")
