"""
제물포GO 패스 - 진입점
AI 기반 동인천 관광 추천 시스템
"""

import os
import sys

# src 폴더를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app, initialize_data

# 데이터 초기화
initialize_data()

# Flask 앱 생성 (WSGI 애플리케이션)
app = create_app()

def main():
    """개발 모드에서만 사용하는 메인 함수"""
    # 개발 모드에서 실행
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
