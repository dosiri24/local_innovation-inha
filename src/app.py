"""
Flask 웹 애플리케이션 설정 및 초기화
"""
from flask import Flask
from flask_cors import CORS
from flask_session import Session
import os
import secrets
from routes import register_routes
from services import load_stores, load_benefits
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def create_app():
    """Flask 앱 팩토리"""
    # 현재 파일의 디렉토리를 기준으로 상위 디렉토리 경로 계산
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # 템플릿과 정적 파일 경로 설정
    template_folder = os.path.join(parent_dir, 'templates')
    static_folder = os.path.join(parent_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    CORS(app)  # CORS 허용

    # 세션 설정 - SECRET_KEY 고정으로 세션 유지 보장
    # 🚨 중요: SECRET_KEY가 변경되면 모든 세션이 무효화되므로 고정값 사용
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        # 환경변수가 없으면 고정된 개발용 키 사용 (프로덕션에서는 반드시 환경변수 설정)
        secret_key = 'jemulpogo-demo-secret-key-fixed-2024-do-not-change-this-value-or-sessions-will-be-lost'
        print("[보안 경고] 프로덕션 환경에서는 반드시 SECRET_KEY 환경변수를 설정하세요!")
    
    app.config['SECRET_KEY'] = secret_key
    print(f"[세션 보안] SECRET_KEY 설정됨 (길이: {len(secret_key)})")

    # 환경에 따른 세션 설정
    is_production = (
        os.environ.get('GAE_ENV', '').startswith('standard') or 
        os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
        'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
    )

    print(f"[환경 감지] Production 환경: {is_production}")

    if is_production:
        # 프로덕션 환경: 영구 세션 설정으로 안정성 강화
        print("[세션] 프로덕션 환경: 영구 클라이언트 사이드 세션 사용")
        app.config['SESSION_COOKIE_SECURE'] = False  # HTTP에서도 작동하도록 설정
        app.config['SESSION_COOKIE_HTTPONLY'] = False  # JavaScript 접근 허용
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 쿠키 설정과 일치
        app.config['SESSION_PERMANENT'] = True  # 영구 세션으로 설정
        app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24*30  # 30일로 연장 (기존 7일에서 확대)
        # Flask-Session 초기화 하지 않음 (기본 Flask 세션 사용하되 SECRET_KEY 고정으로 안정성 확보)
    else:
        # 개발 환경: 파일시스템 세션 사용 (안정성 강화)
        print("[세션] 개발 환경: 파일시스템 세션 사용")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_PERMANENT'] = True  # 개발환경도 영구 세션으로 변경
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'jemulpogo:'
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24*30  # 개발환경도 30일로 연장
        # 파일시스템 세션 디렉토리를 임시 디렉토리로 설정
        session_dir = os.path.join(parent_dir, 'flask_session')
        os.makedirs(session_dir, exist_ok=True)
        app.config['SESSION_FILE_DIR'] = session_dir
        Session(app)

    # 라우트 등록
    register_routes(app)
    
    return app

def initialize_data():
    """애플리케이션 시작 시 데이터 로드"""
    try:
        stores_data = load_stores()
        benefits_data = load_benefits()
        
        if not stores_data or not benefits_data:
            print("[경고] 일부 데이터 로드 실패")
            return [], []
        else:
            print(f"[완료] {len(stores_data)}개 상점, {len(benefits_data)}개 혜택 로드됨")
        
        return stores_data, benefits_data
    except Exception as e:
        print(f"[오류] 데이터 초기화 실패: {str(e)}")
        return [], []

# Flask 앱 생성 함수만 제공 (중복된 앱 인스턴스 생성 제거)
# 앱 인스턴스는 main.py에서만 생성

if __name__ == '__main__':
    # 개발 모드에서만 실행
    app = create_app()
    initialize_data()
    
    # 개발 모드에서 실행
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
