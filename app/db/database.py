"""
데이터베이스 설정
"""

import logging
import sys

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 로거 설정
logger = logging.getLogger("database")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# 설정에서 DATABASE_URL 가져오기
DATABASE_URL = settings.DATABASE_URL
logger.debug(f"Connecting to database: {DATABASE_URL}")

# SQLAlchemy 엔진 생성
try:
    engine = create_engine(DATABASE_URL)
    logger.debug("Database engine created successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    raise

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.debug("Database session factory created")

# Base 클래스는 base.py에서 import
# (중복 정의 방지)


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        logger.debug("Creating new database session")
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()
