from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from main import (
    Store, Benefit, UserPrefs, Pass, PASS_TYPES,
    load_data, generate_pass
)
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 허용

# 전역 데이터 저장
stores_data = []
benefits_data = []

def initialize_data():
    """애플리케이션 시작 시 데이터 로드"""
    global stores_data, benefits_data
    stores_data, benefits_data = load_data()
    if not stores_data or not benefits_data:
        print("[오류] 데이터 로드 실패")
    else:
        print(f"[완료] {len(stores_data)}개 상점, {len(benefits_data)}개 혜택 로드됨")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/themes')
def get_themes():
    """사용 가능한 테마 목록 반환"""
    themes = set()
    for store in stores_data:
        themes.update(store.themes)
    return jsonify(sorted(list(themes)))

@app.route('/api/pass-types')
def get_pass_types():
    """패스 타입 정보 반환"""
    return jsonify({
        'light': {
            'name': PASS_TYPES['light'].name,
            'price': PASS_TYPES['light'].price,
            'max_benefits': PASS_TYPES['light'].max_benefits,
            'description': PASS_TYPES['light'].description
        },
        'premium': {
            'name': PASS_TYPES['premium'].name,
            'price': PASS_TYPES['premium'].price,
            'max_benefits': PASS_TYPES['premium'].max_benefits,
            'description': PASS_TYPES['premium'].description
        }
    })

@app.route('/api/generate-pass', methods=['POST'])
def generate_pass_api():
    """패스 생성 API"""
    try:
        data = request.get_json()
        
        # 입력 검증
        if not data:
            return jsonify({'error': '요청 데이터가 없습니다.'}), 400
        
        themes = data.get('themes', [])
        request_text = data.get('request', '').strip()
        pass_type = data.get('pass_type', 'light')
        
        if not request_text:
            return jsonify({'error': '요청사항을 입력해주세요.'}), 400
        
        if pass_type not in PASS_TYPES:
            return jsonify({'error': '유효하지 않은 패스 타입입니다.'}), 400
        
        # UserPrefs 객체 생성
        user_prefs = UserPrefs(
            themes=themes,
            request=request_text,
            pass_type=pass_type,
            budget=PASS_TYPES[pass_type].price
        )
        
        # 패스 생성
        generated_pass = generate_pass(user_prefs, stores_data, benefits_data)
        
        if not generated_pass.recs:
            return jsonify({'error': '조건에 맞는 추천을 찾을 수 없습니다.'}), 400
        
        # 응답 데이터 구성
        pass_info = PASS_TYPES[pass_type]
        result = {
            'success': True,
            'pass_info': {
                'name': pass_info.name,
                'price': pass_info.price,
                'max_benefits': pass_info.max_benefits,
                'description': pass_info.description,
                'benefits_count': len(generated_pass.recs),
                'total_value': generated_pass.total_value,
                'value_ratio': round((generated_pass.total_value / pass_info.price) * 100, 0),
                'avg_synergy': round(generated_pass.avg_synergy, 1)
            },
            'recommendations': generated_pass.recs,
            'user_input': {
                'themes': themes,
                'request': request_text,
                'pass_type': pass_type
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[오류] 패스 생성 중 에러: {e}")
        return jsonify({'error': f'패스 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({'status': 'healthy', 'message': '제물포GO 서버가 정상 작동 중입니다.'})

if __name__ == '__main__':
    # 데이터 초기화
    initialize_data()
    
    # 개발 모드에서 실행
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
