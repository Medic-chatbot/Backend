# 의료 챗봇 서비스 테이블 명세서

## 📋 개요
이 문서는 프론트엔드 개발자를 위한 데이터베이스 테이블 명세서입니다.
API 개발 시 참고할 수 있는 테이블 구조와 관계를 정리했습니다.

---

## 👤 사용자 관리

### users (사용자 테이블)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 사용자 고유 식별자 |
| email | VARCHAR | UNIQUE, NOT NULL | 로그인용 이메일 |
| password_hash | VARCHAR | NOT NULL | 암호화된 비밀번호 |
| nickname | VARCHAR | NOT NULL | 사용자 닉네임 |
| age | INTEGER | NOT NULL | 사용자 나이 |
| gender | VARCHAR | NOT NULL | 성별 ('MALE', 'FEMALE', 'OTHER') |
| last_login_at | TIMESTAMP | - | 마지막 로그인 시간 |
| created_at | TIMESTAMP | DEFAULT NOW | 계정 생성일 |
| updated_at | TIMESTAMP | DEFAULT NOW | 정보 수정일 |
| deleted_at | TIMESTAMP | NULLABLE | 계정 삭제일 (soft delete) |

**API 사용 예시:**
- 회원가입: `email`, `password`, `nickname`, `age`, `gender` 필수
- 프로필 조회: `id`, `email`, `nickname`, `age`, `gender`, `last_login_at` 반환
- 로그인: `email`, `password` 입력

### user_locations (사용자 위치 정보)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 위치 정보 식별자 |
| user_id | UUID | FK(users), NOT NULL | 사용자 ID (1:1 관계) |
| latitude | FLOAT | NOT NULL | 위도 |
| longitude | FLOAT | NOT NULL | 경도 |
| address | TEXT | - | 주소 텍스트 |
| is_current | BOOLEAN | DEFAULT TRUE | 현재 위치 여부 |

**API 사용 예시:**
- 위치 업데이트: `latitude`, `longitude`, `address` 입력
- 병원 추천 시 거리 계산에 사용

---

## 💬 채팅 시스템

### chat_rooms (채팅방 테이블)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 채팅방 식별자 |
| user_id | UUID | FK(users), NOT NULL | 채팅방 소유자 (1:N 관계) |
| title | VARCHAR | NOT NULL | 채팅방 제목 |
| is_active | BOOLEAN | DEFAULT TRUE | 채팅방 활성 상태 |
| created_at | TIMESTAMP | DEFAULT NOW | 채팅방 생성일 |
| updated_at | TIMESTAMP | DEFAULT NOW | 채팅방 수정일 |
| deleted_at | TIMESTAMP | NULLABLE | 채팅방 삭제일 |

**API 사용 예시:**
- 채팅방 목록: `id`, `title`, `is_active`, `created_at` 반환
- 새 채팅방 생성: `title` 입력 (user_id는 토큰에서 추출)

### chat_messages (채팅 메시지)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 메시지 식별자 |
| chat_room_id | UUID | FK(chat_rooms), NOT NULL | 채팅방 ID (1:N 관계) |
| message_type | VARCHAR | NOT NULL | 메시지 타입 ('USER', 'BOT') |
| content | TEXT | NOT NULL | 메시지 내용 |
| created_at | TIMESTAMP | DEFAULT NOW | 메시지 전송일 |

**API 사용 예시:**
- 메시지 전송: `content` 입력 (`message_type`은 'USER'로 자동 설정)
- 메시지 목록: `id`, `message_type`, `content`, `created_at` 반환

---

## 🏥 의료 데이터

### diseases (질환 정보)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 질환 식별자 |
| name | VARCHAR | UNIQUE, NOT NULL | 질환명 |
| description | TEXT | - | 질환 설명 |

**API 사용 예시:**
- 질환 목록 조회: `id`, `name`, `description` 반환
- 총 22개의 질환 데이터

### symptoms (증상 정보)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 증상 식별자 |
| name | VARCHAR | UNIQUE, NOT NULL | 증상명 |
| description | TEXT | - | 증상 설명 |

**API 사용 예시:**
- 증상 자동완성: `name` 기반 검색
- 증상 상세 정보: `id`, `name`, `description` 반환

### symptom_synonyms (증상 동의어)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 동의어 식별자 |
| symptom_id | UUID | FK(symptoms), NOT NULL | 연관 증상 ID |
| synonym | VARCHAR | UNIQUE, NOT NULL | 동의어/유사어 |
| source | VARCHAR | - | 출처 ('USER_INPUT', 'PREDEFINED') |
| frequency | INTEGER | DEFAULT 1 | 사용 빈도 |

---

## 🏥 병원 데이터

