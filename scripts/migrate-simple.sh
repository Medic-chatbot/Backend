#!/bin/bash

# 간단한 Alembic 마이그레이션 스크립트 (volumes 동기화 사용)
# 사용법: ./scripts/migrate-simple.sh "마이그레이션 메시지"

set -e

# 인자 확인
if [ -z "$1" ]; then
    echo "사용법: $0 \"마이그레이션 메시지\""
    echo "예시: $0 \"Add user profile fields\""
    exit 1
fi

MESSAGE="$1"

echo "🚀 Alembic 마이그레이션 시작..."
echo "메시지: $MESSAGE"
echo

# 1. Docker 컨테이너가 실행 중인지 확인
echo "📋 Docker 컨테이너 상태 확인..."
if ! docker-compose ps | grep -q "backend-api-1.*Up"; then
    echo "❌ API 컨테이너가 실행되지 않았습니다."
    echo "💡 Docker를 재시작합니다..."
    docker-compose down && docker-compose up -d
    
    # 컨테이너가 완전히 시작될 때까지 대기
    echo "⏳ 컨테이너 시작 대기 중..."
    sleep 5
fi

# 2. 마이그레이션 생성 및 적용
echo "🔄 마이그레이션 파일 생성 중..."
docker-compose exec api alembic revision --autogenerate -m "$MESSAGE"

echo
echo "🔧 마이그레이션 데이터베이스에 적용 중..."
docker-compose exec api alembic upgrade head

# 3. 현재 상태 확인
echo
echo "📊 현재 마이그레이션 상태:"
docker-compose exec api alembic current

echo
echo "🎉 마이그레이션 완료!"
echo "💡 volumes 동기화로 인해 로컬에 자동으로 파일이 동기화되었습니다."
echo "📁 확인: ./alembic/versions/ 디렉토리"
echo "💡 Git에 커밋하는 것을 잊지 마세요!"
