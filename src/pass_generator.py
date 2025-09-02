"""
패스 생성 전용 모듈
AI 기반 맞춤형 패스 생성 로직을 담당합니다.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from dotenv import load_dotenv
from models import Store, Benefit, UserPrefs, Pass, PassType, Theme
import hashlib

# 환경 변수 로드
load_dotenv()

class PassGenerator:
    """패스 생성을 담당하는 클래스"""
    
    def __init__(self):
        """PassGenerator 초기화"""
        self.model = self._initialize_ai_model()
        self.stores_cache = None
        self.benefits_cache = None
        self.stores_raw_cache = None
        
    def _initialize_ai_model(self):
        """Google Gemini AI 모델 초기화"""
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        print(f"[패스 생성기] AI API 키 존재: {bool(api_key)}")
        
        if api_key and genai is not None:
            try:
                genai.configure(api_key=api_key)  # type: ignore
                model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
                model = genai.GenerativeModel(model_name)  # type: ignore
                print(f"[패스 생성기] Google Gemini 모델 '{model_name}' 초기화 완료")
                return model
            except Exception as e:
                print(f"[패스 생성기] AI 모델 초기화 실패: {e}")
                return None
        else:
            if genai is None:
                print("[패스 생성기] ❌ google-generativeai 패키지가 설치되지 않았습니다!")
            else:
                print("[패스 생성기] ❌ GEMINI_API_KEY가 설정되지 않았습니다!")
            print("[패스 생성기] ❌ AI 기능을 사용하려면 .env 파일에 GEMINI_API_KEY를 설정해주세요")
            return None
    
    def load_stores(self) -> List[Store]:
        """상점 데이터 로드 (캐싱 적용)"""
        if self.stores_cache is not None:
            return self.stores_cache
            
        try:
            stores_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stores.json')
            with open(stores_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stores_data = data.get('stores', data)
                
                stores = []
                for store_data in stores_data:
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
                
                self.stores_cache = stores
                return stores
                
        except FileNotFoundError:
            print("[패스 생성기] stores.json 파일을 찾을 수 없습니다.")
            return []
        except Exception as e:
            print(f"[패스 생성기] 상점 데이터 로드 중 오류: {e}")
            return []

    def load_stores_raw(self) -> List[Dict]:
        """상점 원본 데이터 로드 (ID 포함, 캐싱 적용)"""
        if self.stores_raw_cache is not None:
            return self.stores_raw_cache
            
        try:
            stores_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stores.json')
            with open(stores_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stores_data = data.get('stores', data)
                self.stores_raw_cache = stores_data
                return stores_data
                
        except FileNotFoundError:
            print("[패스 생성기] stores.json 파일을 찾을 수 없습니다.")
            return []
        except Exception as e:
            print(f"[패스 생성기] 상점 데이터 로드 중 오류: {e}")
            return []

    def load_benefits(self) -> List[Benefit]:
        """혜택 데이터 로드 (캐싱 적용)"""
        if self.benefits_cache is not None:
            return self.benefits_cache
            
        try:
            benefits_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'benefits.json')
            with open(benefits_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                benefits_data = data.get('benefits', data)
                
                benefits = []
                for benefit_data in benefits_data:
                    benefit = Benefit(
                        store_name=benefit_data.get('store_id', ''),
                        benefit_type=benefit_data.get('type', 'discount'),
                        description=benefit_data.get('desc', benefit_data.get('description', ''))
                    )
                    benefits.append(benefit)
                
                self.benefits_cache = benefits
                return benefits
                
        except FileNotFoundError:
            print("[패스 생성기] benefits.json 파일을 찾을 수 없습니다.")
            return []
        except Exception as e:
            print(f"[패스 생성기] 혜택 데이터 로드 중 오류: {e}")
            return []

    def filter_stores_by_theme(self, stores: List[Store], theme: Theme) -> List[Store]:
        """테마에 따른 상점 필터링"""
        theme_categories = {
            Theme.FOOD: ["한식", "중식", "일식", "양식", "디저트", "카페", "음식점"],
            Theme.CULTURE: ["관광지", "박물관", "갤러리", "문화시설"],
            Theme.SHOPPING: ["쇼핑몰", "마트", "의류", "잡화"],
            Theme.ENTERTAINMENT: ["엔터테인먼트", "레저", "스포츠", "게임"]
        }
        
        relevant_categories = theme_categories.get(theme, [])
        filtered_stores = [store for store in stores 
                         if any(cat in store.category for cat in relevant_categories)]
        
        # 필터링된 결과가 없으면 전체 사용
        if not filtered_stores:
            print(f"[패스 생성기] 테마 '{theme.value}' 필터링 결과 없음, 전체 상점 사용")
            return stores
            
        print(f"[패스 생성기] 테마 '{theme.value}' 필터링: {len(filtered_stores)}개 상점")
        return filtered_stores

    def generate_ai_prompt(self, user_prefs: UserPrefs, pass_type: PassType, 
                          theme: Theme, filtered_stores: List[Store]) -> str:
        """AI 추천을 위한 프롬프트 생성"""
        store_info = []
        for store in filtered_stores:
            store_info.append({
                'name': store.name,
                'category': store.category,
                'description': store.description,
                'rating': store.rating,
                'price_range': store.price_range
            })
        
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
        {json.dumps(store_info, ensure_ascii=False, indent=2)}
        
        응답은 반드시 다음 JSON 형식으로만 제공해주세요:
        {{
            "recommended_stores": ["상점명1", "상점명2", "상점명3"],
            "reason": "추천 이유"
        }}
        """
        return prompt

    def get_ai_recommendations(self, prompt: str) -> List[str]:
        """AI로부터 상점 추천받기"""
        if not self.model:
            raise ValueError("AI API 키가 설정되지 않았습니다. GEMINI_API_KEY를 설정해주세요.")
        
        print("[패스 생성기] Gemini AI로 추천 생성 중...")
        response = self.model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"[패스 생성기] AI 응답 받음: {response_text[:100]}...")
        
        # JSON 파싱
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        try:
            ai_response = json.loads(response_text)
            recommended_store_names = ai_response.get('recommended_stores', [])
            
            if not recommended_store_names:
                raise ValueError("AI가 추천한 상점이 없습니다.")
                
            print(f"[패스 생성기] 추천된 상점들: {recommended_store_names}")
            return recommended_store_names
            
        except json.JSONDecodeError as e:
            print(f"[패스 생성기] AI 응답 JSON 파싱 실패: {e}")
            print(f"[패스 생성기] 원본 응답: {response_text}")
            raise ValueError(f"AI 응답을 해석할 수 없습니다: {e}")

    def match_stores_and_benefits(self, recommended_store_names: List[str], 
                                 all_stores: List[Store], all_benefits: List[Benefit]) -> tuple:
        """추천된 상점명으로 Store 객체와 혜택들을 매칭"""
        # 추천된 상점들 찾기
        recommended_stores = [store for store in all_stores 
                            if store.name in recommended_store_names]
        
        if not recommended_stores:
            raise ValueError(f"추천된 상점들을 찾을 수 없습니다: {recommended_store_names}")
        
        # 추천된 상점들의 ID 목록 생성
        recommended_store_ids = []
        stores_raw = self.load_stores_raw()
        
        for store in recommended_stores:
            for store_data in stores_raw:
                if store_data.get('name') == store.name:
                    store_id = store_data.get('id')
                    recommended_store_ids.append(store_id)
                    print(f"[패스 생성기] 혜택 매칭: {store.name} -> {store_id}")
                    break
        
        print(f"[패스 생성기] 추천된 상점 ID들: {recommended_store_ids}")
        
        # 해당 상점들의 혜택 찾기
        store_benefits = [benefit for benefit in all_benefits 
                         if benefit.store_name in recommended_store_ids]
        
        print(f"[패스 생성기] 찾은 혜택 수: {len(store_benefits)}")
        for benefit in store_benefits:
            print(f"[패스 생성기] 혜택: {benefit.store_name} - {benefit.description}")
        
        return recommended_stores, store_benefits

    def _stable_redemption_code(self, source: str) -> str:
        """소스 문자열로부터 안정된 해시 코드 생성"""
        digest = hashlib.sha1(source.encode('utf-8')).hexdigest().upper()
        return digest[:8]  # 8자리 코드
    
    def _attach_redemption_codes(self, benefits: List[Benefit]):
        """혜택들에 상환 코드 부여"""
        for benefit in benefits:
            if not getattr(benefit, 'redemption_code', None):
                source = f"{benefit.store_name}|{benefit.benefit_type}|{benefit.description}"
                benefit.redemption_code = self._stable_redemption_code(source)
                print(f"[패스 생성기] 혜택 코드 생성: {benefit.redemption_code} -> {benefit.description[:30]}...")

    def create_pass_object(self, user_prefs: UserPrefs, pass_type: PassType, 
                          theme: Theme, stores: List[Store], benefits: List[Benefit]) -> Pass:
        """Pass 객체 생성"""
        # 패스 ID 생성
        pass_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(user_prefs)) % 10000:04d}"
        
        # 패스 생성
        pass_obj = Pass(
            pass_id=pass_id,
            pass_type=pass_type,
            theme=theme,
            stores=stores,
            benefits=benefits,
            created_at=datetime.now().isoformat(),
            user_prefs=user_prefs
        )
        
        # 혜택 전역 코드 부여
        self._attach_redemption_codes(pass_obj.benefits)
        
        print(f"[패스 생성기] 패스 객체 생성 완료: {pass_id}")
        return pass_obj

    def save_pass_to_file(self, pass_obj: Pass) -> bool:
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
                'user_prefs': pass_obj.user_prefs.__dict__
            }
            
            filename = f"pass_{pass_obj.pass_id}.json"
            filepath = os.path.join(saved_passes_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pass_data, f, ensure_ascii=False, indent=2)
            
            print(f"[패스 생성기] 패스 저장 완료: {filepath}")
            return True
            
        except Exception as e:
            print(f"[패스 생성기] 패스 저장 중 오류: {e}")
            return False

    def generate_pass(self, user_prefs: UserPrefs, pass_type: PassType, theme: Theme) -> Optional[Pass]:
        """
        메인 패스 생성 함수
        AI 기반으로 사용자 선호도에 맞는 맞춤형 패스를 생성합니다.
        """
        try:
            print(f"[패스 생성기] 패스 생성 시작 - 타입: {pass_type.value}, 테마: {theme.value}")
            
            # 1. 데이터 로드
            all_stores = self.load_stores()
            all_benefits = self.load_benefits()
            
            if not all_stores:
                print("[패스 생성기] 상점 데이터가 없습니다.")
                return None
            
            # 2. 테마별 상점 필터링
            filtered_stores = self.filter_stores_by_theme(all_stores, theme)
            
            # 3. AI 프롬프트 생성
            prompt = self.generate_ai_prompt(user_prefs, pass_type, theme, filtered_stores)
            
            # 4. AI 추천 받기
            recommended_store_names = self.get_ai_recommendations(prompt)
            
            # 5. 상점과 혜택 매칭
            recommended_stores, store_benefits = self.match_stores_and_benefits(
                recommended_store_names, all_stores, all_benefits
            )
            
            # 6. 패스 객체 생성
            pass_obj = self.create_pass_object(
                user_prefs, pass_type, theme, recommended_stores, store_benefits
            )
            
            # 7. 패스 저장
            if self.save_pass_to_file(pass_obj):
                print(f"[패스 생성기] 패스 생성 및 저장 완료: {pass_obj.pass_id}")
            else:
                print(f"[패스 생성기] 패스 생성 완료, 저장 실패: {pass_obj.pass_id}")
            
            return pass_obj
            
        except Exception as e:
            print(f"[패스 생성기] 패스 생성 중 오류 발생: {e}")
            return None

    def clear_cache(self):
        """캐시 초기화"""
        self.stores_cache = None
        self.benefits_cache = None
        self.stores_raw_cache = None
        print("[패스 생성기] 캐시 초기화 완료")


# 전역 패스 생성기 인스턴스
_pass_generator_instance = None

def get_pass_generator() -> PassGenerator:
    """싱글톤 패턴으로 PassGenerator 인스턴스 반환"""
    global _pass_generator_instance
    if _pass_generator_instance is None:
        _pass_generator_instance = PassGenerator()
    return _pass_generator_instance

def generate_pass(user_prefs: UserPrefs, pass_type: PassType, theme: Theme) -> Optional[Pass]:
    """
    패스 생성 함수 (기존 호환성 유지)
    """
    generator = get_pass_generator()
    return generator.generate_pass(user_prefs, pass_type, theme)
