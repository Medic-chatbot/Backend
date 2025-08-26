# Medic Chatbot Backend

의료 챗봇 서비스의 백엔드 시스템입니다. 사용자의 증상을 자연어로 입력받아 BERT 모델을 통해 분석하고, 적절한 진단과 병원을 추천하는 서비스를 제공합니다.

## 기술 스택

- **프레임워크**: FastAPI
- **데이터베이스**: PostgreSQL
- **캐시**: Redis
- **ML 모델**: BERT, LLM
- **컨테이너화**: Docker
- **클라우드**: AWS (ECR, ECS, Fargate)

## 프로젝트 구조

```
Backend/
├── app/
│   ├── api/
│   │   ├── v1/             # API 버전 1
│   │   └── endpoints/      # API 엔드포인트
│   ├── core/               # 핵심 설정 및 상수
│   ├── db/                 # 데이터베이스 모델 및 설정
│   ├── models/            # Pydantic 모델
│   ├── schemas/           # API 스키마
│   ├── services/          # 비즈니스 로직
│   │   ├── ml/            # BERT & LLM 서비스
│   │   └── hospital/      # 병원 추천 서비스
│   └── utils/             # 유틸리티 함수
├── tests/
│   ├── unit/              # 단위 테스트
│   └── integration/       # 통합 테스트
└── docs/                  # 문서
```

## 도커 구성

### 서비스 구조

프로젝트는 MSA(Microservice Architecture) 방식으로 구성되어 있으며, 다음과 같은 서비스들로 구성됩니다:

1. **API 서비스** (Dockerfile)
   - FastAPI 기반 메인 애플리케이션
   - 사용자 요청 처리 및 응답 생성
   - 포트: 8000

2. **ML 서비스** (Dockerfile.ml)
   - BERT 모델을 통한 증상 분석
   - LLM API를 통한 응답 생성
   - GPU 지원
   - 포트: 8001

3. **데이터베이스** (PostgreSQL)
   - 병원 정보 저장
   - 사용자 데이터 관리
   - 포트: 5432

4. **캐시** (Redis)
   - 세션 관리
   - 응답 캐싱
   - 포트: 6379

### 도커 설정 파일

- **docker-compose.yml**: 전체 서비스 오케스트레이션
- **Dockerfile**: API 서비스 컨테이너 설정
- **Dockerfile.ml**: ML 서비스 컨테이너 설정
- **.dockerignore**: 도커 빌드 제외 파일 설정

## 개발 환경 설정

1. 저장소 클론
```bash
git clone https://github.com/Medic-chatbot/Backend.git
cd Backend
```

2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 적절히 수정
```

3. 도커 컨테이너 실행
```bash
docker-compose up -d
```

4. API 문서 확인
```
http://localhost:8000/docs
```

## 배포 환경

- AWS ECR: 도커 이미지 저장소
- AWS ECS (Fargate): 컨테이너 오케스트레이션
- GitHub Actions: CI/CD 파이프라인

## 브랜치 전략

- `main`: 프로덕션 환경 브랜치
- `develop`: 개발 환경 브랜치
- `feature/*`: 새로운 기능 개발
- `hotfix/*`: 긴급 버그 수정
- `release/*`: 릴리스 준비

## 기여 방법

1. `develop` 브랜치에서 새로운 feature 브랜치를 생성
2. 변경사항 작업 및 커밋
3. Pull Request 생성
4. 코드 리뷰 후 승인되면 병합

## 라이센스

MIT License
