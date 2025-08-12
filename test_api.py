#!/usr/bin/env python3
"""
API 테스트 스크립트
"""

import requests
import json

# 서버 URL
BASE_URL = "http://127.0.0.1:8080"

def test_login():
    """데모 로그인 테스트"""
    print("=== 로그인 테스트 ===")
    
    login_data = {
        "email": "demo@jemulpogo.com",
        "password": "demo123"
    }
    
    session = requests.Session()
    
    try:
        response = session.post(f"{BASE_URL}/api/login", json=login_data)
        result = response.json()
        
        if result.get('success'):
            print("✅ 로그인 성공!")
            return session
        else:
            print(f"❌ 로그인 실패: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def test_user_passes(session):
    """사용자 패스 목록 조회 테스트"""
    print("\n=== 사용자 패스 목록 조회 테스트 ===")
    
    try:
        response = session.get(f"{BASE_URL}/api/user/passes")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                passes = result.get('passes', [])
                print(f"✅ 패스 목록 조회 성공! ({len(passes)}개 패스 발견)")
                
                for i, pass_data in enumerate(passes, 1):
                    print(f"\n패스 {i}:")
                    print(f"  - ID: {pass_data.get('pass_id')}")
                    print(f"  - 타입: {pass_data.get('pass_info', {}).get('name', '알 수 없음')}")
                    print(f"  - 생성일: {pass_data.get('created_at')}")
                    print(f"  - 혜택 개수: {pass_data.get('pass_info', {}).get('benefits_count', 0)}개")
                    print(f"  - 테마: {', '.join(pass_data.get('user_input', {}).get('themes', []))}")
                
                return True
            else:
                print(f"❌ 패스 목록 조회 실패: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 패스 목록 조회 오류: {e}")
        return False

def test_pass_generation(session):
    """패스 생성 테스트"""
    print("\n=== 패스 생성 테스트 ===")
    
    pass_data = {
        "themes": ["해산물", "카페"],
        "request": "신선한 해산물과 분위기 좋은 카페를 찾고 있어요",
        "pass_type": "light"
    }
    
    try:
        response = session.post(f"{BASE_URL}/api/generate-pass", json=pass_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 패스 생성 성공!")
                print(f"  - 패스 ID: {result.get('pass_id')}")
                print(f"  - 패스 타입: {result.get('pass_info', {}).get('name')}")
                print(f"  - 혜택 개수: {result.get('pass_info', {}).get('benefits_count')}개")
                print(f"  - 총 가치: {result.get('pass_info', {}).get('total_value')}원")
                return True
            else:
                print(f"❌ 패스 생성 실패: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 패스 생성 오류: {e}")
        return False

def main():
    print("API 테스트를 시작합니다...\n")
    
    # 1. 로그인 테스트
    session = test_login()
    if not session:
        print("로그인에 실패하여 테스트를 중단합니다.")
        return
    
    # 2. 기존 패스 목록 조회 테스트
    test_user_passes(session)
    
    # 3. 새 패스 생성 테스트
    test_pass_generation(session)
    
    # 4. 다시 패스 목록 조회 (새로 생성된 패스 확인)
    print("\n=== 새로 생성된 패스 확인 ===")
    test_user_passes(session)
    
    print("\n🎉 모든 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main()
