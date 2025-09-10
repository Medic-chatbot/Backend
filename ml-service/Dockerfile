# BERT 모델 서비스용 Dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

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

# Python dependencies (torch 제외 - base 이미지에 이미 설치됨)
COPY ml-service/requirements-ml.txt .
# JPype을 먼저 설치 (Java와 연동)
RUN pip install --no-cache-dir jpype1
# torch 제외하고 설치 (base 이미지에 이미 설치됨)
RUN sed '/^torch/d' requirements-ml.txt > requirements-ml-no-torch.txt && \
    pip install --no-cache-dir -r requirements-ml-no-torch.txt

# 애플리케이션 코드 복사
COPY ml-service/main.py .

# Hugging Face 모델 캐시 디렉토리
RUN mkdir -p /app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

# KoNLPy 데이터 캐시 디렉토리
RUN mkdir -p /app/konlpy_data
ENV KONLPY_DATA_PATH=/app/konlpy_data

# 환경 변수 설정
ENV MODEL_NAME=unu-dev/krbert_ms2d_v1
ENV DEVICE=cuda
ENV API_SERVICE_URL=http://api-service:8000

# 포트 노출
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]