FROM nginx:alpine

# nginx.conf 템플릿 복사
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# 환경변수 기본값 설정
ENV API_SERVICE_HOST=api
ENV ML_SERVICE_HOST=ml-service

# 80 포트 노출
EXPOSE 80

# envsubst로 환경변수 치환 후 nginx 실행
CMD ["nginx", "-g", "daemon off;"]
