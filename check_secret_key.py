"""
세션 안정성 확인 스크립트 

이 스크립트는 SECRET_KEY가 제대로 설정되었는지 확인하고
세션의 안정성을 테스트합니다.
"""

import os
import sys
from datetime import datetime

def check_secret_key():
    """SECRET_KEY 설정 상태 확인"""
    print("=" * 60)
    print("🔐 SECRET_KEY 안정성 검사")
    print("=" * 60)
    
    # .env 파일에서 SECRET_KEY 확인
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_file_path):
        print("✅ .env 파일이 존재합니다.")
        
        with open(env_file_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
            
        if 'SECRET_KEY' in env_content:
            print("✅ .env 파일에 SECRET_KEY가 설정되어 있습니다.")
            
            # SECRET_KEY 값 추출
            for line in env_content.split('\n'):
                if line.strip().startswith('SECRET_KEY'):
                    key_value = line.split('=', 1)[1].strip().strip('"')
                    if len(key_value) > 20:
                        print(f"✅ SECRET_KEY 길이: {len(key_value)} (권장: 32자 이상)")
                        print(f"🔑 SECRET_KEY 미리보기: {key_value[:10]}...{key_value[-10:]}")
                    else:
                        print("⚠️ SECRET_KEY가 너무 짧습니다. 보안을 위해 32자 이상 사용을 권장합니다.")
                    break
        else:
            print("❌ .env 파일에 SECRET_KEY가 설정되지 않았습니다.")
    else:
        print("❌ .env 파일이 존재하지 않습니다.")
    
    # 환경 변수에서 SECRET_KEY 확인
    env_secret = os.environ.get('SECRET_KEY')
    if env_secret:
        print("✅ 환경 변수 SECRET_KEY가 설정되어 있습니다.")
        print(f"🔑 환경변수 SECRET_KEY 미리보기: {env_secret[:10]}...{env_secret[-10:]}")
    else:
        print("⚠️ 환경 변수 SECRET_KEY가 설정되지 않았습니다.")
    
    # app.yaml 파일 확인
    app_yaml_path = os.path.join(os.path.dirname(__file__), 'app.yaml')
    if os.path.exists(app_yaml_path):
        print("✅ app.yaml 파일이 존재합니다.")
        
        with open(app_yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
            
        if 'SECRET_KEY:' in yaml_content:
            print("✅ app.yaml에 SECRET_KEY가 설정되어 있습니다.")
        else:
            print("❌ app.yaml에 SECRET_KEY가 설정되지 않았습니다.")
    
    print("\n" + "=" * 60)
    print("📋 결과 및 권장사항")
    print("=" * 60)
    
    print("1. SECRET_KEY는 절대 변경하지 마세요!")
    print("2. 변경하면 모든 기존 사용자 세션과 패스가 무효화됩니다.")
    print("3. 프로덕션 배포 전에 app.yaml의 SECRET_KEY를 확인하세요.")
    print("4. 로컬 개발과 프로덕션에서 동일한 SECRET_KEY를 사용하세요.")
    
    print(f"\n🕐 검사 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    check_secret_key()
