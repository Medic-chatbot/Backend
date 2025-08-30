# CUDA 지원을 위한 기본 이미지
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Python 3.9 설치
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /ml

# 의존성 파일 복사
COPY requirements.txt ./

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# ML 관련 추가 의존성 설치
RUN pip install torch transformers sentencepiece

# 애플리케이션 코드 복사
COPY ./app/services/ml ./app/services/ml

# 모델 다운로드 스크립트 실행 (필요한 경우)
# RUN python3 download_models.py

# 환경 변수 설정
ENV PYTHONPATH=/ml
ENV PORT=8001

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
CMD ["uvicorn", "app.services.ml.main:app", "--host", "0.0.0.0", "--port", "8001"]
