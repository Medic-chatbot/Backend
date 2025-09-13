# BERT 모델 서비스용 Dockerfile
FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-runtime

WORKDIR /app

# 시스템 dependencies (KoNLPy 및 한국어 처리를 위한 Java 설치)
RUN apt-get update && apt-get install -y \
    curl \
    openjdk-11-jdk \
    g++ \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Java 환경 변수 설정
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Python dependencies
COPY ml-service/requirements-ml.txt .
# JPype을 먼저 설치 (Java와 연동)
RUN pip install --no-cache-dir jpype1
# PyTorch가 이미 베이스 이미지에 설치되어 있으므로 requirements만 설치
RUN pip install --no-cache-dir -r requirements-ml.txt

# 애플리케이션 코드 복사
COPY ml-service/main.py .

# Hugging Face 모델 캐시 디렉토리
RUN mkdir -p /app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

# KoNLPy 데이터 캐시 디렉토리
RUN mkdir -p /app/konlpy_data
ENV KONLPY_DATA_PATH=/app/konlpy_data

# 환경 변수 설정
ENV MODEL_NAME=unu-dev/krbert_morph_s2d_fin_0.1
ENV DEVICE=cuda
ENV API_SERVICE_URL=http://api-service:8000

# 포트 노출
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
