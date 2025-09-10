# Alembic 마이그레이션 자동화 스크립트

## 🎯 목적
모델 변경 후 Alembic 마이그레이션을 자동으로 생성하고 적용하며, 로컬에 파일을 동기화하는 과정을 자동화합니다.

## 📋 사용 가능한 스크립트

### 1. `migrate-simple.sh` (권장)
Docker volumes를 사용한 자동 동기화 방식

```bash
# 사용법
./scripts/migrate-simple.sh "마이그레이션 메시지"

# 예시
./scripts/migrate-simple.sh "Add user profile fields"
./scripts/migrate-simple.sh "Update chat room model"
```

**특징:**
- ✅ Docker volumes로 자동 파일 동기화
- ✅ 간단한 명령어
- ✅ Docker 자동 재시작 기능

### 2. `migrate.sh` (수동 복사 방식)
컨테이너에서 로컬로 수동 복사하는 방식

```bash
# 사용법
./scripts/migrate.sh "마이그레이션 메시지"
```

**특징:**
- ✅ 명시적인 파일 복사 과정
- ✅ 상세한 로그 출력
- ⚠️ Docker cp 명령어 사용

## 🔄 개발 워크플로우

### 1. 모델 수정
```python
# app/models/user.py
class User(Base):
    # ... 기존 필드
    new_field = Column(String, nullable=True)  # 새 필드 추가
```

### 2. 마이그레이션 생성 및 적용
```bash
./scripts/migrate-simple.sh "Add new_field to User model"
```

### 3. Git 커밋
```bash
git add alembic/versions/
git commit -m "Add new_field to User model migration"
```

## 📁 파일 구조
```
Backend/
├── alembic/
│   └── versions/           # 마이그레이션 파일들 (로컬-컨테이너 동기화)
│       └── *.py
├── scripts/
│   ├── migrate-simple.sh   # 권장 스크립트
│   ├── migrate.sh         # 수동 복사 스크립트
│   └── README.md          # 이 파일
└── docker-compose.yml     # volumes 설정 포함
```

## ⚙️ Docker Volumes 설정
```yaml
# docker-compose.yml
services:
  api:
    volumes:
      - ./alembic/versions:/app/alembic/versions  # 자동 동기화
```

## 🐛 문제 해결

### Migration 파일이 동기화되지 않는 경우
```bash
# Docker 재시작
docker-compose down && docker-compose up -d
```

### Alembic 상태 확인
```bash
# 현재 버전 확인
docker-compose exec api alembic current

# 히스토리 확인
docker-compose exec api alembic history
```

### 수동으로 파일 복사가 필요한 경우
```bash
# 특정 파일 복사
docker cp backend-api-1:/app/alembic/versions/[파일명] ./alembic/versions/

# 전체 디렉토리 복사
docker cp backend-api-1:/app/alembic/versions/. ./alembic/versions/
```

## 💡 팁

1. **항상 로컬에 migration 파일 유지**: Alembic revision chain을 위해 필수
2. **의미있는 메시지 작성**: 나중에 찾기 쉽도록
3. **Git 커밋 필수**: migration 파일은 버전 관리 대상
4. **모델 변경 후 즉시 migration**: 누락 방지