### hospitals (병원 정보)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 병원 식별자 |
| name | VARCHAR | NOT NULL | 병원명 |
| address | TEXT | NOT NULL | 병원 주소 |
| latitude | FLOAT | NOT NULL | 위도 |
| longitude | FLOAT | NOT NULL | 경도 |
| type | VARCHAR | - | 병원 유형 (종합병원, 의원 등) |
| department | VARCHAR | - | 주요 진료과목 |
| phone | VARCHAR | - | 전화번호 |
| website | VARCHAR | - | 웹사이트 |
| operating_hours | JSON | - | 운영시간 정보 |

**API 사용 예시:**
- 병원 검색: `name`, `address`, `type`, `department` 기반 필터링
- 병원 상세 정보: 모든 필드 반환
- 거리 계산: `latitude`, `longitude` 사용

### medical_equipment_categories (의료장비 대분류)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 장비 대분류 식별자 |
| name | VARCHAR | UNIQUE, NOT NULL | 대분류명 |
| description | TEXT | - | 설명 |

### medical_equipment_subcategories (의료장비 세분류)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 장비 세분류 식별자 |
| category_id | UUID | FK(categories), NOT NULL | 상위 대분류 ID |
| name | VARCHAR | NOT NULL | 세분류명 |
| description | TEXT | - | 설명 |

---

## 🔍 분석 시스템

### symptom_analysis (증상 분석 결과)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 분석 결과 식별자 |
| chat_message_id | UUID | FK(chat_messages), NOT NULL | 분석 대상 메시지 (1:1) |
| predicted_disease_id | UUID | FK(diseases) | BERT 예측 질환 |
| confidence_score | FLOAT | - | 예측 신뢰도 |
| raw_bert_output | JSON | - | BERT 원본 출력 |
| created_at | TIMESTAMP | DEFAULT NOW | 분석 수행일 |

**API 사용 예시:**
- 분석 결과 조회: `predicted_disease_id`, `confidence_score` 반환
- 상세 분석 정보: `raw_bert_output` 포함

### analysis_symptoms (분석된 증상들)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 분석 증상 식별자 |
| symptom_analysis_id | UUID | FK(symptom_analysis), NOT NULL | 분석 결과 ID |
| symptom_id | UUID | FK(symptoms), NOT NULL | 감지된 증상 ID |
| confidence_score | FLOAT | DEFAULT 1.0 | 증상 감지 신뢰도 |

### hospital_recommendations (병원 추천 결과)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 추천 결과 식별자 |
| symptom_analysis_id | UUID | FK(symptom_analysis), NOT NULL | 분석 결과 ID |
| hospital_id | UUID | FK(hospitals), NOT NULL | 추천 병원 ID |
| distance | FLOAT | NOT NULL | 거리 (km) |
| recommended_reason | TEXT | - | 추천 이유 |
| recommendation_score | FLOAT | - | 추천 점수 |

**API 사용 예시:**
- 병원 추천 목록: `hospital_id`, `distance`, `recommendation_score` 기준 정렬
- 추천 이유 표시: `recommended_reason` 활용

---

## 📊 학습 시스템

### learning_data (학습 데이터)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 학습 데이터 식별자 |
| original_text | TEXT | NOT NULL | 사용자 원본 입력 |
| verified | BOOLEAN | DEFAULT FALSE | 검증 여부 |
| verification_date | TIMESTAMP | - | 검증 완료일 |
| verifier_id | UUID | FK(users) | 검증자 ID |

---

## 🔗 주요 관계 정리

### 일대일 (1:1) 관계
- `users` ↔ `user_locations`: 사용자별 현재 위치
- `chat_messages` ↔ `symptom_analysis`: 메시지별 분석 결과

### 일대다 (1:N) 관계
- `users` → `chat_rooms`: 사용자별 여러 채팅방
- `chat_rooms` → `chat_messages`: 채팅방별 여러 메시지
- `symptoms` → `symptom_synonyms`: 증상별 여러 동의어

### 다대다 (M:N) 관계
- `diseases` ↔ `symptoms`: 질환-증상 매핑
- `hospitals` ↔ `medical_equipment_subcategories`: 병원-장비 보유
- `symptom_analysis` ↔ `symptoms`: 분석-감지증상
- `symptom_analysis` ↔ `hospitals`: 분석-추천병원

---

## 🎯 프론트엔드 개발 팁

### 1. 페이지네이션
- `created_at` 기준으로 정렬
- `deleted_at IS NULL` 조건으로 soft delete 처리

### 2. 실시간 업데이트
- `chat_messages`: WebSocket으로 실시간 메시지
- `symptom_analysis`: 분석 진행 상태 표시

### 3. 검색 기능
- `hospitals`: 이름, 주소, 진료과목 기반 검색
- `symptoms`: 자동완성 기능
- `symptom_synonyms`: 유사어 검색 지원

### 4. 거리 계산
- 사용자 위치(`user_locations`)와 병원 위치(`hospitals`) 간 거리
- Haversine 공식 또는 서버 API 활용

### 5. 상태 관리
- `is_active`: 채팅방 활성/비활성
- `is_operational`: 의료장비 운영 상태
- `verified`: 데이터 검증 상태
