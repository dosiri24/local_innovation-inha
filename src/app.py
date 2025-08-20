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

    # 세션 설정 - Google App Engine 읽기 전용 파일시스템 문제 해결
    app.config['SECRET_KEY'] = secrets.token_hex(16)

    # 환경에 따른 세션 설정
    is_production = (
        os.environ.get('GAE_ENV', '').startswith('standard') or 
        os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
        'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
    )

    print(f"[환경 감지] Production 환경: {is_production}")

    if is_production:
        # 프로덕션 환경: Flask의 기본 세션 사용 (서버 사이드 대신 클라이언트 사이드)
        print("[세션] 프로덕션 환경: 클라이언트 사이드 세션 사용")
        app.config['SESSION_COOKIE_SECURE'] = False  # HTTPS 강제 해제 (테스트용)
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = None
        # Flask-Session 초기화 하지 않음 (기본 Flask 세션 사용)
    else:
        # 개발 환경: 파일시스템 세션 사용
        print("[세션] 개발 환경: 파일시스템 세션 사용")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_PERMANENT'] = False
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'jemulpogo:'
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        Session(app)

    # 라우트 등록
    register_routes(app)
    
    return app

def initialize_data():
    """애플리케이션 시작 시 데이터 로드"""
    stores_data = load_stores()
    benefits_data = load_benefits()
    
    if not stores_data or not benefits_data:
        print("[오류] 데이터 로드 실패")
    else:
        print(f"[완료] {len(stores_data)}개 상점, {len(benefits_data)}개 혜택 로드됨")
    
    return stores_data, benefits_data

# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    # 데이터 초기화
    initialize_data()
    
    # 개발 모드에서 실행
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # 프로덕션 모드 (Gunicorn)에서 실행
    initialize_data()
