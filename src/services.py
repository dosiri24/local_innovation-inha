"""
비즈니스 로직 및 서비스 (패스 생성 제외)
패스 생성 기능은 pass_generator.py 모듈로 분리되었습니다.
"""
import json
import os
from datetime import datetime
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

def load_pass_from_file(pass_id: str) -> Optional[Pass]:
    """파일에서 패스 로드"""
    try:
        filename = f"pass_{pass_id}.json"
        saved_passes_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'saved_passes')
        filepath = os.path.join(saved_passes_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            pass_data = json.load(f)
        
        # 호환성을 위한 데이터 구조 확인
        if 'stores' not in pass_data:
            # 이전 형식의 파일은 스킵
            print(f"패스 로드 중 오류: 이전 형식의 패스 파일 스킵 - {pass_id}")
            return None
            
        if 'benefits' not in pass_data:
            print(f"패스 로드 중 오류: benefits 필드 없음 - {pass_id}")
            return None
        
        # PassType 호환성 확인
        pass_type_str = pass_data.get('pass_type', 'light')
        try:
            pass_type = PassType(pass_type_str)
        except ValueError:
            # 유효하지 않은 PassType은 light로 변환
            print(f"패스 로드 중 경고: 유효하지 않은 패스 타입 '{pass_type_str}' -> 'light'로 변환")
            pass_type = PassType.LIGHT
        
        # Theme 호환성 확인  
        theme_str = pass_data.get('theme', '음식')
        try:
            theme = Theme(theme_str)
        except ValueError:
            print(f"패스 로드 중 경고: 유효하지 않은 테마 '{theme_str}' -> '음식'으로 변환")
            theme = Theme.FOOD
        
        # 데이터 복원
        stores = [Store(**store_data) for store_data in pass_data['stores']]
        # 혜택 코드 누락 시 부여
        benefits = []
        for benefit_data in pass_data['benefits']:
            b = Benefit(**benefit_data)
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
        
        return pass_obj
        
    except Exception as e:
        print(f"패스 로드 중 오류: {e}")
        return None

def get_all_passes() -> List[Dict[str, Any]]:
    """모든 저장된 패스 목록 반환"""
    try:
        passes = []
        saved_passes_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'saved_passes')
        
        if not os.path.exists(saved_passes_dir):
            return passes
        
        for filename in os.listdir(saved_passes_dir):
            if filename.endswith('.json') and filename.startswith('pass_'):
                pass_id = filename[5:-5]  # 'pass_'와 '.json' 제거
                pass_obj = load_pass_from_file(pass_id)
                if pass_obj:
                    passes.append({
                        'pass_id': pass_obj.pass_id,
                        'pass_type': pass_obj.pass_type.value,
                        'theme': pass_obj.theme.value,
                        'created_at': pass_obj.created_at,
                        'store_count': len(pass_obj.stores)
                    })
        
        # 생성일자순 정렬 (최신순)
        passes.sort(key=lambda x: x['created_at'], reverse=True)
        return passes
        
    except Exception as e:
        print(f"패스 목록 조회 중 오류: {e}")
        return []
