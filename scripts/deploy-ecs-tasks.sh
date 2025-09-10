#!/bin/bash

# ECS 태스크 정의 배포 스크립트
# 환경변수를 실제 값으로 치환하여 AWS에 등록

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 필수 환경변수 확인
check_env_vars() {
    local required_vars=(
        "AWS_ACCOUNT_ID"
        "ECR_REGISTRY"
        "ECR_API_SERVICE"
        "ECR_ML_SERVICE"
        "ECR_NGINX"
        "DB_HOST"
        "DB_PASSWORD"
        "SECRET_KEY"
        "DEBUG"
        "ALLOWED_HOSTS_STRING"
        "KAKAO_REST_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo -e "${RED}❌ 환경변수 $var가 설정되지 않았습니다${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ 모든 필수 환경변수가 설정되었습니다${NC}"
}

# 태스크 정의 치환 및 등록
deploy_task_definition() {
    local template_file=$1
    local task_family=$2
    
    echo -e "${YELLOW}📋 $task_family 태스크 정의 배포 중...${NC}"
    
    # 환경변수 치환
    local temp_file=$(mktemp)
    envsubst < "$template_file" > "$temp_file"
    
    # AWS CLI로 태스크 정의 등록
    aws ecs register-task-definition \
        --cli-input-json file://"$temp_file" \
        --region ap-northeast-2
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ $task_family 태스크 정의 등록 완료${NC}"
    else
        echo -e "${RED}❌ $task_family 태스크 정의 등록 실패${NC}"
        exit 1
    fi
    
    # 임시 파일 정리
    rm "$temp_file"
}

# 메인 실행
main() {
    echo -e "${YELLOW}🚀 ECS 태스크 정의 배포 시작${NC}"
    
    # 환경변수 확인
    check_env_vars
    
    # 태스크 정의들 배포
    deploy_task_definition "ecs-task-definitions/api-service-cpu.json" "medic-api-service"
    deploy_task_definition "ecs-task-definitions/ml-service-gpu.json" "medic-ml-service" 
    deploy_task_definition "ecs-task-definitions/nginx-service-fargate.json" "medic-nginx-service"
    
    echo -e "${GREEN}🎉 모든 태스크 정의 배포 완료!${NC}"
}

# 스크립트 실행
main "$@"
