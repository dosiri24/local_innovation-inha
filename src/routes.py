"""
Flask 라우트 정의
"""
from flask import render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for
import os
from models import UserPrefs, PassType, Theme
from services import (
    load_stores, load_benefits, load_themes,
    load_pass_from_file, get_all_passes
)
from pass_generator import generate_pass  # 패스 생성 모듈에서 임포트
from chatbot import get_chatbot, clear_chatbot_session  # 채팅봇 모듈 임포트

def login_required(f):
    """로그인이 필요한 페이지에 적용할 데코레이터"""
    def decorated_function(*args, **kwargs):
        # 프로덕션 환경에서 세션 검증 완화
        is_production = (
            os.environ.get('GAE_ENV', '').startswith('standard') or 
            os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
            'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
        )
        
        if is_production:
            # 프로덕션 환경에서는 세션 검증을 완화하고 쿠키도 확인
            user_logged_in = session.get('user_logged_in') or request.cookies.get('user_logged_in') == 'true'
            user_email = session.get('user_email') or request.cookies.get('user_email')
            
            if not user_logged_in or not user_email:
                print(f"[로그인 필요] 세션: {dict(session)}, 쿠키: {dict(request.cookies)}")
                return redirect(url_for('auth_page'))
        else:
            # 개발 환경에서는 기존 검증 방식 유지
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
        kakao_api_key = os.getenv('KAKAO_API_KEY', 'a67274a743814b8d146d016ae4ae47d8')
        return render_template('auth.html', kakao_api_key=kakao_api_key)

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



    @app.route('/pass/<pass_id>')
    def view_pass(pass_id):
        """패스 상세 페이지"""
        try:
            print(f"[패스 상세] 요청된 패스 ID: {pass_id}")
            pass_data = load_pass_from_file(pass_id)
            
            if not pass_data:
                print(f"[패스 상세] 패스를 찾을 수 없음: {pass_id}")
                return render_template('pass_not_found.html', pass_id=pass_id), 404
            
            print(f"[패스 상세] 로드된 패스 데이터: pass_id={pass_data.pass_id}, type={type(pass_data)}")
            print(f"[패스 상세] 패스 타입: {pass_data.pass_type}, 테마: {pass_data.theme}")
            print(f"[패스 상세] 매장 수: {len(pass_data.stores)}, 혜택 수: {len(pass_data.benefits)}")
            
            # 카카오 API 키 가져오기
            kakao_api_key = os.getenv('KAKAO_API_KEY', 'a67274a743814b8d146d016ae4ae47d8')
            
            # 모든 stores 데이터 로드 (위치 정보 포함)
            all_stores_with_coords = load_stores()
            
            return render_template('pass_detail.html', 
                                 pass_data=pass_data,
                                 kakao_api_key=kakao_api_key,
                                 all_stores_with_coords=all_stores_with_coords)
            
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
        return send_from_directory('static', 'favicon.ico')

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
                
                # 프로덕션 환경에서 세션 백업용 쿠키 설정
                response.set_cookie('user_logged_in', 'true', 
                                  max_age=60*60*24*7,  # 7일 유지
                                  secure=False,  # HTTP에서도 작동하도록 설정
                                  httponly=False,
                                  samesite='Lax')
                response.set_cookie('user_email', email,
                                  max_age=60*60*24*7,  # 7일 유지  
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
            
            response = jsonify({
                'success': True, 
                'message': '회원가입 성공!',
                'redirect_url': '/main'  # 리다이렉트 URL 추가
            })
            
            # 프로덕션 환경에서 세션 백업용 쿠키 설정
            response.set_cookie('user_logged_in', 'true', 
                              max_age=60*60*24*7,  # 7일 유지
                              secure=False,
                              httponly=False,
                              samesite='Lax')
            response.set_cookie('user_email', email,
                              max_age=60*60*24*7,  # 7일 유지  
                              secure=False,
                              httponly=False,
                              samesite='Lax')
            
            return response
            
        except Exception as e:
            return jsonify({'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'}), 500

    @app.route('/api/logout', methods=['POST'])
    def logout_api():
        """로그아웃 API"""
        session.clear()
        response = jsonify({'success': True, 'message': '로그아웃되었습니다.'})
        
        # 쿠키도 제거
        response.set_cookie('user_logged_in', '', expires=0)
        response.set_cookie('user_email', '', expires=0)
        
        return response

    @app.route('/api/session-check', methods=['GET'])
    def session_check_api():
        """세션 상태 확인 API"""
        # 세션과 쿠키 모두 확인
        session_logged_in = session.get('user_logged_in', False)
        session_email = session.get('user_email')
        
        cookie_logged_in = request.cookies.get('user_logged_in') == 'true'
        cookie_email = request.cookies.get('user_email')
        
        # 세션 또는 쿠키 중 하나라도 유효하면 로그인 상태로 인정
        user_logged_in = session_logged_in or cookie_logged_in
        user_email = session_email or cookie_email
        
        is_logged_in = user_logged_in and user_email
        
        print(f"[세션 확인] 세션 로그인: {session_logged_in}, 쿠키 로그인: {cookie_logged_in}")
        print(f"[세션 확인] 세션 이메일: {session_email}, 쿠키 이메일: {cookie_email}")
        print(f"[세션 확인] 최종 로그인 상태: {is_logged_in}")
        print(f"[세션 확인] 전체 세션: {dict(session)}")
        print(f"[세션 확인] 전체 쿠키: {dict(request.cookies)}")
        
        # 쿠키에서 로그인 정보가 확인되었지만 세션에 없다면 세션에 복원
        if cookie_logged_in and cookie_email and not session_logged_in:
            print("[세션 확인] 쿠키에서 세션 복원")
            session['user_logged_in'] = True
            session['user_email'] = cookie_email
            session.permanent = True
        
        return jsonify({
            'logged_in': bool(is_logged_in),
            'user_email': user_email if is_logged_in else None,
            'session_data': dict(session),
            'cookies': dict(request.cookies),
            'debug_info': {
                'session_logged_in': session_logged_in,
                'cookie_logged_in': cookie_logged_in,
                'session_email': session_email,
                'cookie_email': cookie_email
            }
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

    # 채팅봇 관련 API
    @app.route('/api/chat/start', methods=['POST'])
    @login_required
    def start_chat():
        """채팅 대화 시작"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': '요청 데이터가 없습니다.'}), 400
            
            selected_themes = data.get('themes', [])
            
            # 세션 ID 생성 (사용자 이메일 + 타임스탬프)
            user_email = session.get('user_email', 'anonymous')
            session_id = f"{user_email}_{hash(user_email) % 10000:04d}"
            
            # 채팅봇 인스턴스 가져오기
            chatbot = get_chatbot(session_id)
            
            # 대화 시작
            bot_message = chatbot.start_conversation(selected_themes)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'bot_message': bot_message,
                'conversation_history': chatbot.conversation_history
            })
            
        except Exception as e:
            print(f"[채팅봇 API] 대화 시작 실패: {e}")
            return jsonify({
                'error': f'채팅 시작 중 오류가 발생했습니다: {str(e)}',
                'success': False
            }), 500

    @app.route('/api/chat/message', methods=['POST'])
    @login_required  
    def send_chat_message():
        """채팅 메시지 전송"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': '요청 데이터가 없습니다.'}), 400
            
            session_id = data.get('session_id')
            user_message = data.get('message', '').strip()
            
            if not session_id or not user_message:
                return jsonify({'error': '세션 ID와 메시지가 필요합니다.'}), 400
            
            # 채팅봇 인스턴스 가져오기
            chatbot = get_chatbot(session_id)
            
            # 대화 계속하기
            result = chatbot.continue_conversation(user_message)
            
            # 부적절한 대화 감지 시 세션 즉시 종료
            if result.get('inappropriate', False):
                print(f"[채팅봇 API] 부적절한 대화 감지 - 세션 {session_id} 종료")
                clear_chatbot_session(session_id)
                
                return jsonify({
                    'success': True,
                    'bot_message': result.get('message', '죄송합니다. 부적절한 내용이 감지되어 대화를 종료합니다.'),
                    'conversation_complete': True,
                    'inappropriate': True,
                    'terminate_chat': True,  # 프론트엔드에 채팅 종료 신호
                    'conversation_history': result.get('conversation_history', []),
                    'conversation_summary': ''
                })
            
            return jsonify({
                'success': True,
                'bot_message': result['bot_message'],
                'conversation_complete': result['conversation_complete'],
                'conversation_history': result['conversation_history'],
                'conversation_summary': result.get('conversation_summary', '')
            })
            
        except Exception as e:
            print(f"[채팅봇 API] 메시지 처리 실패: {e}")
            return jsonify({
                'error': f'메시지 처리 중 오류가 발생했습니다: {str(e)}',
                'success': False
            }), 500

    @app.route('/api/chat/complete', methods=['POST'])
    @login_required
    def complete_chat():
        """채팅 완료 후 패스 생성"""
        try:
            print(f"[채팅봇 API] 패스 생성 요청 수신 - 사용자: {session.get('user_email')}")
            
            data = request.get_json()
            print(f"[채팅봇 API] 요청 데이터: {data}")
            
            if not data:
                return jsonify({'error': '요청 데이터가 없습니다.'}), 400
            
            session_id = data.get('session_id')
            pass_type_str = data.get('pass_type', 'light')
            
            print(f"[채팅봇 API] 세션 ID: {session_id}, 패스 타입: {pass_type_str}")
            
            if not session_id:
                return jsonify({'error': '세션 ID가 필요합니다.'}), 400
            
            # 채팅봇 인스턴스 가져오기
            print(f"[채팅봇 API] 세션 ID로 채팅봇 인스턴스 가져오기: {session_id}")
            chatbot = get_chatbot(session_id)
            
            # 대화 요약과 기본 정보 가져오기
            basic_prefs = chatbot.get_basic_preferences()
            conversation_summary = chatbot.get_conversation_summary()
            
            print(f"[채팅봇 API] 기본 설정: {basic_prefs}")
            print(f"[채팅봇 API] 대화 요약 길이: {len(conversation_summary) if conversation_summary else 0}")
            
            if not conversation_summary:
                return jsonify({'error': '대화가 완료되지 않았습니다.'}), 400
            
            # 패스 생성기 가져오기
            print("[채팅봇 API] 패스 생성기 가져오기")
            from pass_generator import get_pass_generator
            pass_generator = get_pass_generator()
            
            # PassType과 Theme 변환
            pass_type_mapping = {
                'light': PassType.LIGHT,
                'premium': PassType.PREMIUM,
                'citizen': PassType.CITIZEN
            }
            
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
                '해산물': Theme.SEAFOOD,
                '카페': Theme.CAFE,
                '전통': Theme.TRADITIONAL,
                '레트로': Theme.RETRO,
                '조용함': Theme.QUIET,
                '맛집': Theme.FOOD,
                '디저트': Theme.FOOD,
                '술집': Theme.FOOD,
                '문화': Theme.CULTURE,
                '쇼핑': Theme.SHOPPING
            }
            
            pass_type = pass_type_mapping.get(pass_type_str.lower(), PassType.LIGHT)
            
            # 첫 번째 관심사를 기본 테마로 사용
            first_interest = basic_prefs.get('interests', ['맛집'])[0] if basic_prefs.get('interests') else '맛집'
            theme = theme_mapping.get(first_interest.lower(), Theme.FOOD)
            
            print(f"[채팅봇 API] 패스 생성 시작 - 타입: {pass_type.value}, 테마: {theme.value}")
            print(f"[채팅봇 API] 대화 요약: {conversation_summary[:100]}...")
            
            # 품질 기준을 만족하는 패스 생성 (최대 3회 시도)
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                print(f"[채팅봇 API] 패스 생성 시도 {attempt}/{max_attempts}")
                
                # 대화 요약을 바탕으로 패스 생성
                generated_pass = pass_generator.generate_pass_from_conversation(
                    conversation_summary=conversation_summary,
                    selected_themes=basic_prefs.get('interests', []),
                    pass_type=pass_type,
                    theme=theme
                )
                
                if not generated_pass:
                    print(f"[채팅봇 API] 패스 생성 실패 - 시도 {attempt}")
                    continue
                
                # 패스 타입별 가격 정보
                pass_type_info = {
                    'light': {'name': '스탠다드 패스', 'price': 9900},
                    'premium': {'name': '프리미엄 패스', 'price': 14900},
                    'citizen': {'name': '시민 우대 패스', 'price': 7000}
                }
                
                pass_info = pass_type_info.get(generated_pass.pass_type.value, pass_type_info['light'])
                
                # 품질 검증
                from services import validate_pass_quality
                quality_result = validate_pass_quality(generated_pass, pass_info['price'])
                
                if quality_result['is_valid']:
                    print(f"[채팅봇 API] 품질 기준 충족 - 패스 생성 완료")
                    break
                else:
                    print(f"[채팅봇 API] 품질 기준 미달 - 재생성 필요 (시도 {attempt})")
                    print(f"  가치 대비 효과: {quality_result['value_ratio']:.1f}% (요구: 150% 이상)")
                    print(f"  평균 상생점수: {quality_result['avg_synergy']:.1f}점 (요구: 70점 이상)")
                    
                    if attempt == max_attempts:
                        # 최종 시도 실패 시 기존 패스라도 반환
                        print(f"[채팅봇 API] 최대 시도 횟수 초과 - 마지막 생성된 패스 반환")
                        break
            
            if not generated_pass:
                return jsonify({'error': '조건에 맞는 패스를 생성할 수 없습니다.'}), 400
            
            # 혜택 데이터에서 store_id를 실제 상점명으로 변환
            from services import load_stores_raw, load_benefits_raw
            stores_raw = load_stores_raw()
            benefits_raw = load_benefits_raw()
            
            store_id_to_name = {store['id']: store['name'] for store in stores_raw}
            
            # 혜택별 경제적 가치 맵핑
            benefit_value_map = {}
            for benefit_data in benefits_raw:
                store_id = benefit_data.get('store_id', '')
                desc = benefit_data.get('desc', '')
                eco_value = benefit_data.get('eco_value', 3000)
                benefit_value_map[f"{store_id}_{desc}"] = eco_value
            
            # AI가 생성한 상점별 선택 이유 가져오기
            store_reasons = getattr(pass_generator, 'store_reasons', {})
            
            # 혜택 정보를 프론트엔드 형식으로 변환
            recommendations = []
            enhanced_benefits = []
            
            for benefit in generated_pass.benefits:
                store_name = store_id_to_name.get(benefit.store_name, benefit.store_name)
                
                # 실제 경제적 가치 계산
                key = f"{benefit.store_name}_{benefit.description}"
                eco_value = benefit_value_map.get(key, 3000)
                
                # AI가 제공한 상점별 선택 이유 가져오기
                ai_reason = store_reasons.get(store_name, f'{store_name}에서 제공하는 사용자 맞춤 혜택입니다.')
                
                # 프론트엔드용 형식
                recommendations.append({
                    'benefit_id': f'B{len(recommendations)+1:03d}',
                    'store_name': store_name,
                    'benefit_desc': benefit.description,
                    'eco_value': eco_value,
                    'reason': ai_reason
                })
                
                # 기존 API용 형식
                enhanced_benefit = benefit.__dict__.copy()
                enhanced_benefit['store_name'] = store_name
                enhanced_benefit['ai_reason'] = ai_reason  # AI 선택 이유 추가
                enhanced_benefits.append(enhanced_benefit)
            
            # 패스 타입별 정보 설정 (이미 위에서 정의됨)
            total_value = sum(rec['eco_value'] for rec in recommendations)
            
            # 실제 상생점수 계산
            from services import calculate_average_synergy_score
            avg_synergy = calculate_average_synergy_score(generated_pass.stores)
            
            # 응답 데이터 구성
            result = {
                'success': True,
                'pass_id': generated_pass.pass_id,
                'created_at': generated_pass.created_at,
                'pass_info': {
                    'name': pass_info['name'],
                    'price': pass_info['price'],
                    'pass_type': generated_pass.pass_type.value,
                    'theme': generated_pass.theme.value,
                    'stores_count': len(generated_pass.stores),
                    'benefits_count': len(generated_pass.benefits),
                    'total_value': total_value,
                    'value_ratio': int((total_value / pass_info['price']) * 100),
                    'avg_synergy': round(avg_synergy, 1)
                },
                'stores': [store.__dict__ for store in generated_pass.stores],
                'benefits': enhanced_benefits,
                'recommendations': recommendations,
                'user_input': basic_prefs,
                'conversation_summary': {
                    'chat_history': chatbot.conversation_history,
                    'conversation_summary': conversation_summary,
                    'basic_preferences': basic_prefs
                }
            }
            
            # 생성된 패스를 저장
            try:
                from services import save_pass
                user_email = session.get('user_email', 'demo@jemulpogo.com')
                save_result = save_pass(generated_pass, user_email)
                print(f"[채팅봇 API] 패스 저장 결과: {save_result}")
            except Exception as save_error:
                print(f"[채팅봇 API] 패스 저장 실패: {save_error}")
                # 패스 저장 실패해도 결과는 반환 (사용자에게 패스는 보여줌)
            
            # 채팅 세션 정리
            clear_chatbot_session(session_id)
            
            # 응답 생성 및 쿠키 설정
            response = jsonify(result)
            
            # 쿠키에 패스 ID 백업 저장
            try:
                import json
                # 기존 쿠키에서 패스 ID 목록 가져오기
                existing_passes = request.cookies.get('user_passes', '[]')
                pass_ids = json.loads(existing_passes) if existing_passes else []
                
                # 새 패스 ID 추가 (중복 제거)
                if generated_pass.pass_id not in pass_ids:
                    pass_ids.append(generated_pass.pass_id)
                    
                # 최대 50개까지만 유지
                if len(pass_ids) > 50:
                    pass_ids = pass_ids[-50:]
                
                # 쿠키 설정 (30일 유지)
                response.set_cookie('user_passes', json.dumps(pass_ids),
                                  max_age=60*60*24*30,  # 30일
                                  secure=False,
                                  httponly=False,
                                  samesite='Lax')
                
                print(f"[채팅봇 API] 쿠키에 패스 ID 저장: {generated_pass.pass_id}")
                print(f"[채팅봇 API] 쿠키 내 총 패스 수: {len(pass_ids)}")
                
            except Exception as cookie_error:
                print(f"[채팅봇 API] 쿠키 설정 실패: {cookie_error}")
            
            return response
            
        except Exception as e:
            import traceback
            print(f"[채팅봇 API] 패스 생성 실패: {e}")
            print(f"[채팅봇 API] 상세 오류: {traceback.format_exc()}")
            return jsonify({
                'error': f'패스 생성 중 오류가 발생했습니다: {str(e)}',
                'success': False,
                'details': str(e)
            }), 500

    @app.route('/api/chat/reset', methods=['POST'])
    @login_required
    def reset_chat():
        """채팅 세션 리셋"""
        try:
            data = request.get_json()
            session_id = data.get('session_id') if data else None
            
            if session_id:
                clear_chatbot_session(session_id)
            
            return jsonify({
                'success': True,
                'message': '채팅 세션이 리셋되었습니다.'
            })
            
        except Exception as e:
            print(f"[채팅봇 API] 세션 리셋 실패: {e}")
            return jsonify({
                'error': f'세션 리셋 중 오류가 발생했습니다: {str(e)}',
                'success': False
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
            
            # 패스 생성 - 품질 기준을 만족하는 패스 생성 (최대 3회 시도)
            max_attempts = 3
            generated_pass = None
            
            for attempt in range(1, max_attempts + 1):
                print(f"[패스 생성 API] 패스 생성 시도 {attempt}/{max_attempts}")
                
                # 패스 생성
                current_pass = generate_pass(user_prefs, pass_type, theme)
                
                if not current_pass:
                    print(f"[패스 생성 API] 패스 생성 실패 - 시도 {attempt}")
                    continue
                
                # 패스 타입별 가격 정보
                pass_type_info = {
                    'light': {'name': '라이트 패스', 'price': 7900},
                    'premium': {'name': '프리미엄 패스', 'price': 14900},
                    'citizen': {'name': '시민 패스', 'price': 6900}
                }
                
                pass_info = pass_type_info.get(current_pass.pass_type.value, pass_type_info['light'])
                
                # 품질 검증
                from services import validate_pass_quality
                quality_result = validate_pass_quality(current_pass, pass_info['price'])
                
                if quality_result['is_valid']:
                    print(f"[패스 생성 API] 품질 기준 충족 - 패스 생성 완료")
                    generated_pass = current_pass
                    break
                else:
                    print(f"[패스 생성 API] 품질 기준 미달 - 재생성 필요 (시도 {attempt})")
                    print(f"  가치 대비 효과: {quality_result['value_ratio']:.1f}% (요구: 150% 이상)")
                    print(f"  평균 상생점수: {quality_result['avg_synergy']:.1f}점 (요구: 70점 이상)")
                    
                    if attempt == max_attempts:
                        # 최종 시도 실패 시 기존 패스라도 반환
                        print(f"[패스 생성 API] 최대 시도 횟수 초과 - 마지막 생성된 패스 반환")
                        generated_pass = current_pass
                        break
            
            if not generated_pass:
                return jsonify({'error': '조건에 맞는 패스를 생성할 수 없습니다.'}), 400
            
            # 혜택 데이터에서 store_id를 실제 상점명으로 변환
            from services import load_stores_raw, load_benefits_raw, calculate_average_synergy_score
            stores_raw = load_stores_raw()
            benefits_raw = load_benefits_raw()
            
            store_id_to_name = {store['id']: store['name'] for store in stores_raw}
            
            # 혜택별 경제적 가치 맵핑
            benefit_value_map = {}
            for benefit_data in benefits_raw:
                store_id = benefit_data.get('store_id', '')
                desc = benefit_data.get('desc', '')
                eco_value = benefit_data.get('eco_value', 3000)
                benefit_value_map[f"{store_id}_{desc}"] = eco_value
            
            # AI가 생성한 상점별 선택 이유 가져오기 (일반 패스 생성 API용)
            from pass_generator import get_pass_generator
            generator = get_pass_generator()
            store_reasons = getattr(generator, 'store_reasons', {})
            
            # 혜택 정보를 프론트엔드 형식으로 변환
            recommendations = []
            enhanced_benefits = []
            
            for benefit in generated_pass.benefits:
                store_name = store_id_to_name.get(benefit.store_name, benefit.store_name)
                
                # 실제 경제적 가치 계산
                key = f"{benefit.store_name}_{benefit.description}"
                eco_value = benefit_value_map.get(key, 3000)
                
                # AI가 제공한 상점별 선택 이유 가져오기
                ai_reason = store_reasons.get(store_name, f'{store_name}에서 제공하는 사용자 맞춤 혜택입니다.')
                
                # 프론트엔드용 형식
                recommendations.append({
                    'benefit_id': f'B{len(recommendations)+1:03d}',
                    'store_name': store_name,
                    'benefit_desc': benefit.description,
                    'eco_value': eco_value,
                    'reason': ai_reason
                })
                
                # 기존 API용 형식
                enhanced_benefit = benefit.__dict__.copy()
                enhanced_benefit['store_name'] = store_name
                enhanced_benefit['ai_reason'] = ai_reason  # AI 선택 이유 추가
                enhanced_benefits.append(enhanced_benefit)
            
            # 패스 타입별 정보 설정 (이미 위에서 정의됨)
            total_value = sum(rec['eco_value'] for rec in recommendations)
            
            # 실제 상생점수 계산
            avg_synergy = calculate_average_synergy_score(generated_pass.stores)
            
            print(f"[패스 정보] 패스 타입 값: {generated_pass.pass_type.value}")
            print(f"[패스 정보] 매핑된 정보: {pass_info}")
            print(f"[패스 정보] 총 혜택 가치: {total_value}")
            
            # 응답 데이터 구성 (프론트엔드가 기대하는 형식)
            result = {
                'success': True,
                'pass_id': generated_pass.pass_id,
                'created_at': generated_pass.created_at,
                'pass_info': {
                    'name': pass_info['name'],
                    'price': pass_info['price'],
                    'pass_type': generated_pass.pass_type.value,
                    'theme': generated_pass.theme.value,
                    'stores_count': len(generated_pass.stores),
                    'benefits_count': len(generated_pass.benefits),
                    'total_value': total_value,
                    'value_ratio': int((total_value / pass_info['price']) * 100),
                    'avg_synergy': round(avg_synergy, 1)
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
            
            # 응답 생성 및 쿠키 설정
            response = jsonify(result)
            
            # 쿠키에 패스 ID 백업 저장
            try:
                import json
                # 기존 쿠키에서 패스 ID 목록 가져오기
                existing_passes = request.cookies.get('user_passes', '[]')
                pass_ids = json.loads(existing_passes) if existing_passes else []
                
                # 새 패스 ID 추가 (중복 제거)
                if generated_pass.pass_id not in pass_ids:
                    pass_ids.append(generated_pass.pass_id)
                    
                # 최대 50개까지만 유지 (너무 많아지지 않도록)
                if len(pass_ids) > 50:
                    pass_ids = pass_ids[-50:]
                
                # 쿠키 설정 (30일 유지)
                response.set_cookie('user_passes', json.dumps(pass_ids),
                                  max_age=60*60*24*30,  # 30일
                                  secure=False,  # HTTP에서도 작동
                                  httponly=False,  # JavaScript에서도 접근 가능
                                  samesite='Lax')
                
                print(f"[패스 생성] 쿠키에 패스 ID 저장: {generated_pass.pass_id}")
                print(f"[패스 생성] 쿠키 내 총 패스 수: {len(pass_ids)}")
                
            except Exception as cookie_error:
                print(f"[패스 생성] 쿠키 설정 실패: {cookie_error}")
            
            return response
            
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
                    'user_prefs': pass_data.user_prefs.__dict__
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
            # 프로덕션 환경 감지
            is_production = (
                os.environ.get('GAE_ENV', '').startswith('standard') or 
                os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
                'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
            )
            
            # 세션에서 사용자 이메일 가져오기 (쿠키도 확인)
            session_email = session.get('user_email')
            cookie_email = request.cookies.get('user_email')
            
            user_email = session_email or cookie_email or 'demo@jemulpogo.com'
            
            print(f"[패스 조회 API] 프로덕션: {is_production}, 세션 이메일: {session_email}, 쿠키 이메일: {cookie_email}")
            print(f"[패스 조회 API] 사용자 이메일: {user_email}")
            
            # 쿠키에서 로그인 정보가 확인되었지만 세션에 없다면 세션에 복원
            if is_production and cookie_email and not session_email:
                print("[패스 조회 API] 쿠키에서 세션 복원 중")
                session['user_logged_in'] = True
                session['user_email'] = cookie_email
                session.permanent = True
                user_email = cookie_email
            
            user_passes = get_all_passes()
            
            print(f"[패스 조회 API] {len(user_passes)}개 패스 조회됨")
            
            return jsonify({
                'success': True,
                'passes': user_passes,
                'count': len(user_passes),
                'debug_info': {
                    'user_email': user_email,
                    'session_email': session_email,
                    'cookie_email': cookie_email,
                    'is_production': is_production,
                    'storage_types': list(set([p.get('source', 'unknown') for p in user_passes]))
                }
            })
            
        except Exception as e:
            print(f"[오류] 사용자 패스 조회 중 에러: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': f'패스 조회 중 오류가 발생했습니다: {str(e)}',
                'success': False
            }), 500

    # 혜택 특수코드 검증/사용 API
    @app.route('/api/benefits/validate', methods=['POST'])
    def validate_benefit_code():
        try:
            data = request.get_json() or {}
            code = (data.get('code') or '').strip().upper()
            if not code:
                return jsonify({'success': False, 'error': '코드가 필요합니다.'}), 400
            from services import validate_redemption_code
            info = validate_redemption_code(code)
            return jsonify({'success': True, **info})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/benefits/redeem', methods=['POST'])
    @login_required
    def redeem_benefit_code():
        try:
            data = request.get_json() or {}
            code = (data.get('code') or '').strip().upper()
            pass_id = (data.get('pass_id') or '').strip() or None
            if not code:
                return jsonify({'success': False, 'error': '코드가 필요합니다.'}), 400
            from services import redeem_code
            user_email = session.get('user_email')
            result = redeem_code(code, pass_id, user_email)
            status = 200 if result.get('success') else 400
            return jsonify(result), status
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/directions', methods=['POST'])
    def get_directions():
        """두 지점 간의 최적 경로를 반환 (도보/대중교통 통합)"""
        try:
            data = request.get_json()
            
            if not data or 'start' not in data or 'end' not in data:
                return jsonify({'error': '시작점과 끝점이 필요합니다.', 'success': False}), 400
            
            start = data['start']
            end = data['end']
            
            print(f"[통합 경로] 경로 요청: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
            
            # 입력 검증
            required_fields = ['lat', 'lng']
            for field in required_fields:
                if field not in start or field not in end:
                    return jsonify({'error': f'{field} 좌표가 필요합니다.', 'success': False}), 400
            
            # 거리 계산하여 최적 교통수단 결정
            distance = calculate_distance_server(
                float(start['lat']), float(start['lng']),
                float(end['lat']), float(end['lng'])
            )
            
            print(f"[통합 경로] 거리: {distance:.0f}m")
            
            # 거리에 따른 교통수단 자동 선택
            # 300m 미만: 도보만
            # 300m ~ 1500m: 도보 + 대중교통 비교 후 선택
            # 1500m 이상: 대중교통 우선, 도보 옵션 제공
            
            if distance < 300:
                # 짧은 거리는 도보만
                print("[통합 경로] 짧은 거리 - 도보 경로 제공")
                result = get_walking_route_with_fallback(start, end)
            elif distance < 1500:
                # 중간 거리는 도보와 대중교통 모두 제공
                print("[통합 경로] 중간 거리 - 도보/대중교통 통합 경로 제공")
                result = get_integrated_route(start, end, distance)
            else:
                # 장거리는 대중교통 중심으로 제공
                print("[통합 경로] 장거리 - 대중교통 중심 경로 제공")
                result = get_transit_route_with_walking(start, end, distance)
            
            if result:
                print(f"[통합 경로] 결과 성공: {result.get('transport_mode', 'unknown')} 모드")
                return jsonify(result)
            else:
                # 모든 API 호출 실패시 기본 경로로 대체
                print("[통합 경로] 모든 API 실패, 기본 경로로 대체")
                fallback_path = generate_smart_fallback_route(start, end, distance)
                return jsonify(fallback_path)
            
        except Exception as e:
            print(f"[통합 경로] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생시 기본 경로로 대체
            try:
                fallback_path = generate_smart_fallback_route(data['start'], data['end'], 1000)
                return jsonify(fallback_path)
            except:
                return jsonify({'error': f'경로를 가져올 수 없습니다: {str(e)}', 'success': False}), 500

    @app.route('/api/directions/car', methods=['POST'])
    def get_car_directions_api():
        """자동차 전용 경로 API (개선된 버전)"""
        try:
            data = request.get_json()
            
            if not data or 'start' not in data or 'end' not in data:
                return jsonify({'error': '시작점과 끝점이 필요합니다.', 'success': False}), 400
            
            start = data['start']
            end = data['end']
            
            # 입력 검증
            required_fields = ['lat', 'lng']
            for field in required_fields:
                if field not in start or field not in end:
                    return jsonify({'error': f'{field} 좌표가 필요합니다.', 'success': False}), 400
            
            print(f"[자동차 경로 API] 요청: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
            print(f"[자동차 경로 API] 좌표: ({start['lat']}, {start['lng']}) → ({end['lat']}, {end['lng']})")
            
            # 거리 계산
            distance = calculate_distance_server(
                float(start['lat']), float(start['lng']),
                float(end['lat']), float(end['lng'])
            )
            
            print(f"[자동차 경로 API] 거리: {distance:.0f}m")
            
            # 카카오 REST API 키 가져오기
            kakao_rest_key = os.getenv('KAKAO_REST_API_KEY', 'a3a18e7993c59985381fa9a941aa07a8')
            result = None
            
            if kakao_rest_key:
                print(f"[자동차 경로 API] 카카오 API 키 확인됨: {kakao_rest_key[:4]}...")
                # 실제 카카오 자동차 경로 API 시도
                result = get_car_directions(start, end, kakao_rest_key)
                
                if result:
                    print("[자동차 경로 API] 카카오 API 성공!")
                    return jsonify(result)
                else:
                    print("[자동차 경로 API] 카카오 API 실패, fallback 사용")
            else:
                print("[자동차 경로 API] 카카오 API 키 없음, fallback 사용")
            
            # API 실패시 자동차용 향상된 fallback 경로 생성
            fallback_result = generate_car_fallback_route(start, end, distance)
            print(f"[자동차 경로 API] fallback 결과: {fallback_result.get('success', False)}")
            return jsonify(fallback_result)
            
        except Exception as e:
            print(f"[자동차 경로 API] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생시 기본 자동차 경로로 대체
            try:
                fallback_path = generate_car_fallback_route(data['start'], data['end'], 1000)
                return jsonify(fallback_path)
            except:
                return jsonify({'error': f'자동차 경로를 가져올 수 없습니다: {str(e)}', 'success': False}), 500

    @app.route('/api/directions/walking', methods=['POST'])
    def get_walking_directions_api():
        """도보 전용 경로 API (개선된 버전)"""
        print("=" * 60)
        print("[도보 API] ✨ 새로운 요청이 도착했습니다! ✨")
        print("=" * 60)
        
        try:
            data = request.get_json()
            print(f"[도보 API] 요청 데이터: {data}")
            
            if not data or 'start' not in data or 'end' not in data:
                print("[도보 API] 에러: 시작점과 끝점이 필요합니다")
                return jsonify({'error': '시작점과 끝점이 필요합니다.', 'success': False}), 400
            
            start = data['start']
            end = data['end']
            
            # 입력 검증
            required_fields = ['lat', 'lng']
            for field in required_fields:
                if field not in start or field not in end:
                    print(f"[도보 API] 에러: {field} 좌표가 필요합니다")
                    return jsonify({'error': f'{field} 좌표가 필요합니다.', 'success': False}), 400
            
            print(f"[도보 API] 요청 경로: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
            print(f"[도보 API] 좌표: ({start['lat']}, {start['lng']}) → ({end['lat']}, {end['lng']})")
            
            # 거리 계산
            distance = calculate_distance_server(
                float(start['lat']), float(start['lng']),
                float(end['lat']), float(end['lng'])
            )
            
            print(f"[도보 API] 계산된 거리: {distance:.0f}m")
            
            # 카카오 REST API 키 가져오기
            kakao_rest_key = os.getenv('KAKAO_REST_API_KEY', 'a3a18e7993c59985381fa9a941aa07a8')
            result = None
            
            if kakao_rest_key:
                print(f"[도보 API] 카카오 API 키 확인됨: {kakao_rest_key[:4]}...")
                # 실제 카카오 도보 경로 API 시도
                result = get_walking_directions(start, end, kakao_rest_key)
                
                if result:
                    print(f"[도보 API] 🎉 카카오 API 성공! 경로점: {len(result.get('path', []))}개")
                    return jsonify(result)
                else:
                    print("[도보 API] 카카오 API 실패, 향상된 fallback 사용")
            else:
                print("[도보 API] 카카오 API 키 없음, fallback 사용")
            
            # API 실패시 도보용 향상된 fallback 경로 생성
            print("[도보 API] 🔧 향상된 fallback 경로 생성 중...")
            fallback_result = generate_walking_fallback_route(start, end, distance)
            
            if fallback_result.get('success'):
                print(f"[도보 API] ✅ Fallback 성공: {len(fallback_result.get('path', []))}개 점")
            else:
                print("[도보 API] ❌ Fallback도 실패")
                
            return jsonify(fallback_result)
            
        except Exception as e:
            print(f"[도보 API] 💥 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생시 기본 도보 경로로 대체
            try:
                print("[도보 API] 🛠️ 기본 경로로 대체 중...")
                basic_route = {
                    'success': True,
                    'transport_mode': 'walking',
                    'path': [
                        {'lat': float(data['start']['lat']), 'lng': float(data['start']['lng'])},
                        {'lat': float(data['end']['lat']), 'lng': float(data['end']['lng'])}
                    ],
                    'distance': distance if 'distance' in locals() else 500,
                    'duration': 7.5,  # 기본 시간
                    'note': '기본 직선 경로입니다. API 오류로 인해 상세 경로를 제공할 수 없습니다.'
                }
                return jsonify(basic_route)
            except:
                return jsonify({'error': f'도보 경로를 가져올 수 없습니다: {str(e)}', 'success': False}), 500

def generate_car_fallback_route(start, end, distance):
    """자동차용 향상된 도로 추정 경로 생성"""
    import math
    import random
    
    try:
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        distance_deg = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
        
        # 실제 도로 패턴을 반영한 중간점 생성
        if distance_deg > 0.003:  # 300m 이상인 경우
            # 거리에 따른 중간점 개수 조정
            if distance_deg < 0.01:  # 1km 미만
                steps = 4
            elif distance_deg < 0.02:  # 2km 미만
                steps = 6
            else:  # 2km 이상
                steps = 8
            
            # 도로의 일반적인 패턴을 고려한 경로점 생성
            for i in range(1, steps):
                ratio = i / steps
                
                # 주요 교차로나 도로 분기점을 시뮬레이션
                if i == math.floor(steps / 3) or i == math.floor(steps * 2 / 3):
                    # 주요 분기점에서 더 큰 변화
                    if abs(lat_diff) > abs(lng_diff):
                        # 남북 이동이 주요하면 먼저 위도 이동
                        curve_lat = lat_diff * (0.2 + ratio * 0.6)
                        curve_lng = lng_diff * (ratio * 0.4)
                    else:
                        # 동서 이동이 주요하면 먼저 경도 이동
                        curve_lat = lat_diff * (ratio * 0.4)
                        curve_lng = lng_diff * (0.2 + ratio * 0.6)
                    
                    # 도로의 곡률 추가
                    road_curve = math.sin(ratio * math.pi) * distance_deg * 0.1
                    noise = (random.random() - 0.5) * distance_deg * 0.05
                    
                    mid_lat = start_lat + curve_lat + road_curve + noise
                    mid_lng = start_lng + curve_lng + road_curve + noise
                else:
                    # 일반적인 도로 곡선
                    smooth_curve = math.sin(ratio * math.pi) * distance_deg * 0.08
                    road_variation = (random.random() - 0.5) * distance_deg * 0.03
                    
                    mid_lat = start_lat + lat_diff * ratio + smooth_curve + road_variation
                    mid_lng = start_lng + lng_diff * ratio + smooth_curve + road_variation
                
                path_points.append({'lat': mid_lat, 'lng': mid_lng})
        
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        # 자동차 도로 거리 및 시간 계산 (더 현실적)
        distance_meters = distance if distance else calculate_distance_server(start_lat, start_lng, end_lat, end_lng)
        
        # 도로 특성 반영
        if distance_meters < 500:  # 500m 미만 - 시내 도로
            road_factor = 1.15  # 15% 우회
            speed_kmh = 20      # 20km/h
        elif distance_meters < 2000:  # 2km 미만 - 일반 도로
            road_factor = 1.25  # 25% 우회
            speed_kmh = 30      # 30km/h
        else:  # 2km 이상 - 간선 도로
            road_factor = 1.35  # 35% 우회
            speed_kmh = 40      # 40km/h
        
        adjusted_distance = distance_meters * road_factor
        duration_minutes = (adjusted_distance / 1000) / speed_kmh * 60
        
        print(f"[자동차 fallback] 거리: {adjusted_distance:.0f}m, 시간: {duration_minutes:.1f}분, 속도: {speed_kmh}km/h")
        
        return {
            'success': True,
            'path': path_points,
            'distance': adjusted_distance,
            'duration': duration_minutes,
            'transport_mode': 'car',
            'note': '도로 패턴을 반영한 자동차 추정 경로입니다.',
            'road_info': {
                'highway_distance': 0,
                'city_road_distance': adjusted_distance,
                'estimated_speed': speed_kmh,
                'road_type': 'city' if distance_meters < 2000 else 'arterial'
            },
            'toll_info': {
                'cost': 0,
                'sections': []
            },
            'route_quality': 'enhanced_estimation'
        }
        
    except Exception as e:
        print(f"[자동차 fallback] 오류: {e}")
        return {
            'success': False,
            'error': '자동차 경로 생성 실패',
            'path': [
                {'lat': start['lat'], 'lng': start['lng']},
                {'lat': end['lat'], 'lng': end['lng']}
            ],
            'distance': distance if distance else 1000,
            'duration': 5
        }

def generate_walking_fallback_route(start, end, distance):
    """단순하고 자연스러운 도보 경로 생성"""
    import math
    
    try:
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        print(f"[도보 fallback] 시작: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
        print(f"[도보 fallback] 좌표: ({start_lat:.6f}, {start_lng:.6f}) → ({end_lat:.6f}, {end_lng:.6f})")
        
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        distance_deg = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
        
        print(f"[도보 fallback] 직선거리: {distance_deg:.6f}도 (약 {distance:.0f}m)")
        
        # 거리별 적절한 중간점 개수 (너무 많지 않게)
        if distance_deg < 0.002:  # 200m 미만
            num_segments = 2  # 1개 중간점
        elif distance_deg < 0.008:  # 800m 미만  
            num_segments = 3  # 2개 중간점
        else:  # 800m 이상
            num_segments = 4  # 3개 중간점
        
        print(f"[도보 fallback] {num_segments-1}개 중간점 생성")
        
        # 주요 이동 방향 결정
        is_lng_dominant = abs(lng_diff) > abs(lat_diff)
        
        # L자형 경로 생성 (실제 도로 패턴)
        if num_segments > 2:  # 중간점이 있는 경우
            if is_lng_dominant:
                # 동서 이동이 주요한 경우: 먼저 동서로, 나중에 남북으로
                print(f"[도보 fallback] 동서 우선 경로 (lng 변화: {lng_diff:.6f}, lat 변화: {lat_diff:.6f})")
                
                # 첫 번째 중간점: 목적지 경도까지 이동
                mid1_lat = start_lat + lat_diff * 0.2  # 20%만 위도 이동
                mid1_lng = start_lng + lng_diff * 0.8  # 80% 경도 이동
                path_points.append({'lat': mid1_lat, 'lng': mid1_lng})
                print(f"[도보 fallback] 중간점 1 (동서): ({mid1_lat:.6f}, {mid1_lng:.6f})")
                
                if num_segments > 3:  # 중간점이 2개 이상인 경우
                    # 두 번째 중간점: 남북 방향으로 조정
                    mid2_lat = start_lat + lat_diff * 0.7
                    mid2_lng = mid1_lng
                    path_points.append({'lat': mid2_lat, 'lng': mid2_lng})
                    print(f"[도보 fallback] 중간점 2 (남북): ({mid2_lat:.6f}, {mid2_lng:.6f})")
                
            else:
                # 남북 이동이 주요한 경우: 먼저 남북으로, 나중에 동서로
                print(f"[도보 fallback] 남북 우선 경로 (lat 변화: {lat_diff:.6f}, lng 변화: {lng_diff:.6f})")
                
                # 첫 번째 중간점: 목적지 위도까지 이동
                mid1_lat = start_lat + lat_diff * 0.8  # 80% 위도 이동
                mid1_lng = start_lng + lng_diff * 0.2  # 20%만 경도 이동
                path_points.append({'lat': mid1_lat, 'lng': mid1_lng})
                print(f"[도보 fallback] 중간점 1 (남북): ({mid1_lat:.6f}, {mid1_lng:.6f})")
                
                if num_segments > 3:  # 중간점이 2개 이상인 경우
                    # 두 번째 중간점: 동서 방향으로 조정
                    mid2_lat = mid1_lat
                    mid2_lng = start_lng + lng_diff * 0.7
                    path_points.append({'lat': mid2_lat, 'lng': mid2_lng})
                    print(f"[도보 fallback] 중간점 2 (동서): ({mid2_lat:.6f}, {mid2_lng:.6f})")
        
        # 끝점 추가
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        print(f"[도보 fallback] 최종 경로점 개수: {len(path_points)}개")
        
        # 거리 및 시간 계산
        distance_meters = distance if distance else calculate_distance_server(start_lat, start_lng, end_lat, end_lng)
        walking_factor = 1.15  # 15% 우회
        speed_kmh = 4.5        # 평균 도보 속도
        
        adjusted_distance = distance_meters * walking_factor
        duration_minutes = (adjusted_distance / 1000) / speed_kmh * 60
        
        print(f"[도보 fallback] 거리: {adjusted_distance:.0f}m, 시간: {duration_minutes:.1f}분")
        
        return {
            'success': True,
            'path': path_points,
            'distance': adjusted_distance,
            'duration': duration_minutes,
            'transport_mode': 'walking',
            'note': '보행자 최적화된 추정 경로입니다. 일방통행과 관계없이 이동 가능합니다.',
            'walking_info': {
                'estimated_speed': speed_kmh,
                'path_type': 'L_shape_realistic'
            },
            'route_quality': 'simple_walking_path'
        }
        
    except Exception as e:
        print(f"[도보 fallback] 오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': '도보 경로 생성 실패',
            'path': [
                {'lat': start['lat'], 'lng': start['lng']},
                {'lat': end['lat'], 'lng': end['lng']}
            ],
            'distance': distance if distance else 1000,
            'duration': 15
        }

def get_walking_route_with_fallback(start, end):
    import requests
    
    try:
        print(f"[도보 경로] 시작: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
        
        # 카카오 REST API 키 가져오기
        kakao_rest_key = os.getenv('KAKAO_REST_API_KEY')
        
        if kakao_rest_key:
            print("[도보 경로] 카카오 API 시도 중...")
            result = get_walking_directions(start, end, kakao_rest_key)
            if result:
                print("[도보 경로] 카카오 API 성공!")
                return result
            else:
                print("[도보 경로] 카카오 API 실패")
        else:
            print("[도보 경로] 카카오 API 키 없음")
        
        # API 실패시 도보 fallback 경로 생성
        print("[도보 경로] 간단한 fallback 경로 생성 중...")
        
        # 거리 계산
        distance_m = calculate_distance_server(
            float(start['lat']), float(start['lng']),
            float(end['lat']), float(end['lng'])
        )
        
        # 간단한 경로 생성
        import math
        
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        # 시작점
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        # 거리에 따라 중간점 개수 결정
        if distance_m < 200:
            waypoints = []  # 매우 짧은 거리는 직선
        elif distance_m < 800:
            waypoints = [0.33, 0.67]  # 2개 중간점
        elif distance_m < 2000:
            waypoints = [0.25, 0.5, 0.75]  # 3개 중간점
        else:
            waypoints = [0.2, 0.4, 0.6, 0.8]  # 4개 중간점
        
        # 중간점들 생성 (부드러운 곡선)
        for progress in waypoints:
            # 기본 직선상의 점
            mid_lat = start_lat + (end_lat - start_lat) * progress
            mid_lng = start_lng + (end_lng - start_lng) * progress
            
            # 자연스러운 곡선 오프셋 (매우 작게)
            curve_offset = math.sin(progress * math.pi) * distance_m * 0.000002
            
            path_points.append({
                'lat': mid_lat + curve_offset,
                'lng': mid_lng + curve_offset * 0.5
            })
        
        # 끝점
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        result = {
            'success': True,
            'transport_mode': 'walking',
            'path': path_points,
            'distance': distance_m,
            'duration': distance_m / 1000 / 4 * 60,  # 4km/h 보행속도
            'note': '보행자 최적화된 추정 경로입니다. 일방통행과 관계없이 이동 가능합니다.'
        }
        
        print(f"[도보 경로] 간단 fallback 완료: {len(path_points)}개 점")
        return result
        
    except Exception as e:
        print(f"[도보 경로] 오류: {e}")
        # 오류 시 간단한 직선 경로
        return {
            'success': True,
            'transport_mode': 'walking',
            'path': [
                {'lat': float(start['lat']), 'lng': float(start['lng'])},
                {'lat': float(end['lat']), 'lng': float(end['lng'])}
            ],
            'distance': 500,  # 기본값
            'duration': 7.5,  # 4km/h로 500m 걷는 시간
            'note': '보행자 최적화된 추정 경로입니다. 일방통행과 관계없이 이동 가능합니다.'
        }

def get_integrated_route(start, end, distance):
    """도보와 대중교통을 통합한 경로"""
    import requests
    
    try:
        # 카카오 REST API 키 가져오기
        kakao_rest_key = os.getenv('KAKAO_REST_API_KEY')
        
        # 도보 경로 시도
        walking_route = None
        transit_route = None
        
        if kakao_rest_key:
            walking_route = get_walking_directions(start, end, kakao_rest_key)
            transit_route = get_transit_directions(start, end, kakao_rest_key)
        
        # 대중교통 정류장 정보 포함한 통합 경로 생성
        if transit_route and walking_route:
            # 대중교통과 도보를 비교하여 더 나은 옵션 제공
            walking_time = walking_route.get('duration', float('inf'))
            transit_time = transit_route.get('duration', float('inf'))
            
            # 도보 시간이 대중교통보다 5분 이상 빠르면 도보 추천
            if walking_time + 5 < transit_time:
                primary_route = walking_route
                primary_route['recommended'] = True
                primary_route['reason'] = '도보가 더 빠른 경로입니다.'
                alternative_route = transit_route
                alternative_route['recommended'] = False
            else:
                # 대중교통에 도보 접근 구간 추가
                primary_route = enhance_transit_with_walking(start, end, transit_route, kakao_rest_key)
                primary_route['recommended'] = True
                primary_route['reason'] = '대중교통 이용을 권장합니다.'
                alternative_route = walking_route
                alternative_route['recommended'] = False
            
            return {
                'success': True,
                'primary_route': primary_route,
                'alternative_route': alternative_route,
                'route_type': 'integrated',
                'distance': distance
            }
        
        elif walking_route:
            # 도보만 가능한 경우
            walking_route['recommended'] = True
            walking_route['reason'] = '도보 경로만 이용 가능합니다.'
            return walking_route
        
        elif transit_route:
            # 대중교통만 가능한 경우 (도보 접근 구간 추가)
            enhanced_route = enhance_transit_with_walking(start, end, transit_route, kakao_rest_key)
            enhanced_route['recommended'] = True
            enhanced_route['reason'] = '대중교통을 이용해 주세요.'
            return enhanced_route
        
        else:
            # 모든 API 실패시 스마트 fallback
            return generate_smart_fallback_route(start, end, distance)
            
    except Exception as e:
        print(f"[통합 경로] 오류: {e}")
        return generate_smart_fallback_route(start, end, distance)

def get_transit_route_with_walking(start, end, distance):
    """대중교통 중심 경로 (도보 접근 포함)"""
    import requests
    
    try:
        # 카카오 REST API 키 가져오기
        kakao_rest_key = os.getenv('KAKAO_REST_API_KEY')
        
        if kakao_rest_key:
            # 대중교통 경로 시도
            transit_route = get_transit_directions(start, end, kakao_rest_key)
            
            if transit_route:
                # 대중교통 경로에 도보 접근 구간 추가
                enhanced_route = enhance_transit_with_walking(start, end, transit_route, kakao_rest_key)
                enhanced_route['recommended'] = True
                enhanced_route['reason'] = '장거리는 대중교통을 이용해 주세요.'
                
                # 도보 대안도 제공 (장거리 경고와 함께)
                walking_route = get_walking_directions(start, end, kakao_rest_key)
                if walking_route:
                    walking_time = walking_route.get('duration', 0)
                    walking_route['recommended'] = False
                    walking_route['warning'] = f'도보로 약 {walking_time:.0f}분 소요됩니다.'
                    
                    return {
                        'success': True,
                        'primary_route': enhanced_route,
                        'alternative_route': walking_route,
                        'route_type': 'transit_focused',
                        'distance': distance
                    }
                
                return enhanced_route
        
        # API 실패시 대중교통 fallback
        return generate_transit_fallback_with_walking(start, end, distance)
        
    except Exception as e:
        print(f"[대중교통 중심 경로] 오류: {e}")
        return generate_transit_fallback_with_walking(start, end, distance)

def enhance_transit_with_walking(start, end, transit_route, api_key):
    """대중교통 경로에 도보 접근 구간 추가"""
    try:
        # 가상의 정류장 위치 (실제로는 카카오 API에서 가져와야 함)
        # 여기서는 시작점과 끝점 사이에 중간 정류장을 추정
        start_lat, start_lng = float(start['lat']), float(start['lng'])
        end_lat, end_lng = float(end['lat']), float(end['lng'])
        
        # 시작 정류장 (시작점에서 200-300m 정도 떨어진 지점으로 추정)
        station1_lat = start_lat + (end_lat - start_lat) * 0.15
        station1_lng = start_lng + (end_lng - start_lng) * 0.15
        start_station = {'lat': station1_lat, 'lng': station1_lng, 'name': '출발 정류장'}
        
        # 도착 정류장 (끝점에서 200-300m 정도 떨어진 지점으로 추정)
        station2_lat = start_lat + (end_lat - start_lat) * 0.85
        station2_lng = start_lng + (end_lng - start_lng) * 0.85
        end_station = {'lat': station2_lat, 'lng': station2_lng, 'name': '도착 정류장'}
        
        # 전체 경로 = 시작점→출발정류장(도보) + 대중교통 + 도착정류장→끝점(도보)
        enhanced_path = []
        total_walking_distance = 0
        total_walking_duration = 0
        
        # 1. 시작점 → 출발 정류장 (도보)
        walk_to_station = generate_walking_fallback(start, start_station)
        if walk_to_station['success']:
            enhanced_path.extend(walk_to_station['path'])
            total_walking_distance += walk_to_station['distance']
            total_walking_duration += walk_to_station['duration']
        
        # 2. 대중교통 경로 (원본 경로 사용)
        if 'path' in transit_route:
            enhanced_path.extend(transit_route['path'])
        
        # 3. 도착 정류장 → 끝점 (도보)
        walk_from_station = generate_walking_fallback(end_station, end)
        if walk_from_station['success']:
            enhanced_path.extend(walk_from_station['path'])
            total_walking_distance += walk_from_station['distance']
            total_walking_duration += walk_from_station['duration']
        
        # 통합된 결과 반환
        enhanced_route = transit_route.copy()
        enhanced_route['path'] = enhanced_path
        enhanced_route['walking_distance'] = total_walking_distance
        enhanced_route['walking_duration'] = total_walking_duration
        enhanced_route['total_duration'] = transit_route.get('duration', 0) + total_walking_duration
        enhanced_route['stations'] = [start_station, end_station]
        enhanced_route['route_segments'] = [
            {'type': 'walk', 'description': '출발 정류장까지 도보'},
            {'type': 'transit', 'description': '대중교통 이용'},
            {'type': 'walk', 'description': '정류장에서 목적지까지 도보'}
        ]
        
        return enhanced_route
        
    except Exception as e:
        print(f"[대중교통 향상] 오류: {e}")
        return transit_route  # 원본 경로 반환

def generate_smart_fallback_route(start, end, distance):
    """거리에 따른 스마트 fallback 경로"""
    try:
        if distance < 300:
            # 짧은 거리: 도보만
            route = generate_walking_fallback(start, end)
            route['recommendation'] = '도보를 권장합니다.'
        elif distance < 800:
            # 중간 거리: 도보 중심, 대중교통 옵션 제공
            walking_route = generate_walking_fallback(start, end)
            walking_route['recommended'] = True
            walking_route['recommendation'] = '도보를 권장합니다.'
            
            transit_route = generate_transit_fallback(start, end)
            transit_route['recommended'] = False
            transit_route['recommendation'] = '대중교통도 이용 가능합니다.'
            
            route = {
                'success': True,
                'primary_route': walking_route,
                'alternative_route': transit_route,
                'route_type': 'smart_fallback',
                'distance': distance
            }
        else:
            # 장거리: 대중교통 중심
            route = generate_transit_fallback_with_walking(start, end, distance)
            route['recommendation'] = '대중교통을 권장합니다.'
        
        route['fallback'] = True
        route['note'] = '실제 교통 정보가 아닌 추정 경로입니다.'
        
        return route
        
    except Exception as e:
        print(f"[스마트 fallback] 오류: {e}")
        return generate_basic_fallback_route(start, end)

def generate_transit_fallback_with_walking(start, end, distance):
    """도보 접근이 포함된 대중교통 fallback"""
    try:
        # 기본 대중교통 fallback 생성
        transit_route = generate_transit_fallback(start, end)
        
        # 도보 접근 구간 추가 (가상의 정류장 추정)
        start_lat, start_lng = float(start['lat']), float(start['lng'])
        end_lat, end_lng = float(end['lat']), float(end['lng'])
        
        # 추정 정류장 위치
        station1_lat = start_lat + (end_lat - start_lat) * 0.2
        station1_lng = start_lng + (end_lng - start_lng) * 0.2
        start_station = {'lat': station1_lat, 'lng': station1_lng}
        
        station2_lat = start_lat + (end_lat - start_lat) * 0.8
        station2_lng = start_lng + (end_lng - start_lng) * 0.8
        end_station = {'lat': station2_lat, 'lng': station2_lng}
        
        # 도보 구간 거리 계산
        walk_to_station_distance = calculate_distance_server(start_lat, start_lng, station1_lat, station1_lng)
        walk_from_station_distance = calculate_distance_server(station2_lat, station2_lng, end_lat, end_lng)
        
        total_walking_distance = walk_to_station_distance + walk_from_station_distance
        total_walking_duration = total_walking_distance / 1000 * 15  # 15분/km
        
        # 향상된 경로 정보 추가
        transit_route['walking_distance'] = total_walking_distance
        transit_route['walking_duration'] = total_walking_duration
        transit_route['total_duration'] = transit_route.get('duration', 0) + total_walking_duration
        transit_route['route_segments'] = [
            {
                'type': 'walk', 
                'distance': walk_to_station_distance,
                'duration': walk_to_station_distance / 1000 * 15,
                'description': '정류장까지 도보'
            },
            {
                'type': 'transit',
                'distance': distance - total_walking_distance,
                'duration': transit_route.get('duration', 0),
                'description': '대중교통 이용'
            },
            {
                'type': 'walk',
                'distance': walk_from_station_distance,
                'duration': walk_from_station_distance / 1000 * 15,
                'description': '목적지까지 도보'
            }
        ]
        
        return transit_route
        
    except Exception as e:
        print(f"[대중교통 fallback 향상] 오류: {e}")
        return generate_transit_fallback(start, end)

def generate_basic_fallback_route(start, end):
    """최소한의 기본 경로 - 자연스러운 곡선 추가"""
    import math
    import random
    
    try:
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        distance_deg = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
        
        # 거리가 충분하면 중간점 추가 (최소한의 곡선)
        if distance_deg > 0.002:  # 200m 이상
            steps = 3  # 간단한 3점 경로
            
            for i in range(1, steps):
                ratio = i / steps
                
                # 기본 진행
                base_lat = start_lat + lat_diff * ratio
                base_lng = start_lng + lng_diff * ratio
                
                # 최소한의 자연스러운 곡선 추가
                curve = math.sin(ratio * math.pi) * distance_deg * 0.05
                variation = (random.random() - 0.5) * distance_deg * 0.02
                
                mid_lat = base_lat + curve + variation
                mid_lng = base_lng + curve + variation
                
                path_points.append({'lat': mid_lat, 'lng': mid_lng})
        
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        distance = calculate_distance_server(start_lat, start_lng, end_lat, end_lng)
        duration = distance / 1000 * 10  # 6km/h 속도로 추정
        
        return {
            'success': True,
            'path': path_points,
            'distance': distance * 1.1,  # 10% 우회 반영
            'duration': duration,
            'transport_mode': 'mixed',
            'note': '기본 추정 경로입니다.',
            'fallback': True
        }
        
    except Exception as e:
        print(f"[기본 fallback] 오류: {e}")
        return {
            'success': False,
            'error': '경로 생성 실패',
            'path': [
                {'lat': start['lat'], 'lng': start['lng']},
                {'lat': end['lat'], 'lng': end['lng']}
            ],
            'distance': 1000,
            'duration': 10
        }

def get_car_directions(start, end, api_key):
    """자동차 경로 가져오기 (카카오 Mobility API 사용)"""
    import requests
    
    try:
        print(f"[자동차 경로] API 호출 시작: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
        print(f"[자동차 경로] API 키 앞 4자리: {api_key[:4]}...")
        
        # 카카오 내비게이션 API 사용 (길찾기)
        directions_url = "https://apis-navi.kakaomobility.com/v1/directions"
        
        headers = {
            'Authorization': f'KakaoAK {api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'origin': f"{start['lng']},{start['lat']}",
            'destination': f"{end['lng']},{end['lat']}",
            'waypoints': '',
            'priority': 'RECOMMEND',  # RECOMMEND, TIME, DISTANCE
            'car_fuel': 'GASOLINE',
            'car_hipass': False,
            'alternatives': False,
            'road_details': True  # 도로 세부정보 요청
        }
        
        print(f"[자동차 경로] 요청 URL: {directions_url}")
        print(f"[자동차 경로] 요청 파라미터: {params}")
        
        response = requests.get(directions_url, headers=headers, params=params, timeout=15)
        
        print(f"[자동차 경로] 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            directions_data = response.json()
            print(f"[자동차 경로] 응답 키들: {list(directions_data.keys())}")
            
            if 'routes' in directions_data and len(directions_data['routes']) > 0:
                route = directions_data['routes'][0]
                print(f"[자동차 경로] 경로 키들: {list(route.keys())}")
                
                path_points = []
                total_distance = 0
                total_duration = 0
                total_toll = 0
                highway_distance = 0
                road_types = []
                
                if 'sections' in route:
                    print(f"[자동차 경로] {len(route['sections'])}개 섹션 처리")
                    for section_idx, section in enumerate(route['sections']):
                        section_distance = section.get('distance', 0)
                        section_duration = section.get('duration', 0)
                        section_toll = section.get('toll', 0)
                        
                        total_distance += section_distance
                        total_duration += section_duration
                        total_toll += section_toll
                        
                        print(f"[자동차 경로] 섹션 {section_idx}: {section_distance}m, {section_duration}초, 톨 {section_toll}원")
                        
                        # 도로 정보 수집
                        if 'roads' in section:
                            for road_idx, road in enumerate(section['roads']):
                                road_type = road.get('road_type', 'city')
                                road_name = road.get('name', f'도로{road_idx+1}')
                                road_distance = road.get('distance', 0)
                                
                                if road_type in ['highway', 'expressway']:
                                    highway_distance += road_distance
                                
                                road_types.append({
                                    'type': road_type,
                                    'name': road_name,
                                    'distance': road_distance
                                })
                                
                                # 경로 좌표 추출
                                if 'vertexes' in road:
                                    vertexes = road['vertexes']
                                    for i in range(0, len(vertexes), 2):
                                        if i + 1 < len(vertexes):
                                            lng = vertexes[i]
                                            lat = vertexes[i + 1]
                                            path_points.append({'lat': lat, 'lng': lng})
                                
                                print(f"[자동차 경로] 도로 {road_idx}: {road_name}, {road_type}, {road_distance}m")
                
                # 시작점과 끝점 확인
                if len(path_points) > 0:
                    first_point = path_points[0]
                    last_point = path_points[-1]
                    
                    # 시작점이 정확하지 않으면 추가
                    if abs(first_point['lat'] - start['lat']) > 0.0001 or abs(first_point['lng'] - start['lng']) > 0.0001:
                        path_points.insert(0, {'lat': start['lat'], 'lng': start['lng']})
                        print("[자동차 경로] 시작점 추가됨")
                    
                    # 끝점이 정확하지 않으면 추가
                    if abs(last_point['lat'] - end['lat']) > 0.0001 or abs(last_point['lng'] - end['lng']) > 0.0001:
                        path_points.append({'lat': end['lat'], 'lng': end['lng']})
                        print("[자동차 경로] 끝점 추가됨")
                
                if len(path_points) > 1:
                    print(f"[자동차 경로] 성공: {len(path_points)}개 점, {total_distance}m, {total_duration}초, 톨게이트: {total_toll}원")
                    
                    return {
                        'success': True,
                        'path': path_points,
                        'distance': total_distance,
                        'duration': total_duration / 60,  # 분 단위 변환
                        'transport_mode': 'car',
                        'road_info': {
                            'total_distance': total_distance,
                            'highway_distance': highway_distance,
                            'city_road_distance': total_distance - highway_distance,
                            'road_types': road_types,
                            'has_highway': highway_distance > 0
                        },
                        'toll_info': {
                            'cost': total_toll,
                            'has_toll': total_toll > 0
                        },
                        'route_quality': 'kakao_mobility_api',
                        'note': '실제 도로 정보를 기반으로 한 자동차 경로입니다.'
                    }
                else:
                    print("[자동차 경로] 경로점이 부족함")
            else:
                print("[자동차 경로] 경로 정보가 없음")
        
        elif response.status_code == 401:
            print("[자동차 경로] API 키 오류 (401)")
        elif response.status_code == 429:
            print("[자동차 경로] API 요청 한도 초과 (429)")
        else:
            print(f"[자동차 경로] API 실패: {response.status_code}")
            try:
                error_data = response.json()
                print(f"[자동차 경로] 오류 응답: {error_data}")
            except:
                print(f"[자동차 경로] 오류 응답 텍스트: {response.text[:200]}")
            
        return None
        
    except requests.exceptions.Timeout:
        print("[자동차 경로] API 시간 초과")
        return None
    except Exception as e:
        print(f"[자동차 경로] 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_walking_directions(start, end, api_key):
    """도보 경로 가져오기 - 카카오 보행자 전용 API 사용 (개선된 버전)"""
    import requests
    
    try:
        print(f"[도보 경로] API 호출 시작: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
        print(f"[도보 경로] 좌표: ({start['lat']}, {start['lng']}) → ({end['lat']}, {end['lng']})")
        print(f"[도보 경로] API 키 앞 4자리: {api_key[:4]}...")
        
        # 카카오맵 길찾기 API 사용 (도보 모드)
        walking_url = "https://apis-navi.kakaomobility.com/v1/directions"
        
        headers = {
            'Authorization': f'KakaoAK {api_key}',
            'Content-Type': 'application/json'
        }
        
        # 도보 전용 파라미터
        params = {
            'origin': f"{start['lng']},{start['lat']}",
            'destination': f"{end['lng']},{end['lat']}",
            'waypoints': '',
            'priority': 'RECOMMEND',
            'alternatives': False,
            'road_details': True,     # 경로점 상세정보 필수!
            'summary': True,
            'car_fuel': 'GASOLINE',   # 필수 파라미터
            'car_hipass': False,
        }
        
        print(f"[도보 경로] 요청 URL: {walking_url}")
        print(f"[도보 경로] 요청 파라미터: {params}")
        
        response = requests.get(walking_url, headers=headers, params=params, timeout=15)
        
        print(f"[도보 경로] 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            directions_data = response.json()
            print(f"[도보 경로] 응답 데이터 키: {list(directions_data.keys())}")
            
            if 'routes' in directions_data and len(directions_data['routes']) > 0:
                route = directions_data['routes'][0]
                print(f"[도보 경로] 경로 키들: {list(route.keys())}")
                
                path_points = []
                total_distance = 0
                total_duration = 0
                crosswalk_count = 0
                sidewalk_segments = 0
                
                if 'sections' in route:
                    print(f"[도보 경로] {len(route['sections'])}개 섹션 처리 중")
                    
                    for section_idx, section in enumerate(route['sections']):
                        section_distance = section.get('distance', 0)
                        section_duration = section.get('duration', 0)
                        
                        total_distance += section_distance
                        total_duration += section_duration
                        
                        print(f"[도보 경로] 섹션 {section_idx + 1}: {section_distance}m, {section_duration}초")
                        
                        # 도로 정보에서 보행자 경로 포인트 추출
                        if 'roads' in section:
                            print(f"[도보 경로] 섹션 {section_idx + 1}에 {len(section['roads'])}개 도로")
                            
                            for road_idx, road in enumerate(section['roads']):
                                road_name = road.get('name', '')
                                road_type = road.get('road_type', '')
                                
                                print(f"[도보 경로] 도로 {road_idx + 1}: {road_name} ({road_type})")
                                
                                # 도보 특화 정보 수집
                                if road_name and any(keyword in road_name for keyword in ['횡단보도', '보도', '육교', '지하보도']):
                                    crosswalk_count += 1
                                    print(f"[도보 경로] 횡단시설 발견: {road_name}")
                                
                                if road_type and 'sidewalk' in road_type.lower():
                                    sidewalk_segments += 1
                                
                                # 경로 좌표 추출
                                if 'vertexes' in road:
                                    vertexes = road['vertexes']
                                    point_count = len(vertexes) // 2
                                    print(f"[도보 경로] 도로 {road_idx + 1}에서 {point_count}개 점 추출")
                                    
                                    for i in range(0, len(vertexes), 2):
                                        if i + 1 < len(vertexes):
                                            lng = vertexes[i]
                                            lat = vertexes[i + 1]
                                            path_points.append({'lat': lat, 'lng': lng})
                                else:
                                    print(f"[도보 경로] 도로 {road_idx + 1}에 vertexes 없음")
                        else:
                            print(f"[도보 경로] 섹션 {section_idx + 1}에 roads 없음")
                
                # 시작점과 끝점 확인 및 추가
                if len(path_points) > 0:
                    first_point = path_points[0]
                    last_point = path_points[-1]
                    
                    # 시작점 확인
                    start_distance = abs(first_point['lat'] - start['lat']) + abs(first_point['lng'] - start['lng'])
                    if start_distance > 0.0001:  # 약 10m 이상 차이나면
                        path_points.insert(0, {'lat': start['lat'], 'lng': start['lng']})
                        print("[도보 경로] 시작점 추가됨")
                    
                    # 끝점 확인
                    end_distance = abs(last_point['lat'] - end['lat']) + abs(last_point['lng'] - end['lng'])
                    if end_distance > 0.0001:  # 약 10m 이상 차이나면
                        path_points.append({'lat': end['lat'], 'lng': end['lng']})
                        print("[도보 경로] 끝점 추가됨")
                
                # 경로점이 충분한지 확인
                if len(path_points) > 2:  # 최소 3개 점 (시작, 중간, 끝)
                    # 도보 시간을 분으로 변환 (현실적인 도보 시간으로 조정)
                    duration_minutes = max(total_duration / 60, total_distance * 0.015)  # 최소 4km/h 속도 보장
                    
                    print(f"[도보 경로] 성공 - 거리: {total_distance}m, 시간: {duration_minutes:.1f}분, 경로점: {len(path_points)}개")
                    print(f"[도보 경로] 횡단시설: {crosswalk_count}개, 보도구간: {sidewalk_segments}개")
                    
                    return {
                        'success': True,
                        'path': path_points,
                        'distance': total_distance,
                        'duration': duration_minutes,
                        'transport_mode': 'walking',
                        'walking_info': {
                            'crosswalk_count': crosswalk_count,
                            'sidewalk_segments': sidewalk_segments,
                            'estimated_speed': 4.5 if total_distance < 1000 else 4.0,  # km/h
                            'difficulty': 'easy' if total_distance < 800 else 'normal' if total_distance < 2000 else 'long',
                            'path_type': 'kakao_pedestrian_api'
                        },
                        'route_quality': 'kakao_mobility_api',
                        'note': '실제 보행자 도로를 기반으로 한 도보 경로입니다.'
                    }
                else:
                    print(f"[도보 경로] 경로점이 부족함 (점 개수: {len(path_points)})")
            else:
                print("[도보 경로] API 응답에 경로 정보 없음")
                
        elif response.status_code == 401:
            print("[도보 경로] API 키 오류 (401)")
        elif response.status_code == 429:
            print("[도보 경로] API 요청 한도 초과 (429)")
        else:
            print(f"[도보 경로] API 실패 - 상태코드: {response.status_code}")
            try:
                error_data = response.json()
                print(f"[도보 경로] 오류 응답: {error_data}")
            except:
                print(f"[도보 경로] 오류 응답 텍스트: {response.text[:200]}")
        
        return None
            
    except requests.Timeout:
        print("[도보 경로] API 시간 초과")
        return None
    except Exception as e:
        print(f"[도보 경로] 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_transit_directions(start, end, api_key):
    """대중교통 경로 가져오기"""
    import requests
    
    try:
        # 카카오 대중교통 API 사용 (별도 승인 필요)
        transit_url = "https://apis-navi.kakaomobility.com/v1/directions/transit"
        
        headers = {
            'Authorization': f'KakaoAK {api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'origin': f"{start['lng']},{start['lat']}",
            'destination': f"{end['lng']},{end['lat']}",
            'waypoints': '',
            'priority': 'RECOMMEND',
            'alternatives': False
        }
        
        print(f"[대중교통 경로] API 호출: {start.get('name', 'Unknown')} → {end.get('name', 'Unknown')}")
        
        response = requests.get(transit_url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            directions_data = response.json()
            
            if 'routes' in directions_data and len(directions_data['routes']) > 0:
                route = directions_data['routes'][0]
                
                path_points = []
                total_distance = 0
                total_duration = 0
                
                # 대중교통 경로 파싱 (구조가 다를 수 있음)
                if 'sections' in route:
                    for section in route['sections']:
                        if 'roads' in section:
                            for road in section['roads']:
                                if 'vertexes' in road:
                                    vertexes = road['vertexes']
                                    for i in range(0, len(vertexes), 2):
                                        if i + 1 < len(vertexes):
                                            lng = vertexes[i]
                                            lat = vertexes[i + 1]
                                            path_points.append({'lat': lat, 'lng': lng})
                        
                        total_distance += section.get('distance', 0)
                        total_duration += section.get('duration', 0)
                
                if len(path_points) > 0:
                    print(f"[대중교통 경로] 성공: {len(path_points)}개 점, {total_distance}m, {total_duration}초")
                    return {
                        'success': True,
                        'path': path_points,
                        'distance': total_distance,
                        'duration': total_duration / 60,
                        'transport_mode': 'transit'
                    }
        
        print(f"[대중교통 경로] API 실패: {response.status_code}, 곡선 경로로 대체")
        return generate_transit_fallback(start, end)
        
    except Exception as e:
        print(f"[대중교통 경로] 오류: {e}, 곡선 경로로 대체")
        return generate_transit_fallback(start, end)

def generate_walking_fallback(start, end):
    """도보 대체 경로 생성 - 자연스러운 보행자 경로"""
    import math
    import random
    
    print(f"[도보 fallback] 시작: 경로 생성 중...")
    
    start_lat = float(start['lat'])
    start_lng = float(start['lng'])
    end_lat = float(end['lat'])
    end_lng = float(end['lng'])
    
    path_points = [{'lat': start_lat, 'lng': start_lng}]
    
    lat_diff = end_lat - start_lat
    lng_diff = end_lng - start_lng
    distance_deg = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
    
    print(f"[도보 fallback] 거리(도): {distance_deg:.6f}")
    
    # 도보 경로는 보행자의 실제 이동 패턴을 반영
    if distance_deg > 0.001:  # 100m 이상인 경우 중간점 생성
        # 거리에 따른 중간점 개수 결정
        if distance_deg < 0.003:  # 300m 미만
            steps = 3
        elif distance_deg < 0.008:  # 800m 미만
            steps = 5
        elif distance_deg < 0.015:  # 1.5km 미만
            steps = 7
        else:  # 1.5km 이상
            steps = 9
        
        print(f"[도보 fallback] {steps}개 중간점 생성")
        
        for i in range(1, steps):
            ratio = i / steps
            
            # 보행자 특화 경로 생성
            if distance_deg > 0.005:  # 500m 이상인 경우 도시 블록 구조 반영
                # L자형 또는 지그재그 보행 패턴
                if ratio < 0.4:
                    # 전반부: 주요 방향 우선 이동
                    if abs(lat_diff) > abs(lng_diff):
                        progress_lat = lat_diff * (ratio / 0.4) * 0.8
                        progress_lng = lng_diff * (ratio / 0.4) * 0.2
                    else:
                        progress_lat = lat_diff * (ratio / 0.4) * 0.2
                        progress_lng = lng_diff * (ratio / 0.4) * 0.8
                elif ratio > 0.6:
                    # 후반부: 나머지 방향 이동
                    remaining_ratio = (ratio - 0.6) / 0.4
                    if abs(lat_diff) > abs(lng_diff):
                        progress_lat = lat_diff * 0.8 + lat_diff * 0.2 * remaining_ratio
                        progress_lng = lng_diff * 0.2 + lng_diff * 0.8 * remaining_ratio
                    else:
                        progress_lat = lat_diff * 0.2 + lat_diff * 0.8 * remaining_ratio
                        progress_lng = lng_diff * 0.8 + lng_diff * 0.2 * remaining_ratio
                else:
                    # 중간부: 교차로나 방향 전환 구간
                    intersection_ratio = (ratio - 0.4) / 0.2
                    if abs(lat_diff) > abs(lng_diff):
                        # 동서 방향으로 우회
                        detour = lng_diff * 0.3
                        progress_lat = lat_diff * 0.8
                        progress_lng = lng_diff * 0.2 + detour * math.sin(intersection_ratio * math.pi)
                    else:
                        # 남북 방향으로 우회
                        detour = lat_diff * 0.3
                        progress_lat = lat_diff * 0.2 + detour * math.sin(intersection_ratio * math.pi)
                        progress_lng = lng_diff * 0.8
            else:
                # 단거리는 자연스러운 곡선 경로
                progress_lat = lat_diff * ratio
                progress_lng = lng_diff * ratio
            
            # 보행자의 자연스러운 움직임 추가 (보도, 횡단보도 등)
            sidewalk_curve = math.sin(ratio * math.pi * 2) * distance_deg * 0.03
            pedestrian_variation = (random.random() - 0.5) * distance_deg * 0.015
            
            mid_lat = start_lat + progress_lat + sidewalk_curve + pedestrian_variation
            mid_lng = start_lng + progress_lng + sidewalk_curve + pedestrian_variation
            
            path_points.append({'lat': mid_lat, 'lng': mid_lng})
    else:
        print("[도보 fallback] 짧은 거리 - 중간점 없음")
    
    path_points.append({'lat': end_lat, 'lng': end_lng})
    
    # 도보 거리 및 시간 계산 (우회 경로 반영)
    distance_meters = calculate_distance_server(start_lat, start_lng, end_lat, end_lng)
    
    # 보행자 특성 반영
    if distance_meters < 300:
        walking_factor = 1.05  # 5% 우회
        speed_kmh = 4.8
    elif distance_meters < 800:
        walking_factor = 1.12  # 12% 우회 (횡단보도, 보행로)
        speed_kmh = 4.5
    else:
        walking_factor = 1.18  # 18% 우회 (교차로, 우회로)
        speed_kmh = 4.2
    
    adjusted_distance = distance_meters * walking_factor
    duration_minutes = (adjusted_distance / 1000) / speed_kmh * 60
    
    print(f"[도보 fallback] 완료: {len(path_points)}개 점, {adjusted_distance:.0f}m, {duration_minutes:.1f}분")
    
    return {
        'success': True,
        'path': path_points,
        'distance': adjusted_distance,
        'duration': duration_minutes,
        'transport_mode': 'walk',
        'note': '보행자 패턴을 반영한 도보 추정 경로입니다.',
        'walking_info': {
            'path_type': 'enhanced_pedestrian',
            'difficulty': 'easy' if distance_meters < 500 else 'normal' if distance_meters < 1500 else 'long',
            'estimated_speed': speed_kmh
        }
    }

def generate_transit_fallback(start, end):
    """대중교통 대체 경로 생성"""
    import math
    import random
    
    start_lat = float(start['lat'])
    start_lng = float(start['lng'])
    end_lat = float(end['lat'])
    end_lng = float(end['lng'])
    
    path_points = [{'lat': start_lat, 'lng': start_lng}]
    
    lat_diff = end_lat - start_lat
    lng_diff = end_lng - start_lng
    distance = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
    
    # 대중교통은 우회할 수 있으므로 약간 곡선으로
    if distance > 0.005:  # 약 500m 이상
        steps = min(6, max(3, int(distance * 600)))
        
        for i in range(1, steps):
            ratio = i / steps
            
            # 대중교통 특성상 약간의 우회 경로
            curvature = math.sin(ratio * math.pi) * distance * 0.2
            offset_lat = (random.random() - 0.5) * curvature
            offset_lng = (random.random() - 0.5) * curvature
            
            mid_lat = start_lat + lat_diff * ratio + offset_lat
            mid_lng = start_lng + lng_diff * ratio + offset_lng
            path_points.append({'lat': mid_lat, 'lng': mid_lng})
    
    path_points.append({'lat': end_lat, 'lng': end_lng})
    
    # 대중교통 거리 및 시간 계산
    distance_meters = calculate_distance_server(start_lat, start_lng, end_lat, end_lng)
    # 대중교통은 우회 + 대기시간 고려하여 1.5배 거리, 시간은 더 복잡
    adjusted_distance = distance_meters * 1.3
    duration_minutes = distance_meters / 1000 * 8  # 대중교통: 약 7.5km/h + 대기시간
    
    return {
        'success': True,
        'path': path_points,
        'distance': adjusted_distance,
        'duration': duration_minutes,
        'transport_mode': 'transit',
        'note': '대중교통 추정 경로입니다.'
    }

def calculate_distance_server(lat1, lng1, lat2, lng2):
    """서버에서 거리 계산"""
    import math
    
    R = 6371000  # 지구 반지름 (미터)
    dLat = math.radians(lat2 - lat1)
    dLng = math.radians(lng2 - lng1)
    a = (math.sin(dLat/2) * math.sin(dLat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dLng/2) * math.sin(dLng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def generate_curved_path_server(start, end, transport_mode='car'):
    """서버에서 곡선 경로 생성"""
    import math
    import random
    
    try:
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        distance = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
        
        # 거리가 충분히 긴 경우에만 중간점 추가
        if distance > 0.005:  # 약 500m 이상
            steps = min(8, max(3, int(distance * 800)))  # 3-8개 중간점
            
            for i in range(1, steps):
                ratio = i / steps
                
                # 약간의 곡률을 주기 위한 오프셋
                curvature = math.sin(ratio * math.pi) * distance * 0.05
                offset_lat = (random.random() - 0.5) * curvature
                offset_lng = (random.random() - 0.5) * curvature
                
                mid_lat = start_lat + lat_diff * ratio + offset_lat
                mid_lng = start_lng + lng_diff * ratio + offset_lng
                
                path_points.append({'lat': mid_lat, 'lng': mid_lng})
        
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        # 거리 계산 (Haversine formula)
        def calculate_distance_server(lat1, lng1, lat2, lng2):
            R = 6371000  # 지구 반지름 (미터)
            dLat = math.radians(lat2 - lat1)
            dLng = math.radians(lng2 - lng1)
            a = (math.sin(dLat/2) * math.sin(dLat/2) + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dLng/2) * math.sin(dLng/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        total_distance = calculate_distance_server(start_lat, start_lng, end_lat, end_lng)
        total_duration = total_distance / 1000 * 3  # 3분/km로 추정
        
        print(f"[경로 생성] 곡선 경로: {len(path_points)}개 점, {total_distance:.0f}m, {total_duration:.1f}분")
        
        return {
            'success': True,
            'path': path_points,
            'distance': total_distance,
            'duration': total_duration,
            'note': '실제 도로 정보가 아닌 추정 경로입니다.'
        }
        
    except Exception as e:
        print(f"[경로 생성] 곡선 경로 생성 실패: {e}")
        return {
            'success': False,
            'error': '경로 생성 실패',
            'path': [
                {'lat': start['lat'], 'lng': start['lng']},
                {'lat': end['lat'], 'lng': end['lng']}
            ],
            'distance': 1000,  # 기본값
            'duration': 3      # 기본값
        }

    # 길찾기 API 엔드포인트 추가
    @app.route('/api/directions/car', methods=['POST'])
    def get_car_directions():
        """자동차 길찾기 API"""
        try:
            data = request.get_json()
            start = data.get('start')
            end = data.get('end')
            
            if not start or not end:
                return jsonify({
                    'success': False,
                    'error': '출발지와 도착지가 필요합니다.'
                })
            
            # 카카오 길찾기 API 시도
            kakao_result = try_kakao_directions(start, end, 'car')
            
            if kakao_result['success']:
                return jsonify(kakao_result)
            else:
                # 카카오 API 실패 시 향상된 시뮬레이션 사용
                enhanced_result = generate_enhanced_car_route(start, end)
                return jsonify(enhanced_result)
                
        except Exception as e:
            print(f"[자동차 길찾기] 오류: {e}")
            return jsonify({
                'success': False,
                'error': '길찾기 서비스 오류',
                'path': [
                    {'lat': start.get('lat', 37.4755), 'lng': start.get('lng', 126.6166)},
                    {'lat': end.get('lat', 37.4755), 'lng': end.get('lng', 126.6166)}
                ]
            })

    @app.route('/api/directions/walking', methods=['POST'])
    def get_walking_directions():
        """도보 길찾기 API"""
        try:
            data = request.get_json()
            start = data.get('start')
            end = data.get('end')
            
            if not start or not end:
                return jsonify({
                    'success': False,
                    'error': '출발지와 도착지가 필요합니다.'
                })
            
            # 카카오 길찾기 API 시도
            kakao_result = try_kakao_directions(start, end, 'walking')
            
            if kakao_result['success']:
                return jsonify(kakao_result)
            else:
                # 카카오 API 실패 시 향상된 시뮬레이션 사용
                enhanced_result = generate_enhanced_walking_route(start, end)
                return jsonify(enhanced_result)
                
        except Exception as e:
            print(f"[도보 길찾기] 오류: {e}")
            return jsonify({
                'success': False,
                'error': '길찾기 서비스 오류',
                'path': [
                    {'lat': start.get('lat', 37.4755), 'lng': start.get('lng', 126.6166)},
                    {'lat': end.get('lat', 37.4755), 'lng': end.get('lng', 126.6166)}
                ]
            })

def try_kakao_directions(start, end, mode):
    """카카오 길찾기 API 시도"""
    try:
        import requests
        import os
        
        # 카카오 REST API 키 가져오기
        kakao_rest_key = os.getenv('KAKAO_REST_API_KEY')
        
        if not kakao_rest_key:
            return {'success': False, 'error': 'API 키 없음'}
        
        # 카카오 길찾기 API 호출
        if mode == 'car':
            # 자동차 길찾기
            url = 'https://apis-navi.kakaomobility.com/v1/directions'
            headers = {
                'Authorization': f'KakaoAK {kakao_rest_key}',
                'Content-Type': 'application/json'
            }
            params = {
                'origin': f"{start['lng']},{start['lat']}",
                'destination': f"{end['lng']},{end['lat']}",
                'priority': 'RECOMMEND',  # 추천 경로
                'car_fuel': 'GASOLINE',
                'car_hipass': False,
                'alternatives': False,
                'road_details': False
            }
            
        else:  # walking
            # 도보 길찾기는 다른 API 사용
            url = 'https://apis-navi.kakaomobility.com/v1/waypoints/directions'
            headers = {
                'Authorization': f'KakaoAK {kakao_rest_key}',
                'Content-Type': 'application/json'
            }
            params = {
                'origin': f"{start['lng']},{start['lat']}",
                'destination': f"{end['lng']},{end['lat']}",
                'waypoints': '',
                'priority': 'RECOMMEND',
                'avoid': '',
                'alternatives': False
            }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('routes'):
                route = result['routes'][0]
                
                # 경로점 추출
                path_points = []
                sections = route.get('sections', [])
                
                for section in sections:
                    roads = section.get('roads', [])
                    for road in roads:
                        vertexes = road.get('vertexes', [])
                        # 좌표는 [lng, lat, lng, lat, ...] 형태로 제공됨
                        for i in range(0, len(vertexes), 2):
                            if i + 1 < len(vertexes):
                                path_points.append({
                                    'lat': vertexes[i + 1],
                                    'lng': vertexes[i]
                                })
                
                if not path_points:
                    # 경로점이 없으면 시작점과 끝점만 사용
                    path_points = [
                        {'lat': start['lat'], 'lng': start['lng']},
                        {'lat': end['lat'], 'lng': end['lng']}
                    ]
                
                # 거리와 시간 정보 추출
                summary = route.get('summary', {})
                distance = summary.get('distance', 0)  # 미터
                duration = summary.get('duration', 0) / 60  # 분 단위로 변환
                
                return {
                    'success': True,
                    'path': path_points,
                    'distance': distance,
                    'duration': duration,
                    'source': 'kakao_api'
                }
        
        return {'success': False, 'error': f'API 응답 오류: {response.status_code}'}
        
    except Exception as e:
        print(f"[카카오 API] 길찾기 실패: {e}")
        return {'success': False, 'error': str(e)}

def generate_enhanced_car_route(start, end):
    """향상된 자동차 경로 시뮬레이션"""
    import math
    import random
    
    try:
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        distance = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
        
        # 자동차는 도로를 따라 이동하므로 더 복잡한 경로 생성
        if distance > 0.01:  # 1km 이상인 경우
            steps = min(10, max(5, int(distance * 1000)))
            
            for i in range(1, steps):
                ratio = i / steps
                
                # 도시 격자형 도로망을 고려한 L자형 경로
                if ratio < 0.3:
                    # 초반: 주요 도로 따라 한 방향 우선
                    if abs(lat_diff) > abs(lng_diff):
                        mid_lat = start_lat + lat_diff * (ratio / 0.3) * 0.8
                        mid_lng = start_lng + lng_diff * (ratio / 0.3) * 0.2
                    else:
                        mid_lat = start_lat + lat_diff * (ratio / 0.3) * 0.2
                        mid_lng = start_lng + lng_diff * (ratio / 0.3) * 0.8
                elif ratio > 0.7:
                    # 후반: 나머지 방향으로
                    adjusted_ratio = (ratio - 0.7) / 0.3
                    if abs(lat_diff) > abs(lng_diff):
                        mid_lat = start_lat + lat_diff * 0.8 + lat_diff * 0.2 * adjusted_ratio
                        mid_lng = start_lng + lng_diff * 0.2 + lng_diff * 0.8 * adjusted_ratio
                    else:
                        mid_lat = start_lat + lat_diff * 0.2 + lat_diff * 0.8 * adjusted_ratio
                        mid_lng = start_lng + lng_diff * 0.8 + lng_diff * 0.2 * adjusted_ratio
                else:
                    # 중간: 교차로 회전 시뮬레이션
                    turn_ratio = (ratio - 0.3) / 0.4
                    if abs(lat_diff) > abs(lng_diff):
                        detour = lng_diff * 0.3 * math.sin(turn_ratio * math.pi)
                        mid_lat = start_lat + lat_diff * 0.8
                        mid_lng = start_lng + lng_diff * 0.2 + detour
                    else:
                        detour = lat_diff * 0.3 * math.sin(turn_ratio * math.pi)
                        mid_lat = start_lat + lat_diff * 0.2 + detour
                        mid_lng = start_lng + lng_diff * 0.8
                
                # 약간의 랜덤 변화 (도로의 곡률 반영)
                mid_lat += (random.random() - 0.5) * distance * 0.05
                mid_lng += (random.random() - 0.5) * distance * 0.05
                
                path_points.append({'lat': mid_lat, 'lng': mid_lng})
        
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        # 거리와 시간 계산
        total_distance = calculate_haversine_distance_server(start_lat, start_lng, end_lat, end_lng) * 1000
        total_distance *= 1.3  # 도로 우회 고려 (30% 증가)
        total_duration = total_distance / 1000 / 30 * 60  # 30km/h 평균속도
        
        return {
            'success': True,
            'path': path_points,
            'distance': total_distance,
            'duration': total_duration,
            'source': 'enhanced_simulation'
        }
        
    except Exception as e:
        print(f"[향상된 자동차 경로] 생성 실패: {e}")
        return {
            'success': False,
            'error': '경로 생성 실패'
        }

def generate_enhanced_walking_route(start, end):
    """향상된 도보 경로 시뮬레이션"""
    import math
    import random
    
    try:
        start_lat = float(start['lat'])
        start_lng = float(start['lng'])
        end_lat = float(end['lat'])
        end_lng = float(end['lng'])
        
        path_points = [{'lat': start_lat, 'lng': start_lng}]
        
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        distance = math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
        
        # 도보는 보행로를 따라 이동
        if distance > 0.005:  # 500m 이상인 경우
            steps = min(8, max(3, int(distance * 800)))
            
            for i in range(1, steps):
                ratio = i / steps
                
                # 보행자는 인도를 따라 이동
                if distance > 0.008:  # 800m 이상: 보행자용 L자 경로
                    if ratio < 0.4:
                        # 전반부: 주요 방향 우선
                        if abs(lat_diff) > abs(lng_diff):
                            mid_lat = start_lat + lat_diff * (ratio / 0.4) * 0.75
                            mid_lng = start_lng + lng_diff * (ratio / 0.4) * 0.25
                        else:
                            mid_lat = start_lat + lat_diff * (ratio / 0.4) * 0.25
                            mid_lng = start_lng + lng_diff * (ratio / 0.4) * 0.75
                    elif ratio > 0.6:
                        # 후반부: 나머지 방향
                        remaining_ratio = (ratio - 0.6) / 0.4
                        if abs(lat_diff) > abs(lng_diff):
                            mid_lat = start_lat + lat_diff * 0.75 + lat_diff * 0.25 * remaining_ratio
                            mid_lng = start_lng + lng_diff * 0.25 + lng_diff * 0.75 * remaining_ratio
                        else:
                            mid_lat = start_lat + lat_diff * 0.25 + lat_diff * 0.75 * remaining_ratio
                            mid_lng = start_lng + lng_diff * 0.75 + lng_diff * 0.25 * remaining_ratio
                    else:
                        # 중간부: 횡단보도 구간
                        intersection_ratio = (ratio - 0.4) / 0.2
                        if abs(lat_diff) > abs(lng_diff):
                            crosswalk = lng_diff * 0.2 * math.sin(intersection_ratio * math.pi)
                            mid_lat = start_lat + lat_diff * 0.75
                            mid_lng = start_lng + lng_diff * 0.25 + crosswalk
                        else:
                            crosswalk = lat_diff * 0.2 * math.sin(intersection_ratio * math.pi)
                            mid_lat = start_lat + lat_diff * 0.25 + crosswalk
                            mid_lng = start_lng + lng_diff * 0.75
                else:
                    # 단거리: 자연스러운 보행
                    base_lat = start_lat + lat_diff * ratio
                    base_lng = start_lng + lng_diff * ratio
                    
                    # 보행로 곡선 반영
                    sidewalk_curve = math.sin(ratio * math.pi * 1.5) * distance * 0.05
                    minor_variation = (random.random() - 0.5) * distance * 0.02
                    
                    mid_lat = base_lat + sidewalk_curve + minor_variation
                    mid_lng = base_lng + sidewalk_curve + minor_variation
                
                path_points.append({'lat': mid_lat, 'lng': mid_lng})
        
        path_points.append({'lat': end_lat, 'lng': end_lng})
        
        # 거리와 시간 계산
        total_distance = calculate_haversine_distance_server(start_lat, start_lng, end_lat, end_lng) * 1000
        total_distance *= 1.15  # 보행자 우회 고려 (15% 증가)
        total_duration = total_distance / 1000 / 4 * 60  # 4km/h 평균속도
        
        return {
            'success': True,
            'path': path_points,
            'distance': total_distance,
            'duration': total_duration,
            'source': 'enhanced_simulation'
        }
        
    except Exception as e:
        print(f"[향상된 도보 경로] 생성 실패: {e}")
        return {
            'success': False,
            'error': '경로 생성 실패'
        }

def calculate_haversine_distance_server(lat1, lng1, lat2, lng2):
    """Haversine 거리 계산 (킬로미터)"""
    import math
    
    R = 6371  # 지구 반지름 (km)
    dLat = math.radians(lat2 - lat1)
    dLng = math.radians(lng2 - lng1)
    a = (math.sin(dLat/2) * math.sin(dLat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dLng/2) * math.sin(dLng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
