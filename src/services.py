"""
비즈니스 로직 및 서비스 (패스 생성 제외)
패스 생성 기능은 pass_generator.py 모듈로 분리되었습니다.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from models import Store, Benefit, UserPrefs, Pass, PassType, Theme
import hashlib
from pass_generator import generate_pass  # 패스 생성 모듈 임포트

# 환경 변수 로드
load_dotenv()

def load_stores() -> List[Store]:
    """상점 데이터 로드"""
    try:
        stores_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stores.json')
        with open(stores_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # JSON 구조가 {"stores": [...]} 형태인 경우
            if 'stores' in data:
                stores_data = data['stores']
            else:
                stores_data = data
            
            stores = []
            for store_data in stores_data:
                # JSON 필드를 Store 모델에 맞게 변환
                store = Store(
                    name=store_data.get('name', ''),
                    category=store_data.get('category', ''),
                    address=store_data.get('address', ''),
                    phone=store_data.get('phone', ''),
                    description=store_data.get('desc', store_data.get('description', '')),
                    rating=float(store_data.get('rating', 0)),
                    price_range=store_data.get('price_range', '보통'),
                    opening_hours=store_data.get('opening_hours', '09:00-21:00'),
                    menu_highlights=store_data.get('menu_highlights', []),
                    location=store_data.get('area', store_data.get('location', '')),
                    latitude=store_data.get('latitude'),
                    longitude=store_data.get('longitude'),
                    image_url=store_data.get('image_url', '')
                )
                stores.append(store)
            return stores
    except FileNotFoundError:
        print("stores.json 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"상점 데이터 로드 중 오류: {e}")
        return []

def load_stores_raw() -> List[Dict]:
    """상점 원본 데이터 로드 (ID 포함)"""
    try:
        stores_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stores.json')
        with open(stores_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # JSON 구조가 {"stores": [...]} 형태인 경우
            if 'stores' in data:
                return data['stores']
            else:
                return data
    except FileNotFoundError:
        print("stores.json 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"상점 데이터 로드 중 오류: {e}")
        return []

def load_benefits() -> List[Benefit]:
    """혜택 데이터 로드"""
    try:
        benefits_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'benefits.json')
        with open(benefits_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # JSON 구조가 {"benefits": [...]} 형태인 경우
            if 'benefits' in data:
                benefits_data = data['benefits']
            else:
                benefits_data = data
            
            benefits = []
            for benefit_data in benefits_data:
                # JSON 필드를 Benefit 모델에 맞게 변환
                benefit = Benefit(
                    store_name=benefit_data.get('store_id', ''),  # store_id를 store_name으로 사용
                    benefit_type=benefit_data.get('benefit_type', '할인'),
                    description=benefit_data.get('desc', benefit_data.get('description', '')),
                    discount_rate=benefit_data.get('discount_rate'),
                    valid_until=benefit_data.get('valid_until'),
                    terms=benefit_data.get('terms')
                )
                benefits.append(benefit)
            return benefits
    except FileNotFoundError:
        print("benefits.json 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"혜택 데이터 로드 중 오류: {e}")
        return []

def load_themes() -> Dict[str, Any]:
    """테마 데이터 로드"""
    try:
        themes_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'themes.json')
        with open(themes_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("themes.json 파일을 찾을 수 없습니다.")
        return {}
    except Exception as e:
        print(f"테마 데이터 로드 중 오류: {e}")
        return {}

def _stable_redemption_code(source: str) -> str:
    """입력 문자열 기반으로 안정적인 8자 코드 생성(대문자+숫자), XXXX-XXXX 형식"""
    digest = hashlib.sha1(source.encode('utf-8')).hexdigest().upper()
    # 영숫자만 사용, 앞 8자
    code = ''.join(ch for ch in digest if ch.isalnum())[:8]
    return f"{code[:4]}-{code[4:8]}"


def _attach_redemption_codes(benefits: List[Benefit]) -> None:
    """각 혜택에 전역 고정 특수코드 부여(입력 데이터 기반 안정적 생성)"""
    for b in benefits:
        # store_name에는 현재 store_id가 들어있음(load_benefits 구현 참고)
        source = f"{b.store_name}|{b.benefit_type}|{b.description}"
        b.redemption_code = _stable_redemption_code(source)


def _redemptions_path() -> str:
    return os.path.join(os.path.dirname(__file__), '..', 'storage', 'redemptions.json')


def load_redemptions() -> Dict[str, Any]:
    """전역 혜택 코드 사용 내역 로드"""
    path = _redemptions_path()
    if not os.path.exists(path):
        return {"used": {}}  # { code: { used_at, used_by, pass_id? }}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'used' not in data:
                data = {"used": {}}
            return data
    except Exception:
        return {"used": {}}


def save_redemptions(data: Dict[str, Any]) -> bool:
    """전역 혜택 코드 사용 내역 저장"""
    try:
        path = _redemptions_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def validate_redemption_code(code: str) -> Dict[str, Any]:
    """코드 유효성 및 사용 여부 확인"""
    all_benefits = load_benefits()
    # 코드 부여
    _attach_redemption_codes(all_benefits)
    benefit_map = {b.redemption_code: b for b in all_benefits if b.redemption_code}
    info = {"valid": False, "used": False}
    if code not in benefit_map:
        return info
    redemptions = load_redemptions()
    info.update({
        "valid": True,
        "used": code in redemptions.get('used', {}),
        "benefit": {
            "store_name": benefit_map[code].store_name,
            "benefit_type": benefit_map[code].benefit_type,
            "description": benefit_map[code].description,
        }
    })
    if info["used"]:
        info["used_info"] = redemptions['used'][code]
    return info


def redeem_code(code: str, pass_id: Optional[str], user_email: Optional[str]) -> Dict[str, Any]:
    """코드를 사용 처리(전역 1회성)
    - code가 유효하면 사용 처리
    - 이미 사용된 경우 used=true 반환
    """
    result = validate_redemption_code(code)
    if not result.get('valid'):
        return {"success": False, "error": "invalid_code"}
    redemptions = load_redemptions()
    if code in redemptions.get('used', {}):
        return {"success": True, "used": True, "used_info": redemptions['used'][code]}
    # 사용 처리
    redemptions.setdefault('used', {})[code] = {
        "used_at": datetime.now().isoformat(),
        "used_by": user_email,
        "pass_id": pass_id,
    }
    save_redemptions(redemptions)
    return {"success": True, "used": True}

# 패스 생성 기능은 pass_generator.py 모듈로 이동되었습니다.
# 기존 generate_pass, save_pass_to_file 함수들은 pass_generator.py에서 처리합니다.

def save_pass(pass_obj: Pass, user_email: str) -> Dict[str, Any]:
    """패스를 여러 저장소에 저장 (파일 + Datastore + 세션)"""
    try:
        from pass_generator import get_pass_generator
        generator = get_pass_generator()
        
        # 프로덕션 환경 감지
        is_production = (
            os.environ.get('GAE_ENV', '').startswith('standard') or 
            os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
            'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
        )
        
        print(f"[패스 저장] 프로덕션 환경: {is_production}")
        print(f"[패스 저장] 패스 ID: {pass_obj.pass_id}")
        print(f"[패스 저장] 사용자: {user_email}")
        
        # 1. 파일 시스템 저장 시도
        file_success = generator.save_pass_to_file(pass_obj)
        print(f"[패스 저장] 파일 저장 결과: {file_success}")
        
        # 2. Datastore 저장 (프로덕션 환경에서 영구 저장)
        datastore_success = False
        if is_production:
            try:
                try:
                    from src.datastore_service import save_pass_to_datastore
                except ImportError:
                    from datastore_service import save_pass_to_datastore
                print(f"[패스 저장] Datastore 저장 시작")
                datastore_success = save_pass_to_datastore(pass_obj, user_email)
                print(f"[패스 저장] Datastore 저장 결과: {datastore_success}")
            except Exception as datastore_error:
                print(f"[패스 저장] Datastore 저장 실패: {datastore_error}")
                import traceback
                print(f"[패스 저장] Datastore 오류 세부사항: {traceback.format_exc()}")
        
        # 3. 세션에 패스 저장 (즉시 접근용) - 모든 환경에서 실행
        session_success = False
        try:
            from flask import session
            
            # 패스 데이터를 직렬화 가능한 형태로 변환
            pass_data = {
                'pass_id': pass_obj.pass_id,
                'pass_type': pass_obj.pass_type.value,
                'theme': pass_obj.theme.value,
                'stores': [store.__dict__ for store in pass_obj.stores],
                'benefits': [benefit.__dict__ for benefit in pass_obj.benefits],
                'created_at': pass_obj.created_at,
                'user_prefs': pass_obj.user_prefs.__dict__,
                'user_email': user_email,
                'saved_via': 'session'
            }
            
            # 기존 세션 패스 목록 가져오기
            saved_passes = session.get('saved_passes', [])
            
            # 중복 제거
            saved_passes = [p for p in saved_passes if p.get('pass_id') != pass_obj.pass_id]
            
            # 새 패스 추가
            saved_passes.append(pass_data)
            
            # 최대 50개까지만 유지
            if len(saved_passes) > 50:
                saved_passes = saved_passes[-50:]
            
            # 세션에 저장
            session['saved_passes'] = saved_passes
            session.permanent = True  # 🚨 중요: SECRET_KEY 고정과 함께 영구 세션 보장
            session_success = True
            print(f"[패스 저장] 세션 저장 성공: 총 {len(saved_passes)}개 패스")
            
        except Exception as session_error:
            print(f"[패스 저장] 세션 저장 실패: {session_error}")
            import traceback
            print(f"[패스 저장] 세션 오류 세부사항: {traceback.format_exc()}")
        
        # 전체 저장 결과 계산
        overall_success = file_success or datastore_success or session_success
        
        result = {
            'file_success': file_success,
            'datastore_success': datastore_success,
            'session_success': session_success,
            'overall_success': overall_success,
            'is_production': is_production,
            'pass_id': pass_obj.pass_id,
            'user_email': user_email
        }
        
        print(f"[패스 저장] 최종 결과: {result}")
        return result
        
    except Exception as e:
        print(f"[패스 저장] 전체 실패: {e}")
        import traceback
        traceback.print_exc()
        return {
            'file_success': False,
            'datastore_success': False, 
            'session_success': False,
            'overall_success': False,
            'error': str(e)
        }

def load_pass_from_file(pass_id: str) -> Optional[Pass]:
    """파일에서 패스 로드 (프로덕션 환경에서는 Datastore와 세션에서도 조회)"""
    try:
        print(f"[패스 로드] 패스 ID: {pass_id}")
        
        # 프로덕션 환경 감지
        is_production = (
            os.environ.get('GAE_ENV', '').startswith('standard') or 
            os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
            'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
        )
        
        print(f"[패스 로드] 프로덕션 환경: {is_production}")
        
        # 프로덕션 환경에서는 먼저 Datastore에서 찾기
        if is_production:
            try:
                try:
                    from src.datastore_service import load_pass_from_datastore
                except ImportError:
                    from datastore_service import load_pass_from_datastore
                print(f"[패스 로드] Datastore 조회 시작: {pass_id}")
                datastore_pass = load_pass_from_datastore(pass_id)
                if datastore_pass:
                    print(f"[패스 로드] Datastore에서 패스 발견: {pass_id}")
                    return datastore_pass
                print(f"[패스 로드] Datastore에서 패스를 찾을 수 없음: {pass_id}")
            except Exception as datastore_error:
                print(f"[패스 로드] Datastore 조회 실패: {datastore_error}")
                import traceback
                print(f"[패스 로드] Datastore 오류 세부사항: {traceback.format_exc()}")
        
        # 프로덕션 환경에서는 세션에서도 찾기 (백업)
        if is_production:
            try:
                from flask import session
                session_passes = session.get('saved_passes', [])
                print(f"[패스 로드] 세션에서 {len(session_passes)}개 패스 확인 중...")
                
                for pass_data in session_passes:
                    if pass_data.get('pass_id') == pass_id:
                        print(f"[패스 로드] 세션에서 패스 발견: {pass_id}")
                        return _create_pass_from_data(pass_data)
                        
                print(f"[패스 로드] 세션에서 패스를 찾을 수 없음: {pass_id}")
                        
            except Exception as session_error:
                print(f"[패스 로드] 세션 접근 오류: {session_error}")
        
        # 파일 시스템에서 찾기
        filename = f"pass_{pass_id}.json"
        saved_passes_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'saved_passes')
        filepath = os.path.join(saved_passes_dir, filename)
        
        print(f"[패스 로드] 파일 경로: {filepath}")
        print(f"[패스 로드] 파일 존재: {os.path.exists(filepath)}")
        
        if not os.path.exists(filepath):
            print(f"[패스 로드] 파일을 찾을 수 없음: {pass_id}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            pass_data = json.load(f)
        
        print(f"[패스 로드] 파일에서 패스 발견: {pass_id}")
        return _create_pass_from_data(pass_data)
        
    except Exception as e:
        print(f"[패스 로드] 오류: {e} (패스 ID: {pass_id})")
        import traceback
        traceback.print_exc()
        return None

def _create_pass_from_data(pass_data: dict) -> Optional[Pass]:
    """패스 데이터 딕셔너리에서 Pass 객체 생성"""
    try:
        # 호환성을 위한 데이터 구조 확인
        if 'stores' not in pass_data:
            print(f"패스 생성 오류: stores 필드 없음")
            return None
            
        if 'benefits' not in pass_data:
            print(f"패스 생성 오류: benefits 필드 없음")
            return None
        
        # PassType 호환성 확인
        pass_type_str = pass_data.get('pass_type', 'light')
        try:
            pass_type = PassType(pass_type_str)
        except ValueError:
            # 유효하지 않은 PassType은 light로 변환
            print(f"패스 생성 경고: 유효하지 않은 패스 타입 '{pass_type_str}' -> 'light'로 변환")
            pass_type = PassType.LIGHT
        
        # Theme 호환성 확인  
        theme_str = pass_data.get('theme', '음식')
        try:
            theme = Theme(theme_str)
        except ValueError:
            print(f"패스 생성 경고: 유효하지 않은 테마 '{theme_str}' -> '음식'으로 변환")
            theme = Theme.FOOD
        
        # 데이터 복원
        stores = []
        for store_data in pass_data['stores']:
            # Store 모델에 정의된 필드만 추출
            valid_store_fields = {
                'name', 'category', 'address', 'phone', 'description', 
                'rating', 'price_range', 'opening_hours', 'menu_highlights',
                'location', 'latitude', 'longitude', 'image_url'
            }
            filtered_store_data = {k: v for k, v in store_data.items() if k in valid_store_fields}
            stores.append(Store(**filtered_store_data))
            
        # 혜택 코드 누락 시 부여
        benefits = []
        for benefit_data in pass_data['benefits']:
            # Benefit 모델에 정의된 필드만 추출
            valid_benefit_fields = {
                'store_name', 'benefit_type', 'description', 
                'discount_rate', 'valid_until', 'terms', 'redemption_code'
            }
            filtered_benefit_data = {k: v for k, v in benefit_data.items() if k in valid_benefit_fields}
            
            b = Benefit(**filtered_benefit_data)
            if not getattr(b, 'redemption_code', None):
                source = f"{b.store_name}|{b.benefit_type}|{b.description}"
                b.redemption_code = _stable_redemption_code(source)
            benefits.append(b)
            
        user_prefs = UserPrefs(**pass_data['user_prefs'])

        pass_obj = Pass(
            pass_id=pass_data['pass_id'],
            pass_type=pass_type,
            theme=theme,
            stores=stores,
            benefits=benefits,
            created_at=pass_data['created_at'],
            user_prefs=user_prefs
        )
        
        print(f"[패스 생성] 패스 객체 생성 완료: {pass_obj.pass_id}")
        return pass_obj
        
    except Exception as e:
        print(f"[패스 생성] 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_all_passes() -> List[Dict[str, Any]]:
    """모든 저장된 패스 목록 반환"""
    try:
        passes = []
        pass_ids_seen = set()  # 중복 방지를 위한 집합
        saved_passes_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'saved_passes')
        
        # 프로덕션 환경 감지
        is_production = (
            os.environ.get('GAE_ENV', '').startswith('standard') or 
            os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
            'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
        )
        
        print(f"[패스 조회] 프로덕션 환경: {is_production}")
        print(f"[패스 조회] 저장 디렉토리: {saved_passes_dir}")
        print(f"[패스 조회] 디렉토리 존재: {os.path.exists(saved_passes_dir)}")
        
        # 프로덕션 환경에서는 Datastore에서도 패스를 가져옴 (영구 저장소) - 최우선
        if is_production:
            try:
                try:
                    from src.datastore_service import get_user_passes_from_datastore
                except ImportError:
                    from datastore_service import get_user_passes_from_datastore
                from flask import session
                user_email = session.get('user_email') or 'demo@jemulpogo.com'
                print(f"[패스 조회] Datastore 조회 시작, 사용자: {user_email}")
                datastore_passes = get_user_passes_from_datastore(user_email)
                print(f"[패스 조회] Datastore에서 {len(datastore_passes)}개 패스 발견")
                
                # 🚨 디버깅: Datastore 패스 상세 출력
                if datastore_passes:
                    print(f"[패스 조회] 🔍 Datastore 첫 번째 패스: {datastore_passes[0]}")
                    for i, dp in enumerate(datastore_passes):
                        print(f"[패스 조회] 🔍 Datastore 패스 #{i+1}: ID={dp.get('pass_id')}, source={dp.get('source', 'datastore')}")
                else:
                    print("[패스 조회] ⚠️ Datastore에서 패스를 찾을 수 없음")
                
                # Datastore에서 가져온 패스를 변환하여 추가
                for i, pass_raw in enumerate(datastore_passes):
                    pass_id = pass_raw.get('pass_id')
                    print(f"[패스 조회] 🔧 Datastore 패스 #{i+1} 처리: {pass_id}")
                    
                    # 패스 건너뛰기 조건 확인
                    if not pass_id:
                        print("[패스 조회] ⚠️ 패스 ID가 없음 - 건너뛰기")
                        continue
                    
                    if pass_id in pass_ids_seen:
                        print(f"[패스 조회] ⚠️ 중복 패스 건너뛰기: {pass_id}")
                        continue
                    
                    if pass_id.startswith('test_'):
                        print(f"[패스 조회] ⚠️ 테스트 패스 건너뛰기: {pass_id}")
                        continue
                    
                    # 패스 처리 계속
                    print(f"[패스 조회] ✅ 유효한 패스 처리 시작: {pass_id}")
                    
                    # Datastore 데이터를 표준 형식으로 변환
                    theme_names = {
                        'food': '맛집', 'culture': '문화', 'shopping': '쇼핑',
                        'entertainment': '오락', 'seafood': '해산물', 'cafe': '카페',
                        'traditional': '전통', 'retro': '레트로', 'quiet': '조용함'
                    }
                    
                    pass_type_names = {
                        'light': '라이트', 'premium': '프리미엄', 'citizen': '시민'
                    }
                    
                    theme_name = theme_names.get(pass_raw.get('theme', '').lower(), pass_raw.get('theme', '테마'))
                    pass_type_name = pass_type_names.get(pass_raw.get('pass_type', '').lower(), pass_raw.get('pass_type', '타입'))
                    pass_name = f"{theme_name} {pass_type_name} 패스"
                    
                    print(f"[패스 조회] 🔧 패스 이름 생성: {pass_name}")
                    
                    # 유효기간 계산
                    created_at = pass_raw.get('created_at', datetime.now().isoformat())
                    if isinstance(created_at, str):
                        try:
                            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except ValueError:
                            created_date = datetime.now()
                    else:
                        created_date = created_at if created_at else datetime.now()
                        
                    valid_until = created_date + timedelta(days=30)
                    
                    # 패스 상태 결정
                    now = datetime.now(timezone.utc) if created_date.tzinfo else datetime.now()
                    status = 'expired' if now > valid_until else 'active'
                    
                    # 패스 가격 계산
                    pass_type_prices = {
                        'light': 7900, 'premium': 14900, 'citizen': 6900
                    }
                    total_price = pass_type_prices.get(pass_raw.get('pass_type', '').lower(), 7900)
                    
                    stores = pass_raw.get('stores', [])
                    benefits = pass_raw.get('benefits', [])
                    
                    datastore_pass_entry = {
                        'pass_id': pass_id,
                        'name': pass_name,
                        'pass_type': pass_type_name,
                        'theme': theme_name,
                        'created_at': created_at,
                        'valid_until': valid_until.isoformat(),
                        'status': status,
                        'total_places': len(stores),
                        'visited_places': 0,
                        'total_price': total_price,
                        'store_count': len(stores),
                        'benefits_count': len(benefits),
                        'source': 'datastore'  # 출처 표시
                    }
                    
                    passes.append(datastore_pass_entry)
                    pass_ids_seen.add(pass_id)
                    print(f"[패스 조회] ✅ Datastore 패스 추가됨: {pass_id}")
                        
                    passes.append(datastore_pass_entry)
                    pass_ids_seen.add(pass_id)
                    print(f"[패스 조회] ✅ Datastore 패스 추가됨: {pass_id}")
                        
            except Exception as datastore_error:
                print(f"[패스 조회] Datastore 조회 오류: {datastore_error}")
                import traceback
                print(f"[패스 조회] Datastore 오류 세부사항: {traceback.format_exc()}")
        
        # 세션에서 패스 가져오기 (모든 환경에서 실행)
        try:
            from flask import session
            session_passes = session.get('saved_passes', [])
            print(f"[패스 조회] 세션에서 {len(session_passes)}개 패스 발견")
            
            for pass_data in session_passes:
                try:
                    # 이미 동일한 패스가 있는지 확인 (중복 방지)
                    pass_id = pass_data.get('pass_id')
                    if not pass_id or pass_id in pass_ids_seen:
                        print(f"[패스 조회] 중복 패스 건너뛰기: {pass_id}")
                        continue
                    
                    # 테스트 패스 필터링 (프로덕션에서 자동 생성된 테스트 패스 제외)
                    if pass_id.startswith('test_'):
                        print(f"[패스 조회] 테스트 패스 제외: {pass_id}")
                        continue
                    
                    # 세션에서 가져온 패스 데이터를 처리
                    theme_names = {
                        'food': '맛집', 'culture': '문화', 'shopping': '쇼핑',
                        'entertainment': '오락', 'seafood': '해산물', 'cafe': '카페',
                        'traditional': '전통', 'retro': '레트로', 'quiet': '조용함'
                    }
                    
                    pass_type_names = {
                        'light': '라이트', 'premium': '프리미엄', 'citizen': '시민'
                    }
                    
                    theme_name = theme_names.get(pass_data.get('theme', '').lower(), pass_data.get('theme', '테마'))
                    pass_type_name = pass_type_names.get(pass_data.get('pass_type', '').lower(), pass_data.get('pass_type', '타입'))
                    pass_name = f"{theme_name} {pass_type_name} 패스"
                    
                    # 유효기간 계산
                    created_at = pass_data.get('created_at', datetime.now().isoformat())
                    if isinstance(created_at, str):
                        try:
                            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except ValueError:
                            # ISO 형식이 아닌 경우 현재 시간 사용
                            created_date = datetime.now()
                    else:
                        created_date = created_at if created_at else datetime.now()
                        
                    valid_until = created_date + timedelta(days=30)
                    
                    # 패스 상태 결정
                    now = datetime.now(timezone.utc) if created_date.tzinfo else datetime.now()
                    status = 'expired' if now > valid_until else 'active'
                    
                    # 패스 가격 계산
                    pass_type_prices = {
                        'light': 7900, 'premium': 14900, 'citizen': 6900
                    }
                    total_price = pass_type_prices.get(pass_data.get('pass_type', '').lower(), 7900)
                    
                    stores = pass_data.get('stores', [])
                    benefits = pass_data.get('benefits', [])
                    
                    pass_entry = {
                        'pass_id': pass_id,
                        'name': pass_name,
                        'pass_type': pass_type_name,
                        'theme': theme_name,
                        'created_at': created_at,
                        'valid_until': valid_until.isoformat(),
                        'status': status,
                        'total_places': len(stores),
                        'visited_places': 0,
                        'total_price': total_price,
                        'store_count': len(stores),
                        'benefits_count': len(benefits),
                        'source': 'session'  # 출처 표시
                    }
                    
                    passes.append(pass_entry)
                    pass_ids_seen.add(pass_id)
                    print(f"[패스 조회] 세션에서 패스 추가: {pass_id} - {pass_name}")
                    print(f"[패스 조회] 패스 상세: 장소={len(stores)}, 혜택={len(benefits)}, 상태={status}")
                    
                except Exception as pass_error:
                    print(f"[패스 조회] 세션 패스 처리 오류: {pass_error}")
                    import traceback
                    print(f"[패스 조회] 세부 오류: {traceback.format_exc()}")
                    continue
                    
        except Exception as session_error:
            print(f"[패스 조회] 세션 접근 오류: {session_error}")
            import traceback
            print(f"[패스 조회] 세션 접근 세부 오류: {traceback.format_exc()}")
        
        # 쿠키에서도 패스를 가져옴 (로그아웃 후에도 유지되는 백업)
        try:
            from flask import request
            cookie_passes = request.cookies.get('user_passes')
            if cookie_passes:
                import json
                cookie_pass_ids = json.loads(cookie_passes)
                print(f"[패스 조회] 쿠키에서 {len(cookie_pass_ids)}개 패스 ID 발견")
                
                for pass_id in cookie_pass_ids:
                    try:
                        # 중복 확인
                        if pass_id in pass_ids_seen:
                            continue
                        
                        # 테스트 패스 필터링
                        if pass_id.startswith('test_'):
                            print(f"[패스 조회] 쿠키 테스트 패스 제외: {pass_id}")
                            continue
                            
                        # 파일에서 패스 로드 시도
                        pass_obj = load_pass_from_file(pass_id)
                        if pass_obj:
                            # 패스 이름 생성 (테마와 타입 기반)
                            theme_names = {
                                'food': '맛집', 'culture': '문화', 'shopping': '쇼핑',
                                'entertainment': '오락', 'seafood': '해산물', 'cafe': '카페',
                                'traditional': '전통', 'retro': '레트로', 'quiet': '조용함'
                            }
                            
                            pass_type_names = {
                                'light': '라이트', 'premium': '프리미엄', 'citizen': '시민'
                            }
                            
                            theme_name = theme_names.get(pass_obj.theme.value, pass_obj.theme.value)
                            pass_type_name = pass_type_names.get(pass_obj.pass_type.value, pass_obj.pass_type.value)
                            pass_name = f"{theme_name} {pass_type_name} 패스"
                            
                            # 유효기간 계산
                            try:
                                if isinstance(pass_obj.created_at, str):
                                    created_date = datetime.fromisoformat(pass_obj.created_at.replace('Z', '+00:00'))
                                else:
                                    created_date = pass_obj.created_at
                                    
                                valid_until = created_date + timedelta(days=30)
                                
                                # 패스 상태 결정
                                now = datetime.now(timezone.utc) if created_date.tzinfo else datetime.now()
                                status = 'expired' if now > valid_until else 'active'
                                
                                # 패스 가격 계산
                                pass_type_prices = {
                                    'light': 7900, 'premium': 14900, 'citizen': 6900
                                }
                                total_price = pass_type_prices.get(pass_obj.pass_type.value, 7900)
                                
                                passes.append({
                                    'pass_id': pass_obj.pass_id,
                                    'name': pass_name,
                                    'pass_type': pass_type_name,
                                    'theme': theme_name,
                                    'created_at': pass_obj.created_at,
                                    'valid_until': valid_until.isoformat(),
                                    'status': status,
                                    'total_places': len(pass_obj.stores),
                                    'visited_places': 0,
                                    'total_price': total_price,
                                    'store_count': len(pass_obj.stores),
                                    'benefits_count': len(pass_obj.benefits),
                                    'source': 'cookie_file'  # 출처 표시
                                })
                                
                                pass_ids_seen.add(pass_id)
                                print(f"[패스 조회] 쿠키에서 패스 추가: {pass_id} - {pass_name}")
                                
                            except Exception as date_error:
                                print(f"[패스 조회] 날짜 처리 오류 (패스 {pass_id}): {date_error}")
                                continue
                                
                    except Exception as cookie_pass_error:
                        print(f"[패스 조회] 쿠키 패스 로드 실패 ({pass_id}): {cookie_pass_error}")
                        continue
                        
        except Exception as cookie_error:
            print(f"[패스 조회] 쿠키 접근 오류: {cookie_error}")
        
        # 최종 중복 제거 및 정렬 (생성 시간 역순)
        unique_passes = []
        final_pass_ids = set()
        
        for pass_data in passes:
            pass_id = pass_data.get('pass_id')
            if pass_id and pass_id not in final_pass_ids:
                unique_passes.append(pass_data)
                final_pass_ids.add(pass_id)
        
        # 생성 시간으로 정렬 (최신 순)
        try:
            unique_passes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as sort_error:
            print(f"[패스 조회] 정렬 오류: {sort_error}")
        
        print(f"[패스 조회] 최종 결과: {len(unique_passes)}개 패스 반환")
        print(f"[패스 조회] 패스 출처별 분포: {[p.get('source', 'unknown') for p in unique_passes]}")
        
        return unique_passes
        
    except Exception as e:
        print(f"[패스 조회] 전체 함수 오류: {e}")
        import traceback
        print(f"[패스 조회] 전체 함수 오류 세부사항: {traceback.format_exc()}")
        return []
        
        # 프로덕션 환경에서는 세션에서도 패스를 가져옴 (백업)
        if is_production:
            try:
                from flask import session
                session_passes = session.get('saved_passes', [])
                print(f"[패스 조회] 세션에서 {len(session_passes)}개 패스 발견")
                
                for pass_data in session_passes:
                    try:
                        # 세션에서 가져온 패스 데이터를 처리
                        theme_names = {
                            'food': '맛집', 'culture': '문화', 'shopping': '쇼핑',
                            'entertainment': '오락', 'seafood': '해산물', 'cafe': '카페',
                            'traditional': '전통', 'retro': '레트로', 'quiet': '조용함'
                        }
                        
                        pass_type_names = {
                            'light': '라이트', 'premium': '프리미엄', 'citizen': '시민'
                        }
                        
                        theme_name = theme_names.get(pass_data.get('theme', '').lower(), pass_data.get('theme', '테마'))
                        pass_type_name = pass_type_names.get(pass_data.get('pass_type', '').lower(), pass_data.get('pass_type', '타입'))
                        pass_name = f"{theme_name} {pass_type_name} 패스"
                        
                        # 유효기간 계산
                        created_at = pass_data.get('created_at', datetime.now().isoformat())
                        if isinstance(created_at, str):
                            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            created_date = created_at
                            
                        valid_until = created_date + timedelta(days=30)
                        
                        # 패스 가격 계산
                        pass_type_prices = {
                            'light': 7900, 'premium': 14900, 'citizen': 6900
                        }
                        total_price = pass_type_prices.get(pass_data.get('pass_type', '').lower(), 7900)
                        
                        stores = pass_data.get('stores', [])
                        benefits = pass_data.get('benefits', [])
                        
                        passes.append({
                            'pass_id': pass_data.get('pass_id'),
                            'name': pass_name,
                            'pass_type': pass_type_name,
                            'theme': theme_name,
                            'created_at': created_at,
                            'valid_until': valid_until.isoformat(),
                            'status': status,
                            'total_places': len(stores),
                            'visited_places': 0,
                            'total_price': total_price,
                            'store_count': len(stores),
                            'benefits_count': len(benefits),
                            'source': 'session_backup'  # 출처 표시
                        })
                        
                        print(f"[패스 조회] 프로덕션 세션에서 패스 추가: {pass_data.get('pass_id')}")
                        
                    except Exception as pass_error:
                        print(f"[패스 조회] 프로덕션 세션 패스 처리 오류: {pass_error}")
                        continue
                        
            except Exception as session_error:
                print(f"[패스 조회] 프로덕션 세션 접근 오류: {session_error}")
        
        # 쿠키에서도 패스를 가져옴 (로그아웃 후에도 유지되는 백업)
        try:
            from flask import request
            cookie_passes = request.cookies.get('user_passes')
            if cookie_passes:
                import json
                cookie_pass_ids = json.loads(cookie_passes)
                print(f"[패스 조회] 쿠키에서 {len(cookie_pass_ids)}개 패스 ID 발견")
                
                for pass_id in cookie_pass_ids:
                    try:
                        # 파일에서 패스 로드 시도
                        pass_obj = load_pass_from_file(pass_id)
                        if pass_obj:
                            # 패스 이름 생성 (테마와 타입 기반)
                            theme_names = {
                                'food': '맛집', 'culture': '문화', 'shopping': '쇼핑',
                                'entertainment': '오락', 'seafood': '해산물', 'cafe': '카페',
                                'traditional': '전통', 'retro': '레트로', 'quiet': '조용함'
                            }
                            
                            pass_type_names = {
                                'light': '라이트', 'premium': '프리미엄', 'citizen': '시민'
                            }
                            
                            theme_name = theme_names.get(pass_obj.theme.value, pass_obj.theme.value)
                            pass_type_name = pass_type_names.get(pass_obj.pass_type.value, pass_obj.pass_type.value)
                            pass_name = f"{theme_name} {pass_type_name} 패스"
                            
                            # 유효기간 계산
                            try:
                                if isinstance(pass_obj.created_at, str):
                                    created_date = datetime.fromisoformat(pass_obj.created_at.replace('Z', '+00:00'))
                                else:
                                    created_date = pass_obj.created_at
                                
                                valid_until = created_date + timedelta(days=30)
                                valid_until_str = valid_until.isoformat()
                                
                                # 패스 상태 결정
                                now = datetime.now(timezone.utc) if created_date.tzinfo else datetime.now()
                                status = 'expired' if now > valid_until else 'active'
                            except Exception as date_error:
                                print(f"쿠키 패스 날짜 처리 오류: {date_error}")
                                valid_until_str = pass_obj.created_at
                                status = 'active'
                            
                            # 패스 가격 계산
                            pass_type_prices = {
                                'light': 7900, 'premium': 14900, 'citizen': 6900
                            }
                            total_price = pass_type_prices.get(pass_obj.pass_type.value, 7900)
                            
                            passes.append({
                                'pass_id': pass_obj.pass_id,
                                'name': pass_name,
                                'pass_type': pass_type_name,
                                'theme': theme_name,
                                'created_at': pass_obj.created_at,
                                'valid_until': valid_until_str,
                                'status': status,
                                'total_places': len(pass_obj.stores),
                                'visited_places': 0,
                                'total_price': total_price,
                                'store_count': len(pass_obj.stores),
                                'benefits_count': len(pass_obj.benefits),
                                'source': 'cookie'  # 출처 표시
                            })
                            
                            print(f"[패스 조회] 쿠키에서 패스 추가: {pass_obj.pass_id}")
                        else:
                            print(f"[패스 조회] 쿠키 패스 로드 실패: {pass_id}")
                            
                    except Exception as pass_error:
                        print(f"[패스 조회] 쿠키 패스 처리 오류: {pass_error}")
                        continue
        except Exception as cookie_error:
            print(f"[패스 조회] 쿠키 접근 오류: {cookie_error}")
        
        # 파일 시스템에서도 패스를 가져옴 (로컬 또는 배포 시 포함된 파일들)
        if os.path.exists(saved_passes_dir):
            try:
                files = os.listdir(saved_passes_dir)
                print(f"[패스 조회] 디렉토리 내 파일 수: {len(files)}")
                print(f"[패스 조회] 파일 목록: {files}")
            except Exception as list_error:
                print(f"[패스 조회] 파일 목록 조회 실패: {list_error}")
                files = []
        else:
            files = []
        
        for filename in files:
            if filename.endswith('.json') and filename.startswith('pass_'):
                pass_id = filename[5:-5]  # 'pass_'와 '.json' 제거
                pass_obj = load_pass_from_file(pass_id)
                if pass_obj:
                    # 패스 이름 생성 (테마와 타입 기반)
                    theme_names = {
                        'food': '맛집',
                        'culture': '문화',
                        'shopping': '쇼핑',
                        'entertainment': '오락',
                        'seafood': '해산물',
                        'cafe': '카페',
                        'traditional': '전통',
                        'retro': '레트로',
                        'quiet': '조용함'
                    }
                    
                    pass_type_names = {
                        'light': '라이트',
                        'premium': '프리미엄',
                        'citizen': '시민'
                    }
                    
                    theme_name = theme_names.get(pass_obj.theme.value, pass_obj.theme.value)
                    pass_type_name = pass_type_names.get(pass_obj.pass_type.value, pass_obj.pass_type.value)
                    pass_name = f"{theme_name} {pass_type_name} 패스"
                    
                    # 유효기간 계산 (생성일로부터 30일)
                    try:
                        if isinstance(pass_obj.created_at, str):
                            created_date = datetime.fromisoformat(pass_obj.created_at.replace('Z', '+00:00'))
                        else:
                            created_date = pass_obj.created_at
                        
                        valid_until = created_date + timedelta(days=30)
                        valid_until_str = valid_until.isoformat()
                        
                        # 패스 상태 결정
                        now = datetime.now(timezone.utc) if created_date.tzinfo else datetime.now()
                        if now > valid_until:
                            status = 'expired'
                        else:
                            status = 'active'
                    except Exception as date_error:
                        print(f"날짜 처리 오류: {date_error}")
                        valid_until_str = pass_obj.created_at
                        status = 'active'
                    
                    # 패스 가격 계산
                    pass_type_prices = {
                        'light': 7900,
                        'premium': 14900,
                        'citizen': 6900
                    }
                    total_price = pass_type_prices.get(pass_obj.pass_type.value, 7900)
                    
                    passes.append({
                        'pass_id': pass_obj.pass_id,
                        'name': pass_name,
                        'pass_type': pass_type_name,
                        'theme': theme_name,
                        'created_at': pass_obj.created_at,
                        'valid_until': valid_until_str,
                        'status': status,
                        'total_places': len(pass_obj.stores),
                        'visited_places': 0,  # TODO: 실제 방문 기록 추적 시 업데이트
                        'total_price': total_price,
                        'store_count': len(pass_obj.stores),
                        'benefits_count': len(pass_obj.benefits)
                    })
        
        # 패스 ID 기준으로 중복 제거 (세션에서 가져온 패스가 우선)
        unique_passes = {}
        for pass_info in passes:
            pass_id = pass_info.get('pass_id')
            if pass_id and pass_id not in unique_passes:
                unique_passes[pass_id] = pass_info
        
        passes = list(unique_passes.values())
        print(f"[패스 조회] 중복 제거 후 총 {len(passes)}개 패스")
        
        # 생성일자순 정렬 (최신순)
        passes.sort(key=lambda x: x['created_at'], reverse=True)
        return passes
        
    except Exception as e:
        print(f"패스 목록 조회 중 오류: {e}")
        return []

def load_benefits_raw() -> List[Dict]:
    """혜택 원본 데이터 로드 (모든 필드 포함)"""
    try:
        benefits_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'benefits.json')
        with open(benefits_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'benefits' in data:
                return data['benefits']
            else:
                return data
    except FileNotFoundError:
        print("benefits.json 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"혜택 데이터 로드 중 오류: {e}")
        return []

def get_synergy_score(store_data: Dict) -> int:
    """상점의 상생 점수 계산 (0-100점)"""
    base_score = 50
    
    # 프랜차이즈 여부 (-30점)
    if store_data.get('is_franchise', False):
        base_score -= 30
    
    # 리뷰 수 (적을수록 가점)
    reviews = store_data.get('reviews', 0)
    if reviews < 50:
        base_score += 30
    elif reviews < 100:
        base_score += 20
    elif reviews < 200:
        base_score += 10
    
    # 지역 특성 (골목상권, 제물포시장 가점)
    area = store_data.get('area', '')
    if area in ["골목상권", "제물포시장"]:
        base_score += 25
    
    # 0-100 범위로 제한
    return max(0, min(100, base_score))

def calculate_total_eco_value(benefits: List[Benefit]) -> int:
    """혜택들의 총 경제적 가치 계산"""
    total_value = 0
    benefits_raw = load_benefits_raw()
    
    # store_id별 혜택 데이터 맵핑
    benefit_value_map = {}
    for benefit_data in benefits_raw:
        store_id = benefit_data.get('store_id', '')
        desc = benefit_data.get('desc', '')
        eco_value = benefit_data.get('eco_value', 0)
        benefit_value_map[f"{store_id}_{desc}"] = eco_value
    
    for benefit in benefits:
        key = f"{benefit.store_name}_{benefit.description}"
        eco_value = benefit_value_map.get(key, 3000)  # 기본값 3000원
        total_value += eco_value
        print(f"[가치 계산] {benefit.store_name} - {benefit.description}: {eco_value}원")
    
    print(f"[가치 계산] 총 혜택 가치: {total_value}원")
    return total_value

def calculate_average_synergy_score(stores: List[Store]) -> float:
    """상점들의 평균 상생 점수 계산"""
    if not stores:
        return 0.0
    
    stores_raw = load_stores_raw()
    store_data_map = {store['name']: store for store in stores_raw}
    
    total_score = 0
    valid_stores = 0
    
    for store in stores:
        store_data = store_data_map.get(store.name)
        if store_data:
            synergy_score = get_synergy_score(store_data)
            total_score += synergy_score
            valid_stores += 1
            print(f"[상생점수] {store.name}: {synergy_score}점")
    
    if valid_stores == 0:
        return 0.0
    
    avg_score = total_score / valid_stores
    print(f"[상생점수] 평균 상생점수: {avg_score:.1f}점")
    return avg_score

def validate_pass_quality(pass_obj: Pass, pass_price: int) -> Dict[str, Any]:
    """패스 품질 검증 (가치 대비 효과 150% 이상, 상생점수 70점 이상)"""
    total_value = calculate_total_eco_value(pass_obj.benefits)
    avg_synergy = calculate_average_synergy_score(pass_obj.stores)
    value_ratio = (total_value / pass_price) * 100 if pass_price > 0 else 0
    
    is_valid = value_ratio >= 150 and avg_synergy >= 70
    
    result = {
        'is_valid': is_valid,
        'total_value': total_value,
        'value_ratio': value_ratio,
        'avg_synergy': avg_synergy,
        'pass_price': pass_price,
        'requirements': {
            'min_value_ratio': 150,
            'min_synergy_score': 70
        }
    }
    
    print(f"[품질 검증] 가치 대비 효과: {value_ratio:.1f}% (최소 150%)")
    print(f"[품질 검증] 평균 상생점수: {avg_synergy:.1f}점 (최소 70점)")
    print(f"[품질 검증] 품질 기준 충족: {'✅' if is_valid else '❌'}")
    
    return result
