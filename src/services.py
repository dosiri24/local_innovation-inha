"""
비즈니스 로직 및 서비스
"""
import json
import os
import qrcode
from datetime import datetime
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from dotenv import load_dotenv
from models import Store, Benefit, UserPrefs, Pass, PassType, Theme

# 환경 변수 로드
load_dotenv()

# Google Gemini API 설정
API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
print(f"[AI 설정] API 키 존재: {bool(API_KEY)}")
if API_KEY:
    genai.configure(api_key=API_KEY)  # type: ignore
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    model = genai.GenerativeModel(model_name)  # type: ignore
    print(f"[AI 설정] Google Gemini 모델 '{model_name}' 초기화 완료")
else:
    model = None
    print("[AI 설정] ❌ GEMINI_API_KEY가 설정되지 않았습니다!")
    print("[AI 설정] ❌ AI 기능을 사용하려면 .env 파일에 GEMINI_API_KEY를 설정해주세요")
    print("[AI 설정] ❌ 패스 생성 시 오류가 발생합니다")

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

def generate_pass(user_prefs: UserPrefs, pass_type: PassType, theme: Theme) -> Optional[Pass]:
    """AI 기반 패스 생성"""
    try:
        all_stores = load_stores()
        all_benefits = load_benefits()
        
        if not all_stores:
            print("상점 데이터가 없습니다.")
            return None
            
        # 테마에 따른 상점 필터링
        theme_categories = {
            Theme.FOOD: ["한식", "중식", "일식", "양식", "디저트", "카페"],
            Theme.CULTURE: ["관광지", "박물관", "갤러리", "문화시설"],
            Theme.SHOPPING: ["쇼핑몰", "마트", "의류", "잡화"],
            Theme.ENTERTAINMENT: ["엔터테인먼트", "레저", "스포츠", "게임"]
        }
        
        relevant_categories = theme_categories.get(theme, [])
        filtered_stores = [store for store in all_stores 
                         if any(cat in store.category for cat in relevant_categories)]
        
        if not filtered_stores:
            filtered_stores = all_stores  # 필터링된 결과가 없으면 전체 사용
        
        # AI 프롬프트 생성
        prompt = f"""
        사용자 선호도:
        - 예산: {user_prefs.budget}
        - 관심사: {', '.join(user_prefs.interests)}
        - 식이 제한: {', '.join(user_prefs.dietary_restrictions) if user_prefs.dietary_restrictions else '없음'}
        - 그룹 크기: {user_prefs.group_size}명
        - 지속 시간: {user_prefs.duration}
        - 교통수단: {user_prefs.transportation}
        
        패스 타입: {pass_type.value}
        테마: {theme.value}
        
        다음 상점들 중에서 사용자 선호도에 맞는 3-5개의 상점을 추천해주세요:
        {json.dumps([{'name': store.name, 'category': store.category, 'description': store.description, 'rating': store.rating, 'price_range': store.price_range} for store in filtered_stores], ensure_ascii=False, indent=2)}
        
        응답은 반드시 다음 JSON 형식으로만 제공해주세요:
        {{
            "recommended_stores": ["상점명1", "상점명2", "상점명3"],
            "reason": "추천 이유"
        }}
        """
        
        # AI API가 필수 - API 키가 없으면 에러
        if not model:
            raise ValueError("AI API 키가 설정되지 않았습니다. GEMINI_API_KEY를 설정해주세요.")
        
        print("[AI 추천] Gemini AI로 추천 생성 중...")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"[AI 추천] AI 응답 받음: {response_text[:100]}...")
        
        # JSON 파싱
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        ai_response = json.loads(response_text)
        recommended_store_names = ai_response.get('recommended_stores', [])
        
        if not recommended_store_names:
            raise ValueError("AI가 추천한 상점이 없습니다.")
            
        print(f"[AI 추천] 추천된 상점들: {recommended_store_names}")
        
        # 추천된 상점들 찾기
        recommended_stores = [store for store in all_stores 
                            if store.name in recommended_store_names]
        
        if not recommended_stores:
            raise ValueError(f"추천된 상점들을 찾을 수 없습니다: {recommended_store_names}")
        
        # 추천된 상점들의 ID 목록 생성
        recommended_store_ids = []
        stores_raw = load_stores_raw()
        for store in recommended_stores:
            # stores.json에서 store ID 찾기 (store_data에서 'id' 필드 확인)
            for store_data in stores_raw:
                if store_data.get('name') == store.name:
                    recommended_store_ids.append(store_data.get('id'))
                    print(f"[혜택 매칭] {store.name} -> {store_data.get('id')}")
                    break
        
        print(f"[혜택 매칭] 추천된 상점 ID들: {recommended_store_ids}")
        
        # 해당 상점들의 혜택 찾기 (store_id로 매칭)
        store_benefits = [benefit for benefit in all_benefits 
                         if benefit.store_name in recommended_store_ids]
        
        print(f"[혜택 매칭] 찾은 혜택 수: {len(store_benefits)}")
        for benefit in store_benefits:
            print(f"[혜택 매칭] {benefit.store_name} - {benefit.description}")
        
        # 패스 ID 생성
        pass_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(user_prefs)) % 10000:04d}"
        
        # 패스 생성
        pass_obj = Pass(
            pass_id=pass_id,
            pass_type=pass_type,
            theme=theme,
            stores=recommended_stores,
            benefits=store_benefits,
            created_at=datetime.now().isoformat(),
            user_prefs=user_prefs
        )
        
        # QR 코드 생성
        qr_code_path = generate_qr_code(pass_id)
        if qr_code_path:
            pass_obj.qr_code_path = qr_code_path
        
        # 패스 저장
        save_pass_to_file(pass_obj)
        
        return pass_obj
        
    except Exception as e:
        print(f"패스 생성 중 오류 발생: {e}")
        return None

