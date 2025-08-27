"""
Flask 라우트 정의
"""
from flask import render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for
import os
from models import UserPrefs, PassType, Theme
from services import (
    load_stores, load_benefits, load_themes, generate_pass, 
    load_pass_from_file, get_all_passes
)

def login_required(f):
    """로그인이 필요한 페이지에 적용할 데코레이터"""
    def decorated_function(*args, **kwargs):
        # 세션 검증 강화
        if 'user_logged_in' not in session or not session.get('user_logged_in'):
            return redirect(url_for('auth_page'))
        if 'user_email' not in session or not session.get('user_email'):
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def register_routes(app):
    """Flask 앱에 모든 라우트 등록"""
    
    # 헬스체크 엔드포인트
    @app.route('/health')
    def health_check():
        """앱 상태 확인용 헬스체크 엔드포인트"""
        return jsonify({
            'status': 'healthy',
            'message': '제물포GO 패스 애플리케이션이 정상적으로 실행 중입니다.'
        }), 200
    
    @app.route('/_ah/health')
    def gae_health_check():
        """Google App Engine 헬스체크 엔드포인트"""
        return 'OK', 200
    
    # 기본 페이지 라우트
    @app.route('/')
    def auth_page():
        """인증 페이지 - 로그인/회원가입 선택"""
        # 세션 확인을 더 강화
        if 'user_logged_in' in session and session.get('user_logged_in') == True:
            return redirect(url_for('main_page'))
        return render_template('index.html')

    @app.route('/main')
    @login_required
    def main_page():
        """메인 페이지 - 로그인 후 접근 가능"""
        # 추가 세션 검증
        if not session.get('user_logged_in') or not session.get('user_email'):
            session.clear()
            return redirect(url_for('auth_page'))
        return render_template('main.html')

    @app.route('/pass-generator')
    @login_required
    def pass_generator():
        """패스 생성 페이지 - 기존 인덱스 페이지"""
        return render_template('auth.html')

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

    @app.route('/map')
    def map_page():
        """지도 페이지"""
        kakao_api_key = os.getenv('KAKAO_API_KEY', '')
        return render_template('map.html', kakao_api_key=kakao_api_key)

    @app.route('/pass/<pass_id>')
    def view_pass(pass_id):
        """QR 코드 스캔 시 보여줄 패스 상세 페이지"""
        try:
            print(f"[패스 상세] 요청된 패스 ID: {pass_id}")
            pass_data = load_pass_from_file(pass_id)
            
            if not pass_data:
                print(f"[패스 상세] 패스를 찾을 수 없음: {pass_id}")
                return render_template('pass_not_found.html', pass_id=pass_id), 404
            
            print(f"[패스 상세] 로드된 패스 데이터: pass_id={pass_data.pass_id}, type={type(pass_data)}")
            print(f"[패스 상세] 패스 타입: {pass_data.pass_type}, 테마: {pass_data.theme}")
            print(f"[패스 상세] 매장 수: {len(pass_data.stores)}, 혜택 수: {len(pass_data.benefits)}")
            
            return render_template('pass_detail.html', pass_data=pass_data)
            
        except Exception as e:
            print(f"[오류] 패스 페이지 조회 중 에러: {e}")
            import traceback
            traceback.print_exc()
            return render_template('error.html', error=str(e)), 500

    # 정적 파일 제공
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """정적 파일 제공"""
        return send_from_directory('static', filename)

    @app.route('/favicon.ico')
    def favicon():
        """파비콘 제공"""
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

    # 인증 API
    @app.route('/api/login', methods=['POST'])
    def login_api():
        """로그인 API"""
        try:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            
            print(f"[로그인 시도] 이메일: {email}")
            
            if not email or not password:
                return jsonify({'error': '이메일과 비밀번호를 입력해주세요.'}), 400
            
            # 간단한 로그인 검증 (실제 프로덕션에서는 데이터베이스와 연동)
            # 여기서는 데모용으로 간단히 구현
            if email and password:  # 이메일과 비밀번호가 있으면 로그인 성공
                # 세션 설정을 더 명확하게
                session.clear()  # 기존 세션 정리
                session['user_logged_in'] = True
                session['user_email'] = email
                session.permanent = True  # 세션을 영구적으로 설정
                
                print(f"[로그인 성공] 세션 설정 완료: {session}")
                
                response = jsonify({
                    'success': True, 
                    'message': '로그인 성공!',
                    'redirect_url': '/main',  # 리다이렉트 URL 추가
                    'session_id': request.cookies.get('session', 'no-session')
                })
                
                # 추가 쿠키 설정
                response.set_cookie('user_logged_in', 'true', 
                                  secure=False, 
                                  httponly=False,
                                  samesite='Lax')
                
                return response
            else:
                return jsonify({'error': '잘못된 이메일 또는 비밀번호입니다.'}), 401
                
        except Exception as e:
            print(f"[로그인 오류] {str(e)}")
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
            session.clear()  # 기존 세션 정리
            session['user_logged_in'] = True
            session['user_email'] = email
            session.permanent = True  # 세션을 영구적으로 설정
            
            return jsonify({
                'success': True, 
                'message': '회원가입 성공!',
                'redirect_url': '/main'  # 리다이렉트 URL 추가
            })
            
        except Exception as e:
            return jsonify({'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'}), 500

    @app.route('/api/logout', methods=['POST'])
    def logout_api():
        """로그아웃 API"""
        session.clear()
        return jsonify({'success': True, 'message': '로그아웃되었습니다.'})

    @app.route('/api/session-check', methods=['GET'])
    def session_check_api():
        """세션 상태 확인 API"""
        user_logged_in = session.get('user_logged_in', False)
        user_email = session.get('user_email')
        is_logged_in = user_logged_in and user_email
        
        print(f"[세션 확인] user_logged_in: {user_logged_in}")
        print(f"[세션 확인] user_email: {user_email}")
        print(f"[세션 확인] 전체 세션: {dict(session)}")
        print(f"[세션 확인] 쿠키: {dict(request.cookies)}")
        
        return jsonify({
            'logged_in': bool(is_logged_in),
            'user_email': user_email if is_logged_in else None,
            'session_data': dict(session),
            'cookies': dict(request.cookies)
        })

    # 데이터 API
    @app.route('/api/themes')
    def get_themes():
        """사용 가능한 테마 목록 반환"""
        try:
            themes_data = load_themes()
            # themes.json 구조에 맞게 반환
            return jsonify(themes_data)
        
        except Exception as e:
            print(f"[오류] 테마 로드 실패: {e}")
            # 기본 테마 반환
            return jsonify({
                "taste": {"name": "맛있는 동인천", "themes": ["seafood", "cafe", "traditional"]},
                "place": {"name": "아름다운 동인천", "themes": ["retro", "quiet", "culture"]}
            })

    @app.route('/api/pass-types')
    def get_pass_types():
        """패스 타입 정보 반환"""
        return jsonify({
            'TASTE': {
                'name': '맛있는 동인천',
                'description': '동인천의 맛집을 탐방하는 패스'
            },
            'BEAUTY': {
                'name': '아름다운 동인천',
                'description': '동인천의 아름다운 명소를 탐방하는 패스'
            }
        })

    @app.route('/api/test')
    def test_api():
        """테스트용 간단한 API"""
        return jsonify({'message': 'API가 정상 작동합니다!', 'success': True})

    @app.route('/api/stores')
    def get_stores():
        """매장 정보 반환 (좌표 포함)"""
        try:
            from services import load_stores_raw
            stores_data = load_stores_raw()  # 원본 데이터 사용 (좌표 포함)
            
            return jsonify({
                'success': True,
                'stores': stores_data,
                'count': len(stores_data)
            })
            
        except Exception as e:
            print(f"[오류] 매장 데이터 로드 실패: {e}")
            return jsonify({
                'error': f'매장 데이터를 불러올 수 없습니다: {str(e)}',
                'success': False,
                'stores': [],
                'count': 0
            }), 500

    # 패스 관련 API
    @app.route('/api/generate-pass', methods=['POST'])
    @login_required
    def generate_pass_api():
        """패스 생성 API"""
        try:
            data = request.get_json()
            
            # 입력 검증
            if not data:
                return jsonify({'error': '요청 데이터가 없습니다.'}), 400
            
            budget = data.get('budget', '보통')
            interests = data.get('interests', [])
            dietary_restrictions = data.get('dietary_restrictions', [])
            group_size = data.get('group_size', 2)
            duration = data.get('duration', '반나절')
            transportation = data.get('transportation', '도보')
            pass_type_str = data.get('pass_type', 'TASTE')
            theme_str = data.get('theme', 'FOOD')
            
            # 세션에서 사용자 이메일 가져오기
            user_email = session.get('user_email', 'demo@jemulpogo.com')
            
            # UserPrefs 객체 생성
            user_prefs = UserPrefs(
                budget=budget,
                interests=interests,
                dietary_restrictions=dietary_restrictions,
                group_size=group_size,
                duration=duration,
                transportation=transportation
            )
            
            # Enum 변환 - 유연한 매핑
            try:
                # PassType 매핑
                pass_type_mapping = {
                    'light': PassType.LIGHT,
                    'premium': PassType.PREMIUM,
                    'citizen': PassType.CITIZEN
                }
                
                # Theme 매핑
                theme_mapping = {
                    'food': Theme.FOOD,
                    'culture': Theme.CULTURE,
                    'shopping': Theme.SHOPPING,
                    'entertainment': Theme.ENTERTAINMENT,
                    'seafood': Theme.SEAFOOD,
                    'cafe': Theme.CAFE,
                    'traditional': Theme.TRADITIONAL,
                    'retro': Theme.RETRO,
                    'quiet': Theme.QUIET,
                    '음식': Theme.FOOD,
                    '문화': Theme.CULTURE,
                    '쇼핑': Theme.SHOPPING,
                    '엔터테인먼트': Theme.ENTERTAINMENT,
                    '해산물': Theme.SEAFOOD,
                    '카페': Theme.CAFE,
                    '전통': Theme.TRADITIONAL,
                    '레트로': Theme.RETRO,
                    '조용함': Theme.QUIET
                }
                
                pass_type = pass_type_mapping.get(pass_type_str.lower(), PassType.LIGHT)
                theme = theme_mapping.get(theme_str.lower(), Theme.FOOD)
                
                print(f"[패스 타입 변환] 입력: {pass_type_str} -> {pass_type} (값: {pass_type.value})")
                print(f"[테마 변환] 입력: {theme_str} -> {theme} (값: {theme.value})")
                
            except Exception as e:
                print(f"Enum 변환 오류: {e}")
                # 기본값 사용
                pass_type = PassType.LIGHT
                theme = Theme.FOOD
            
            # 패스 생성
            generated_pass = generate_pass(user_prefs, pass_type, theme)
            
            if not generated_pass:
                return jsonify({'error': '조건에 맞는 패스를 생성할 수 없습니다.'}), 400
            
            # 혜택 데이터에서 store_id를 실제 상점명으로 변환
            from services import load_stores_raw
            stores_raw = load_stores_raw()
            store_id_to_name = {store['id']: store['name'] for store in stores_raw}
            
            # 혜택 정보를 프론트엔드 형식으로 변환
            recommendations = []
            enhanced_benefits = []
            
            for benefit in generated_pass.benefits:
                store_name = store_id_to_name.get(benefit.store_name, benefit.store_name)
                
                # 프론트엔드용 형식
                recommendations.append({
                    'benefit_id': f'B{len(recommendations)+1:03d}',
                    'store_name': store_name,
                    'benefit_desc': benefit.description,
                    'eco_value': 3500,  # 임시값, 실제로는 benefit에서 가져와야 함
                    'reason': f'{store_name}에서 제공하는 특별 혜택입니다.'
                })
                
                # 기존 API용 형식
                enhanced_benefit = benefit.__dict__.copy()
                enhanced_benefit['store_name'] = store_name
                enhanced_benefits.append(enhanced_benefit)
            
            # 패스 타입별 정보 설정 (light, premium, citizen만)
            pass_type_info = {
                'light': {'name': '라이트 패스', 'price': 7900},
                'premium': {'name': '프리미엄 패스', 'price': 14900},
                'citizen': {'name': '시민 패스', 'price': 6900}
            }
            
            pass_info = pass_type_info.get(generated_pass.pass_type.value, pass_type_info['light'])
            total_value = sum(rec['eco_value'] for rec in recommendations)
            
            print(f"[패스 정보] 패스 타입 값: {generated_pass.pass_type.value}")
            print(f"[패스 정보] 매핑된 정보: {pass_info}")
            print(f"[패스 정보] 총 혜택 가치: {total_value}")
            
            # 응답 데이터 구성 (프론트엔드가 기대하는 형식)
            result = {
                'success': True,
                'pass_id': generated_pass.pass_id,
                'created_at': generated_pass.created_at,
                'qr_code_available': bool(generated_pass.qr_code_path),
                'pass_info': {
                    'name': pass_info['name'],
                    'price': pass_info['price'],
                    'pass_type': generated_pass.pass_type.value,
                    'theme': generated_pass.theme.value,
                    'stores_count': len(generated_pass.stores),
                    'benefits_count': len(generated_pass.benefits),
                    'total_value': total_value,
                    'value_ratio': int((total_value / pass_info['price']) * 100),
                    'avg_synergy': 85.5  # 임시값
                },
                'stores': [store.__dict__ for store in generated_pass.stores],
                'benefits': enhanced_benefits,  # 기존 API 응답 유지
                'recommendations': recommendations,  # 프론트엔드용 데이터
                'user_input': {
                    'budget': budget,
                    'interests': interests,
                    'dietary_restrictions': dietary_restrictions,
                    'group_size': group_size,
                    'duration': duration,
                    'transportation': transportation,
                    'pass_type': pass_type_str,
                    'theme': theme_str
                }
            }
            
            return jsonify(result)
            
        except ValueError as e:
            # AI API 관련 에러는 400 Bad Request로 처리
            print(f"[AI 오류] {e}")
            return jsonify({
                'error': f'AI 추천 서비스 오류: {str(e)}',
                'error_type': 'AI_SERVICE_ERROR'
            }), 400
            
        except Exception as e:
            print(f"[시스템 오류] 패스 생성 중 에러: {e}")
            return jsonify({
                'error': f'시스템 오류가 발생했습니다: {str(e)}',
                'error_type': 'SYSTEM_ERROR'
            }), 500

    @app.route('/api/pass/<pass_id>')
    def get_pass_by_id(pass_id):
        """패스 ID로 저장된 패스 조회"""
        try:
            pass_data = load_pass_from_file(pass_id)
            
            if not pass_data:
                return jsonify({'error': '패스를 찾을 수 없습니다.'}), 404
            
            # 혜택 데이터에서 store_id를 실제 상점명으로 변환
            from services import load_stores_raw
            stores_raw = load_stores_raw()
            store_id_to_name = {store['id']: store['name'] for store in stores_raw}
            
            # 혜택 정보를 사용자 친화적으로 변환
            enhanced_benefits = []
            for benefit in pass_data.benefits:
                store_name = store_id_to_name.get(benefit.store_name, benefit.store_name)
                enhanced_benefit = benefit.__dict__.copy()
                enhanced_benefit['store_name'] = store_name
                enhanced_benefits.append(enhanced_benefit)
            
            return jsonify({
                'success': True,
                'pass_data': {
                    'pass_id': pass_data.pass_id,
                    'pass_type': pass_data.pass_type.value,
                    'theme': pass_data.theme.value,
                    'created_at': pass_data.created_at,
                    'stores': [store.__dict__ for store in pass_data.stores],
                    'benefits': enhanced_benefits,  # 변환된 혜택 데이터 사용
                    'user_prefs': pass_data.user_prefs.__dict__,
                    'qr_code_path': pass_data.qr_code_path
                }
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
            
            user_passes = get_all_passes()
            
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
            
            qr_code_path = pass_data.qr_code_path
            
            if not qr_code_path or not os.path.exists(qr_code_path):
                return jsonify({'error': 'QR 코드를 찾을 수 없습니다.'}), 404
            
            return send_file(qr_code_path, as_attachment=True, download_name=f'pass_{pass_id}_qr.png')
            
        except Exception as e:
            print(f"[오류] QR 코드 조회 중 에러: {e}")
            return jsonify({'error': f'QR 코드 조회 중 오류가 발생했습니다: {str(e)}'}), 500
