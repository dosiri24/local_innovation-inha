from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
import json
import os
import secrets
from main import (
    Store, Benefit, UserPrefs, Pass, PASS_TYPES,
    load_data, load_themes, generate_pass, save_pass_to_file, 
    load_pass_from_file, get_user_passes
)
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 허용

# 세션 설정
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

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

def login_required(f):
    """로그인이 필요한 페이지에 적용할 데코레이터"""
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def auth_page():
    """인증 페이지 - 로그인/회원가입 선택"""
    if 'user_logged_in' in session:
        return redirect(url_for('main_page'))
    return render_template('auth.html')

@app.route('/main')
@login_required
def main_page():
    """메인 페이지 - 로그인 후 접근 가능"""
    return render_template('main.html')

@app.route('/pass-generator')
@login_required
def pass_generator():
    """패스 생성 페이지 - 기존 인덱스 페이지"""
    return render_template('index.html')

# 로그인/회원가입 API
@app.route('/api/login', methods=['POST'])
def login_api():
    """로그인 API"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({'error': '이메일과 비밀번호를 입력해주세요.'}), 400
        
        # 간단한 로그인 검증 (실제 프로덕션에서는 데이터베이스와 연동)
        # 여기서는 데모용으로 간단히 구현
        if email and password:  # 이메일과 비밀번호가 있으면 로그인 성공
            session['user_logged_in'] = True
            session['user_email'] = email
            return jsonify({'success': True, 'message': '로그인 성공!'})
        else:
            return jsonify({'error': '잘못된 이메일 또는 비밀번호입니다.'}), 401
            
    except Exception as e:
        return jsonify({'error': f'로그인 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/signup', methods=['POST'])
def signup_api():
    """회원가입 API"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not email or not password or not confirm_password:
            return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
        
        if password != confirm_password:
            return jsonify({'error': '비밀번호가 일치하지 않습니다.'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '비밀번호는 6자 이상이어야 합니다.'}), 400
        
        # 간단한 회원가입 처리 (실제 프로덕션에서는 데이터베이스에 저장)
        # 여기서는 데모용으로 바로 로그인 처리
        session['user_logged_in'] = True
        session['user_email'] = email
        return jsonify({'success': True, 'message': '회원가입 성공!'})
        
    except Exception as e:
        return jsonify({'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout_api():
    """로그아웃 API"""
    session.clear()
    return jsonify({'success': True, 'message': '로그아웃되었습니다.'})

# 추가 페이지 라우팅 (모두 로그인 필요)
@app.route('/intro')
@login_required
def intro():
    """소개 페이지"""
    return render_template('intro.html')

@app.route('/taste')
@login_required
def taste():
    """맛 테마 페이지"""
    return render_template('taste.html')

@app.route('/place')
@login_required
def place():
    """장소 테마 페이지"""
    return render_template('place.html')

@app.route('/play')
@login_required
def play():
    """놀이 테마 페이지"""
    return render_template('play.html')

@app.route('/benef')
@login_required
def benef():
    """혜택 페이지"""
    return render_template('benef.html')

@app.route('/login')
def login():
    """로그인 페이지"""
    return render_template('login.html')

@app.route('/member')
def member():
    """회원가입 페이지"""
    return render_template('memberIn.html')

@app.route('/help')
@login_required
def help():
    """도움말 페이지"""
    return render_template('help.html')

# 정적 파일 제공
@app.route('/static/<path:filename>')
def serve_static(filename):
    """정적 파일 제공"""
    return send_from_directory('static', filename)

@app.route('/api/themes')
def get_themes():
    """사용 가능한 테마 목록 반환"""
    try:
        themes = load_themes()
        theme_list = []
        
        for theme in themes:
            theme_list.append({
                'id': theme.id,
                'name': theme.name
            })
        
        return jsonify(theme_list)
    
    except Exception as e:
        print(f"[오류] 테마 로드 실패: {e}")
        # 기본 테마 반환
        return jsonify([
            {'id': 'seafood', 'name': '해산물'},
            {'id': 'cafe', 'name': '카페'},
            {'id': 'traditional', 'name': '전통'},
            {'id': 'retro', 'name': '레트로'},
            {'id': 'quiet', 'name': '조용함'}
        ])

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
@login_required
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
        
        # 세션에서 사용자 이메일 가져오기
        user_email = session.get('user_email', 'demo@jemulpogo.com')
        
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
        
        # 패스 저장을 위한 사용자 입력 정보
        user_input_data = {
            'themes': themes,
            'request': request_text,
            'pass_type': pass_type
        }
        
        # 패스 저장
        save_success = save_pass_to_file(generated_pass, user_email, user_input_data)
        
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
@login_required
def get_user_passes_api():
    """사용자의 모든 패스 조회"""
    try:
        # 세션에서 사용자 이메일 가져오기
        user_email = session.get('user_email', 'demo@jemulpogo.com')
        
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
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
