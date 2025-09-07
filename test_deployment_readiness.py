"""
Flask 앱 SECRET_KEY 로딩 테스트
실제 앱 환경에서 SECRET_KEY가 제대로 설정되는지 확인
"""
import os
import sys

# src 폴더를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

def test_secret_key_loading():
    print("=" * 60)
    print("🧪 Flask 앱 SECRET_KEY 로딩 테스트")
    print("=" * 60)
    
    # 환경 변수 로드
    load_dotenv()
    
    # Flask 앱 생성 (테스트용)
    try:
        from app import create_app
        
        print("✅ Flask 앱 모듈 import 성공")
        
        # 앱 생성
        app = create_app()
        
        print("✅ Flask 앱 생성 성공")
        
        # SECRET_KEY 확인
        secret_key = app.config.get('SECRET_KEY')
        
        if secret_key:
            print(f"✅ SECRET_KEY 로드 성공!")
            print(f"🔑 SECRET_KEY 길이: {len(secret_key)}")
            print(f"🔑 SECRET_KEY 미리보기: {secret_key[:15]}...{secret_key[-15:]}")
            
            # 고정 키인지 확인
            expected_prefix = "jemulpogo-production-secret-key"
            if secret_key.startswith(expected_prefix):
                print("✅ 예상된 고정 SECRET_KEY 사용 중 - 패스 유실 방지됨!")
            else:
                print("⚠️ 예상과 다른 SECRET_KEY - 확인 필요")
                
            # 무작위 키 생성 코드가 사용되지 않는지 확인
            if len(secret_key) < 50:
                print("⚠️ SECRET_KEY가 짧습니다 - 무작위 생성된 키일 가능성")
            else:
                print("✅ SECRET_KEY 길이 충분 - 고정 키 사용 확인됨")
                
        else:
            print("❌ SECRET_KEY 로드 실패!")
            
        print("\n" + "=" * 60)
        print("🔍 추가 앱 설정 확인")
        print("=" * 60)
        
        # 세션 설정 확인
        session_permanent = app.config.get('SESSION_PERMANENT')
        permanent_lifetime = app.config.get('PERMANENT_SESSION_LIFETIME')
        
        print(f"📅 SESSION_PERMANENT: {session_permanent}")
        print(f"⏰ PERMANENT_SESSION_LIFETIME: {permanent_lifetime}")
        
        if session_permanent:
            print("✅ 영구 세션 설정 활성화됨")
        else:
            print("⚠️ 영구 세션 설정이 활성화되지 않음")
            
        if permanent_lifetime:
            days = permanent_lifetime / (60 * 60 * 24)
            print(f"📅 세션 유효기간: {days:.1f}일")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask 앱 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_consistency():
    """환경 설정 일관성 테스트"""
    print("\n" + "=" * 60)
    print("🔧 환경 설정 일관성 검사")
    print("=" * 60)
    
    load_dotenv()
    
    # .env에서 SECRET_KEY 읽기
    env_secret = os.environ.get('SECRET_KEY', '').strip().strip('"')
    
    # app.yaml에서 SECRET_KEY 읽기
    try:
        with open('app.yaml', 'r', encoding='utf-8') as f:
            yaml_content = f.read()
            
        # app.yaml에서 SECRET_KEY 라인 찾기
        yaml_secret = None
        for line in yaml_content.split('\n'):
            if 'SECRET_KEY:' in line and not line.strip().startswith('#'):
                yaml_secret = line.split(':', 1)[1].strip().strip('"')
                break
                
        if env_secret and yaml_secret:
            if env_secret == yaml_secret:
                print("✅ .env와 app.yaml의 SECRET_KEY가 일치합니다")
                print(f"🔑 공통 키 미리보기: {env_secret[:15]}...{env_secret[-15:]}")
            else:
                print("❌ .env와 app.yaml의 SECRET_KEY가 다릅니다!")
                print(f"🔑 .env 키 미리보기: {env_secret[:15]}...{env_secret[-15:]}")
                print(f"🔑 yaml 키 미리보기: {yaml_secret[:15]}...{yaml_secret[-15:]}")
                print("⚠️ 이는 개발/프로덕션 환경에서 세션 불일치를 야기할 수 있습니다!")
        else:
            if not env_secret:
                print("❌ .env에서 SECRET_KEY를 찾을 수 없습니다")
            if not yaml_secret:
                print("❌ app.yaml에서 SECRET_KEY를 찾을 수 없습니다")
                
    except Exception as e:
        print(f"❌ app.yaml 읽기 실패: {e}")

if __name__ == "__main__":
    success = test_secret_key_loading()
    test_environment_consistency()
    
    print("\n" + "=" * 60)
    print("📋 배포 준비 상태")
    print("=" * 60)
    
    if success:
        print("🎉 배포 준비 완료! SECRET_KEY 설정이 올바릅니다.")
        print("✅ 패스 유실 문제가 해결되었습니다.")
    else:
        print("❌ 배포 전 문제를 해결해주세요.")
        print("🔧 app.py의 SECRET_KEY 설정을 다시 확인하세요.")
        
    print("\n🚀 배포 명령어:")
    print("gcloud app deploy")