def generate_qr_code(pass_id: str) -> Optional[str]:
    """QR 코드 생성"""
    try:
        qr_codes_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'qr_codes')
        os.makedirs(qr_codes_dir, exist_ok=True)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # type: ignore
            box_size=10,
            border=4,
        )
        qr.add_data(f"PASS:{pass_id}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_filename = f"pass_{pass_id}.png"
        qr_path = os.path.join(qr_codes_dir, qr_filename)
        img.save(qr_path)  # type: ignore
        
        return qr_path
        
    except Exception as e:
        print(f"QR 코드 생성 중 오류: {e}")
        return None

def save_pass_to_file(pass_obj: Pass) -> bool:
    """패스를 파일로 저장"""
    try:
        saved_passes_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'saved_passes')
        os.makedirs(saved_passes_dir, exist_ok=True)
        
        pass_data = {
            'pass_id': pass_obj.pass_id,
            'pass_type': pass_obj.pass_type.value,
            'theme': pass_obj.theme.value,
            'stores': [store.__dict__ for store in pass_obj.stores],
            'benefits': [benefit.__dict__ for benefit in pass_obj.benefits],
            'created_at': pass_obj.created_at,
            'user_prefs': pass_obj.user_prefs.__dict__,
            'qr_code_path': pass_obj.qr_code_path
        }
        
        filename = f"pass_{pass_obj.pass_id}.json"
        filepath = os.path.join(saved_passes_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(pass_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"패스 저장 중 오류: {e}")
        return False

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
        benefits = [Benefit(**benefit_data) for benefit_data in pass_data['benefits']]
        user_prefs = UserPrefs(**pass_data['user_prefs'])
        
        pass_obj = Pass(
            pass_id=pass_data['pass_id'],
            pass_type=pass_type,
            theme=theme,
            stores=stores,
            benefits=benefits,
            created_at=pass_data['created_at'],
            user_prefs=user_prefs,
            qr_code_path=pass_data.get('qr_code_path')
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
