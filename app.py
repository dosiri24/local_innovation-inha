from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from main import (
    Store, Benefit, UserPrefs, Pass, PASS_TYPES,
    load_data, generate_pass, save_pass_to_file, 
    load_pass_from_file, get_user_passes
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
            'description': PASS_TYPES['light'].description
        },
        'premium': {
            'name': PASS_TYPES['premium'].name,
            'price': PASS_TYPES['premium'].price,
            'description': PASS_TYPES['premium'].description
        },
        'citizen': {
            'name': PASS_TYPES['citizen'].name,
            'price': PASS_TYPES['citizen'].price,
            'description': PASS_TYPES['citizen'].description
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
        user_email = data.get('user_email', '')  # 사용자 이메일 (선택적)
        
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
        
        # 패스 저장
        save_success = save_pass_to_file(generated_pass, user_email)
        
        # 응답 데이터 구성
        pass_info = PASS_TYPES[pass_type]
        result = {
            'success': True,
            'pass_id': generated_pass.pass_id,  # 패스 ID 추가
            'created_at': generated_pass.created_at,  # 생성 시간 추가
            'qr_code_available': bool(generated_pass.qr_code_path),  # QR 코드 유무
            'pass_info': {
                'name': pass_info.name,
                'price': pass_info.price,
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
            },
            'saved': save_success  # 저장 성공 여부
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[오류] 패스 생성 중 에러: {e}")
        return jsonify({'error': f'패스 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({'status': 'healthy', 'message': '제물포GO 서버가 정상 작동 중입니다.'})


@app.route('/api/pass/<pass_id>')
def get_pass_by_id(pass_id):
    """패스 ID로 저장된 패스 조회"""
    try:
        pass_data = load_pass_from_file(pass_id)
        
        if not pass_data:
            return jsonify({'error': '패스를 찾을 수 없습니다.'}), 404
        
        return jsonify({
            'success': True,
            'pass_data': pass_data
        })
        
    except Exception as e:
        print(f"[오류] 패스 조회 중 에러: {e}")
        return jsonify({'error': f'패스 조회 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/user/passes')
def get_user_passes_api():
    """사용자의 모든 패스 조회"""
    try:
        user_email = request.args.get('email')
        
        if not user_email:
            return jsonify({'error': '사용자 이메일이 필요합니다.'}), 400
        
        user_passes = get_user_passes(user_email)
        
        return jsonify({
            'success': True,
            'passes': user_passes,
            'count': len(user_passes)
        })
        
    except Exception as e:
        print(f"[오류] 사용자 패스 조회 중 에러: {e}")
        return jsonify({'error': f'패스 조회 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/api/pass/<pass_id>/qr')
def get_pass_qr_code(pass_id):
    """패스의 QR 코드 이미지 다운로드"""
    try:
        pass_data = load_pass_from_file(pass_id)
        
        if not pass_data:
            return jsonify({'error': '패스를 찾을 수 없습니다.'}), 404
        
        qr_code_path = pass_data.get('qr_code_path')
        
        if not qr_code_path or not os.path.exists(qr_code_path):
            return jsonify({'error': 'QR 코드를 찾을 수 없습니다.'}), 404
        
        return send_file(qr_code_path, as_attachment=True, download_name=f'pass_{pass_id}_qr.png')
        
    except Exception as e:
        print(f"[오류] QR 코드 조회 중 에러: {e}")
        return jsonify({'error': f'QR 코드 조회 중 오류가 발생했습니다: {str(e)}'}), 500


@app.route('/pass/<pass_id>')
def view_pass(pass_id):
    """QR 코드 스캔 시 보여줄 패스 상세 페이지"""
    try:
        pass_data = load_pass_from_file(pass_id)
        
        if not pass_data:
            return render_template('pass_not_found.html', pass_id=pass_id), 404
        
        return render_template('pass_detail.html', pass_data=pass_data)
        
    except Exception as e:
        print(f"[오류] 패스 페이지 조회 중 에러: {e}")
        return render_template('error.html', error=str(e)), 500

if __name__ == '__main__':
    # 데이터 초기화
    initialize_data()
    
    # 개발 모드에서 실행
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
