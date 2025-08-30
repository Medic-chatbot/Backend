"""
API 테스트 스크립트
"""

import requests
import json

# 로컬 서버 URL
BASE_URL = "http://localhost:8000"

def test_health():
    """헬스체크 테스트"""
    print("=== 헬스체크 테스트 ===")
    
    # 기본 헬스체크
    response = requests.get(f"{BASE_URL}/health")
    print(f"기본 헬스체크: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 상세 헬스체크
    response = requests.get(f"{BASE_URL}/api/v1/health/detailed")
    print(f"\n상세 헬스체크: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_auth():
    """인증 테스트"""
    print("\n=== 인증 테스트 ===")
    
    # 회원가입 테스트
    register_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "nickname": "새로운사용자",
        "age": 25,
        "gender": "MALE"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    print(f"회원가입: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 로그인 테스트
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"\n로그인: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_chat():
    """채팅 테스트"""
    print("\n=== 채팅 테스트 ===")
    
    # 채팅방 목록 조회
    response = requests.get(f"{BASE_URL}/api/v1/chat/rooms")
    print(f"채팅방 목록: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 새 채팅방 생성
    room_data = {"title": "테스트 채팅방"}
    response = requests.post(f"{BASE_URL}/api/v1/chat/rooms", json=room_data)
    print(f"\n채팅방 생성: {response.status_code}")
    room_response = response.json()
    print(json.dumps(room_response, indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        room_id = room_response["id"]
        
        # 메시지 전송
        message_data = {"content": "안녕하세요, 두통이 심해서 문의드려요."}
        response = requests.post(f"{BASE_URL}/api/v1/chat/rooms/{room_id}/messages", json=message_data)
        print(f"\n메시지 전송: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    try:
        test_health()
        test_auth()
        test_chat()
    except requests.exceptions.ConnectionError:
        print("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        print("서버 실행: python -m uvicorn app.main:app --reload")
