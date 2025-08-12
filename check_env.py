# 제물포GO 패스 - 환경 변수 검증 스크립트

import os
from dotenv import load_dotenv
import google.generativeai as genai

def check_environment():
    """환경 설정 상태를 확인하는 함수"""
    print("🔍 제물포GO 패스 - 환경 설정 검증")
    print("=" * 50)
    
    # .env 파일 로드
    load_dotenv()
    
    # 1. .env 파일 존재 확인
    env_file_exists = os.path.exists('.env')
    print(f"📁 .env 파일 존재: {'✅' if env_file_exists else '❌'}")
    
    if not env_file_exists:
        print("   → .env 파일을 생성해주세요!")
        return False
    
    # 2. 필수 환경 변수 확인
    print("\n🔑 환경 변수 확인:")
    
    # Gemini API 키
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key and gemini_api_key != 'YOUR_GEMINI_API_KEY_HERE':
        print(f"   GEMINI_API_KEY: ✅ 설정됨 ({gemini_api_key[:8]}...)")
        api_key_valid = True
    else:
        print(f"   GEMINI_API_KEY: ❌ 설정되지 않음")
        api_key_valid = False
    
    # Gemini 모델
    gemini_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    print(f"   GEMINI_MODEL: ✅ {gemini_model}")
    
    # 포트 설정
    port = os.getenv('PORT', '8080')
    print(f"   PORT: ✅ {port}")
    
    # 3. API 연결 테스트
    print("\n🤖 AI API 연결 테스트:")
    
    if api_key_valid:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel(gemini_model)
            
            # 간단한 테스트 요청
            test_response = model.generate_content("안녕하세요! 간단한 테스트입니다.")
            
            if test_response and test_response.text:
                print("   Gemini AI 연결: ✅ 성공!")
                print(f"   테스트 응답: {test_response.text[:50]}...")
                ai_connection = True
            else:
                print("   Gemini AI 연결: ❌ 응답 없음")
                ai_connection = False
                
        except Exception as e:
            print(f"   Gemini AI 연결: ❌ 실패 ({str(e)[:50]}...)")
            ai_connection = False
    else:
        print("   Gemini AI 연결: ⏭️ API 키 없음 (규칙 기반 추천 사용)")
        ai_connection = False
    
    # 4. 데이터 파일 확인
    print("\n📊 데이터 파일 확인:")
    
    stores_exists = os.path.exists('stores.json')
    benefits_exists = os.path.exists('benefits.json')
    themes_exists = os.path.exists('themes.json')
    
    print(f"   stores.json: {'✅' if stores_exists else '❌'}")
    print(f"   benefits.json: {'✅' if benefits_exists else '❌'}")
    print(f"   themes.json: {'✅' if themes_exists else '❌'}")
    
    # 5. 디렉토리 확인
    print("\n📁 저장 디렉토리 확인:")
    
    save_dir = os.getenv('SAVE_DIR', 'saved_passes')
    qr_dir = os.getenv('QR_CODE_DIR', 'qr_codes')
    
    # 디렉토리가 없으면 생성
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(qr_dir, exist_ok=True)
    
    print(f"   {save_dir}/: ✅ 준비됨")
    print(f"   {qr_dir}/: ✅ 준비됨")
    
    # 6. 의존성 패키지 확인
    print("\n📦 주요 패키지 확인:")
    
    packages = {
        'flask': 'Flask',
        'google.generativeai': 'Google Generative AI',
        'qrcode': 'QR Code',
        'dotenv': 'Python Dotenv',
        'flask_cors': 'Flask CORS'
    }
    
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"   {name}: ✅")
        except ImportError:
            print(f"   {name}: ❌ (pip install {package})")
    
    # 7. 종합 결과
    print("\n" + "=" * 50)
    print("📋 종합 결과:")
    
    if env_file_exists and stores_exists and benefits_exists:
        if api_key_valid and ai_connection:
            print("🎉 완벽한 설정! AI 기능이 모두 활성화됩니다.")
            status = "PERFECT"
        elif api_key_valid:
            print("⚠️  API 연결 문제가 있지만 기본 기능은 동작합니다.")
            status = "PARTIAL"
        else:
            print("⚡ AI 기능 없이 규칙 기반 추천만 동작합니다.")
            status = "BASIC"
    else:
        print("❌ 필수 파일이 누락되었습니다. 설정을 완료해주세요.")
        status = "ERROR"
    
    # 8. 추천 액션
    print("\n💡 추천 액션:")
    
    if status == "PERFECT":
        print("   - python app.py 실행하여 웹 서버 시작")
        print("   - python main.py 실행하여 터미널 모드 테스트")
        
    elif status == "PARTIAL":
        print("   - API 키를 다시 확인해주세요")
        print("   - 네트워크 연결을 확인해주세요")
        print("   - Google AI Studio에서 할당량을 확인해주세요")
        
    elif status == "BASIC":
        print("   - .env 파일에서 GEMINI_API_KEY를 설정해주세요")
        print("   - https://makersuite.google.com/app/apikey에서 API 키 발급")
        print("   - AI 없이도 규칙 기반 추천은 정상 동작합니다")
        
    else:
        print("   - .env 파일을 생성하고 필요한 값들을 설정해주세요")
        print("   - stores.json, benefits.json 파일을 확인해주세요")
        print("   - pip install -r requirements.txt 실행")
    
    return status == "PERFECT" or status == "PARTIAL" or status == "BASIC"

if __name__ == "__main__":
    check_environment()
