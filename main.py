import json
import os
import uuid
import qrcode
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai


@dataclass
class Store:
    """파트너 상점 정보를 담는 클래스"""
    id: str
    name: str
    category: str
    area: str
    themes: List[str]
    desc: str
    reviews: int
    is_franchise: bool
    synergy: int = 0  # 계산될 상생 점수


@dataclass
class Benefit:
    """상점에서 제공하는 혜택 정보를 담는 클래스"""
    id: str
    store_id: str
    desc: str
    value: int  # 사용자 만족도 점수
    eco_value: int  # 실제 금전적 가치 (원)


@dataclass
class UserPrefs:
    """사용자의 요청 정보를 담는 클래스"""
    themes: List[str]
    request: str
    pass_type: str  # "light" 또는 "premium"
    budget: int  # 패스 타입에 따라 자동 설정


@dataclass
class PassType:
    """패스 타입 정보를 담는 클래스"""
    name: str
    price: int
    description: str


# 패스 타입 정의
PASS_TYPES = {
    "light": PassType(
        name="스탠다드 패스",
        price=9900,
        description="기본적인 혜택들로 구성된 가성비 패스"
    ),
    "premium": PassType(
        name="프리미엄 패스", 
        price=14900,
        description="다양한 혜택들로 구성된 풀 패키지 패스"
    ),
    "citizen": PassType(
        name="시민 우대 패스", 
        price=7000,
        description="인천 시민을 위해 꼭 필요한 혜택들로 구성된 패스"
    )
}


@dataclass
class Pass:
    """최종 생성된 맞춤형 패스 정보를 담는 클래스"""
    user_id: str
    recs: List[Dict[str, Any]]  # 추천된 혜택과 이유
    avg_synergy: float
    total_value: int
    pass_id: str = ""  # 패스 고유 식별자
    pass_type: str = ""  # 패스 타입
    created_at: str = ""  # 생성 시간
    qr_code_path: str = ""  # QR 코드 이미지 경로


@dataclass
class Theme:
    """테마 정보를 담는 클래스"""
    id: str
    name: str
    description: str


def load_data() -> tuple[List[Store], List[Benefit]]:
    """stores.json과 benefits.json 파일을 읽어 Store와 Benefit 객체 리스트를 생성"""
    try:
        # stores.json 로드
        with open('stores.json', 'r', encoding='utf-8') as f:
            stores_data = json.load(f)
        
        # benefits.json 로드
        with open('benefits.json', 'r', encoding='utf-8') as f:
            benefits_data = json.load(f)
        
        # Store 객체들 생성
        stores = []
        for store_data in stores_data['stores']:
            store = Store(**store_data)
            store.synergy = get_synergy_score(store)  # 상생 점수 계산
            stores.append(store)
        
        # Benefit 객체들 생성
        benefits = []
        for benefit_data in benefits_data['benefits']:
            benefit = Benefit(**benefit_data)
            benefits.append(benefit)
        
        return stores, benefits
    
    except FileNotFoundError as e:
        print(f"데이터 파일을 찾을 수 없습니다: {e}")
        return [], []
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {e}")
        return [], []


def load_themes() -> List[Theme]:
    """themes.json 파일을 읽어 Theme 객체 리스트를 생성"""
    try:
        with open('themes.json', 'r', encoding='utf-8') as f:
            themes_data = json.load(f)
        
        themes = []
        for theme_data in themes_data['themes']:
            theme = Theme(**theme_data)
            themes.append(theme)
        
        return themes
    
    except FileNotFoundError as e:
        print(f"테마 파일을 찾을 수 없습니다: {e}")
        # 기본 테마 반환
        return [
            Theme("seafood", "해산물", "신선한 해산물과 바다의 맛"),
            Theme("cafe", "카페", "편안한 카페 분위기"),
            Theme("traditional", "전통", "한국의 전통 문화와 맛"),
            Theme("retro", "레트로", "옛날 감성과 추억"),
            Theme("quiet", "조용함", "평온하고 조용한 공간")
        ]
    except Exception as e:
        print(f"테마 로드 중 오류 발생: {e}")
        return []


def get_synergy_score(store: Store) -> int:
    """Store의 synergy 점수를 계산"""
    base_score = 50
    
    # 프랜차이즈이면 점수 감소
    if store.is_franchise:
        base_score -= 30
    
    # 리뷰 수가 적을수록 (덜 알려진 곳) 점수 증가
    if store.reviews < 50:
        base_score += 30
    elif store.reviews < 100:
        base_score += 20
    elif store.reviews < 200:
        base_score += 10
    else:
        base_score -= 10
    
    # 골목상권이나 제물포시장 등 특별 지역 보너스
    if store.area in ["골목상권", "제물포시장"]:
        base_score += 25
    elif store.area in ["월미도", "차이나타운"]:
        base_score += 5
    elif store.area in ["인천역"]:
        base_score -= 15
    
    # 0-100 범위로 제한
    return max(0, min(100, base_score))


def get_value_score(benefit: Benefit) -> int:
    """Benefit의 value 점수를 반환 (이미 정의되어 있음)"""
    return benefit.value


def calculate_theme_match_score(benefit: Benefit, store: Store, user_themes: List[str]) -> int:
    """사용자 테마와 상점 테마의 매칭 점수 계산"""
    if not user_themes:
        return 0
    
    matches = sum(1 for theme in user_themes if theme in store.themes)
    return (matches / len(user_themes)) * 100


def generate_pass_id() -> str:
    """패스 고유 ID 생성"""
    return str(uuid.uuid4())[:8].upper()


def generate_qr_code(pass_id: str, save_dir: str = "qr_codes") -> str:
    """QR 코드 생성 및 저장"""
    try:
        # QR 코드 저장 디렉토리 생성
        os.makedirs(save_dir, exist_ok=True)
        
        # QR 코드 데이터 (패스 조회 URL)
        qr_data = f"https://jemulpogo.com/pass/{pass_id}"
        
        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 파일 경로
        qr_filename = f"pass_{pass_id}.png"
        qr_path = os.path.join(save_dir, qr_filename)
        
        # 이미지 저장
        img.save(qr_path)
        
        return qr_path
        
    except Exception as e:
        print(f"[경고] QR 코드 생성 실패: {e}")
        return ""


def save_pass_to_file(pass_obj: Pass, user_email: str = None, user_input: Dict = None) -> bool:
    """패스를 JSON 파일에 저장"""
    try:
        # 패스 데이터 저장 디렉토리 생성
        save_dir = "saved_passes"
        os.makedirs(save_dir, exist_ok=True)
        
        # 패스 정보 가져오기
        pass_info = PASS_TYPES.get(pass_obj.pass_type, PASS_TYPES['light'])
        
        # 저장할 데이터 구성
        pass_data = {
            "pass_id": pass_obj.pass_id,
            "user_id": pass_obj.user_id,
            "user_email": user_email,
            "pass_type": pass_obj.pass_type,
            "created_at": pass_obj.created_at,
            "recommendations": pass_obj.recs,
            "avg_synergy": pass_obj.avg_synergy,
            "total_value": pass_obj.total_value,
            "qr_code_path": pass_obj.qr_code_path,
            "pass_info": {
                "name": pass_info.name,
                "price": pass_info.price,
                "description": pass_info.description,
                "benefits_count": len(pass_obj.recs),
                "total_value": pass_obj.total_value,
                "value_ratio": round((pass_obj.total_value / pass_info.price) * 100, 0) if pass_info.price > 0 else 0
            },
            "user_input": user_input or {}
        }
        
        # 파일 경로
        file_path = os.path.join(save_dir, f"pass_{pass_obj.pass_id}.json")
        
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(pass_data, f, ensure_ascii=False, indent=2)
        
        print(f"[저장] 패스가 저장되었습니다: {file_path}")
        return True
        
    except Exception as e:
        print(f"[오류] 패스 저장 실패: {e}")
        return False


def load_pass_from_file(pass_id: str) -> Dict[str, Any]:
    """패스 ID로 저장된 패스 데이터 로드"""
    try:
        file_path = os.path.join("saved_passes", f"pass_{pass_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            pass_data = json.load(f)
        
        return pass_data
        
    except Exception as e:
        print(f"[오류] 패스 로드 실패: {e}")
        return None


def get_user_passes(user_email: str) -> List[Dict[str, Any]]:
    """사용자의 모든 패스 조회"""
    try:
        save_dir = "saved_passes"
        user_passes = []
        
        if not os.path.exists(save_dir):
            return user_passes
        
        # 모든 패스 파일 검색
        for filename in os.listdir(save_dir):
            if filename.startswith("pass_") and filename.endswith(".json"):
                file_path = os.path.join(save_dir, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    pass_data = json.load(f)
                
                # 사용자 이메일이 일치하는 패스만 추가
                if pass_data.get('user_email') == user_email:
                    user_passes.append(pass_data)
        
        # 생성 시간 기준으로 정렬 (최신순)
        user_passes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return user_passes
        
    except Exception as e:
        print(f"[오류] 사용자 패스 조회 실패: {e}")
        return []


def generate_pass(prefs: UserPrefs, stores: List[Store], benefits: List[Benefit]) -> Pass:
    """메인 추천 엔진 - 하이브리드 추천 알고리즘"""
    
    # 패스 타입 정보 가져오기
    pass_info = PASS_TYPES[prefs.pass_type]
    
    # API 키 및 모델 설정 로드
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')  # 기본값 설정
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("[경고] Gemini API 키가 설정되지 않았습니다. 규칙 기반 추천만 사용합니다.")
        return generate_rule_based_pass(prefs, stores, benefits)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        print(f"[AI] Gemini 모델 '{model_name}' 연결 성공!")
    except Exception as e:
        print(f"[경고] Gemini API 연결 실패: {e}. 규칙 기반 추천만 사용합니다.")
        return generate_rule_based_pass(prefs, stores, benefits)
    
    # 1단계: 규칙 기반 후보 필터링
    candidates = []
    store_dict = {store.id: store for store in stores}
    
    for benefit in benefits:
        store = store_dict.get(benefit.store_id)
        if not store:
            continue
        
        # 가중치 설정
        w1, w2, w3 = 0.4, 0.4, 0.2
        
        theme_match_score = calculate_theme_match_score(benefit, store, prefs.themes)
        prelim_score = (w1 * benefit.value) + (w2 * store.synergy) + (w3 * theme_match_score)
        
        candidates.append({
            'benefit': benefit,
            'store': store,
            'prelim_score': prelim_score
        })
    
    # 상위 20개 후보 선택
    candidates.sort(key=lambda x: x['prelim_score'], reverse=True)
    top_candidates = candidates[:20]
    
    # 2단계: LLM 기반 순위 재조정
    try:
        candidate_list_text = ""
        for i, candidate in enumerate(top_candidates, 1):
            benefit = candidate['benefit']
            store = candidate['store']
            candidate_list_text += f"{i}. [혜택 ID: {benefit.id}] {store.name}: {benefit.desc} (가치: {benefit.eco_value}원)\n"
        
        prompt = f"""당신은 인천 제물포 지역의 스마트 관광 패스 설계 전문가입니다. 아래는 한 관광객의 구체적인 요청사항과 선택한 패스 정보입니다.
---
요청사항: "{prefs.request}"
선호 테마: {', '.join(prefs.themes) if prefs.themes else '없음'}
선택한 패스: {pass_info.name} ({pass_info.price:,}원)
패스 구성: 총 혜택 가치가 패스 가격의 최대 2배({pass_info.price * 2:,}원)까지
---
아래는 추천할 수 있는 혜택 후보 목록입니다. 각 혜택에는 금전적 가치(eco_value)가 포함되어 있습니다.
---
후보 목록:
{candidate_list_text}
---
위 후보 목록 중에서, 사용자의 요청사항을 가장 잘 만족시키면서, {pass_info.name}에 적합한 혜택들을 선택해주세요.

중요한 조건들:
1. 사용자의 요청사항과 선호 테마를 최대한 반영해주세요.
2. 선택된 혜택들의 총 금전적 가치가 패스 가격({pass_info.price:,}원) 이상이어야 합니다.
3. 선택된 혜택들의 총 금전적 가치가 패스 가격의 2배({pass_info.price * 2:,}원)를 초과하면 안 됩니다.
4. 다양한 카테고리의 혜택을 조합해주세요.
5. 가능한 한 많은 혜택을 포함하되, 가치 제한을 준수해주세요.

그 이유와 함께 JSON 형식으로 반환해주세요. JSON 형식은 다음과 같아야 합니다:
[{{"benefit_id": "B008", "reason": "조용히 책을 읽고 싶다는 요청에 가장 잘 맞는 장소입니다."}}, ...]

JSON만 반환해주세요. 다른 설명은 포함하지 마세요."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON 파싱
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith('```'):
            response_text = response_text[3:-3].strip()
        
        try:
            ai_recommendations = json.loads(response_text)
        except json.JSONDecodeError:
            print("[경고] AI 응답 파싱 실패. 규칙 기반 추천을 사용합니다.")
            return generate_rule_based_pass(prefs, stores, benefits)
        
        # 3단계: 최종 검증 및 패스 생성
        final_recs = []
        total_eco_value = 0
        synergy_scores = []
        max_value_limit = pass_info.price * 2  # 가격의 2배까지 제한
        
        benefit_dict = {benefit.id: benefit for benefit in benefits}
        
        for rec in ai_recommendations:
            benefit_id = rec.get('benefit_id')
            reason = rec.get('reason', '추천된 혜택입니다.')
            
            if benefit_id in benefit_dict:
                benefit = benefit_dict[benefit_id]
                store = store_dict.get(benefit.store_id)
                
                # 가치 제한 확인
                if store and total_eco_value + benefit.eco_value <= max_value_limit:
                    final_recs.append({
                        'benefit_id': benefit_id,
                        'store_name': store.name,
                        'benefit_desc': benefit.desc,
                        'eco_value': benefit.eco_value,
                        'reason': reason
                    })
                    total_eco_value += benefit.eco_value
                    synergy_scores.append(store.synergy)
        
        # 검증
        avg_synergy = sum(synergy_scores) / len(synergy_scores) if synergy_scores else 0
        
        if avg_synergy < 40:  # 최소 상생 점수 기준
            print("[경고] 상생 점수가 기준에 미달합니다. 규칙 기반 추천을 사용합니다.")
            return generate_rule_based_pass(prefs, stores, benefits)
        
        if total_eco_value < pass_info.price:  # 패스 가격 이상의 가치 보장
            print("[경고] 혜택 가치가 패스 가격에 미달합니다. 규칙 기반 추천을 보완합니다.")
            return generate_rule_based_pass(prefs, stores, benefits, existing_recs=final_recs)
        
        if total_eco_value > pass_info.price * 2:  # 가격의 2배 초과 방지
            print("[경고] 혜택 가치가 너무 높습니다. 규칙 기반 추천을 사용합니다.")
            return generate_rule_based_pass(prefs, stores, benefits)
        
        # 패스 고유 ID 및 시간 생성
        pass_id = generate_pass_id()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # QR 코드 생성
        qr_code_path = generate_qr_code(pass_id)
        
        return Pass(
            user_id="user_001",
            recs=final_recs,
            avg_synergy=avg_synergy,
            total_value=total_eco_value,
            pass_id=pass_id,
            pass_type=prefs.pass_type,
            created_at=created_at,
            qr_code_path=qr_code_path
        )
    
    except Exception as e:
        print(f"[경고] AI 추천 중 오류 발생: {e}. 규칙 기반 추천을 사용합니다.")
        return generate_rule_based_pass(prefs, stores, benefits)


def generate_rule_based_pass(prefs: UserPrefs, stores: List[Store], benefits: List[Benefit], existing_recs: List[Dict] = None) -> Pass:
    """규칙 기반 추천 (백업 또는 보완용)"""
    pass_info = PASS_TYPES[prefs.pass_type]
    store_dict = {store.id: store for store in stores}
    
    # 기존 추천이 있다면 해당 benefit들을 제외
    used_benefit_ids = set()
    total_used_value = 0
    
    if existing_recs:
        used_benefit_ids = {rec['benefit_id'] for rec in existing_recs}
        total_used_value = sum(rec['eco_value'] for rec in existing_recs)
    
    # 후보 계산
    candidates = []
    for benefit in benefits:
        if benefit.id in used_benefit_ids:
            continue
            
        store = store_dict.get(benefit.store_id)
        if not store:
            continue
        
        # 점수 계산
        w1, w2, w3 = 0.4, 0.4, 0.2
        theme_match_score = calculate_theme_match_score(benefit, store, prefs.themes)
        score = (w1 * benefit.value) + (w2 * store.synergy) + (w3 * theme_match_score)
        
        candidates.append({
            'benefit': benefit,
            'store': store,
            'score': score
        })
    
    # 상위 후보들을 가치 제한 내에서 선택
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    final_recs = existing_recs.copy() if existing_recs else []
    current_value = total_used_value
    synergy_scores = []
    max_value_limit = pass_info.price * 2  # 가격의 2배까지 제한
    
    if existing_recs:
        # 기존 추천의 상생 점수도 포함
        for rec in existing_recs:
            benefit_id = rec['benefit_id']
            for benefit in benefits:
                if benefit.id == benefit_id:
                    store = store_dict.get(benefit.store_id)
                    if store:
                        synergy_scores.append(store.synergy)
                    break
    
    # 가치 제한 내에서 최대한 많은 혜택 선택
    for candidate in candidates:
        benefit = candidate['benefit']
        store = candidate['store']
        
        # 가치 제한 확인
        if current_value + benefit.eco_value > max_value_limit:
            continue
            
        final_recs.append({
            'benefit_id': benefit.id,
            'store_name': store.name,
            'benefit_desc': benefit.desc,
            'eco_value': benefit.eco_value,
            'reason': f"높은 만족도({benefit.value}점)와 상생 점수({store.synergy}점)를 바탕으로 추천됩니다."
        })
        current_value += benefit.eco_value
        synergy_scores.append(store.synergy)
    
    avg_synergy = sum(synergy_scores) / len(synergy_scores) if synergy_scores else 0
    
    # 패스 고유 ID 및 시간 생성
    pass_id = generate_pass_id()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # QR 코드 생성
    qr_code_path = generate_qr_code(pass_id)
    
    return Pass(
        user_id="user_001",
        recs=final_recs,
        avg_synergy=avg_synergy,
        total_value=current_value,
        pass_id=pass_id,
        pass_type=prefs.pass_type,
        created_at=created_at,
        qr_code_path=qr_code_path
    )


def print_welcome():
    """환영 메시지 출력"""
    print("제물포GO 패스 - AI 맞춤형 관광 추천 시스템")
    print("=" * 50)
    print("인천 제물포구의 숨은 명소와 상생 혜택을 발견해보세요!")
    print()


def get_user_input() -> UserPrefs:
    """사용자 입력 받기"""
    print("맞춤형 패스 생성을 위한 정보를 입력해주세요:")
    print()
    
    # 사용 가능한 테마 로드
    available_themes = load_themes()
    
    # 테마 입력
    print("1. 관심 테마를 선택해주세요 (번호로 선택, 쉼표로 구분):")
    for i, theme in enumerate(available_themes, 1):
        print(f"   {i}. {theme.name}")
    
    print("   또는 직접 입력: (예: 해산물, 카페, 전통)")
    themes_input = input("테마 선택: ").strip()
    
    # 번호로 선택했는지 확인
    selected_themes = []
    if themes_input.replace(',', '').replace(' ', '').isdigit():
        # 번호로 선택한 경우
        theme_numbers = [int(x.strip()) for x in themes_input.split(',') if x.strip().isdigit()]
        for num in theme_numbers:
            if 1 <= num <= len(available_themes):
                selected_themes.append(available_themes[num-1].name)
    else:
        # 직접 입력한 경우
        selected_themes = [theme.strip() for theme in themes_input.split(',') if theme.strip()]
    
    # 자유 요청사항 입력
    print("\n2. 자유롭게 원하는 것을 설명해주세요:")
    print("   예시: 조용한 곳에서 책을 읽고 싶어요, 맛있는 해산물을 먹고 싶어요")
    request = input("요청사항: ").strip()
    
    # 패스 타입 선택
    print("\n3. 패스 타입을 선택해주세요:")
    print("   1번 스탠다드 패스 (9,900원) - 기본적인 혜택들로 구성")
    print("   2번 프리미엄 패스 (14,900원) - 다양한 혜택들로 구성")
    print("   3번 시민 우대 패스 (7,000원) - 꼭 필요한 혜택들로 구성")
    print("   ※ 모든 패스는 가격 대비 최대 2배까지의 가치를 제공합니다")
    
    while True:
        choice = input("선택 (1, 2, 또는 3): ").strip()
        if choice == "1":
            pass_type = "light"
            budget = PASS_TYPES["light"].price
            break
        elif choice == "2":
            pass_type = "premium"
            budget = PASS_TYPES["premium"].price
            break
        elif choice == "3":
            pass_type = "citizen"
            budget = PASS_TYPES["citizen"].price
            break
        else:
            print("1, 2, 또는 3을 입력해주세요.")
    
    return UserPrefs(themes=selected_themes, request=request, pass_type=pass_type, budget=budget)


def print_pass_result(pass_obj: Pass, prefs: UserPrefs):
    """생성된 패스 결과 출력"""
    pass_info = PASS_TYPES[prefs.pass_type]
    
    print("\n" + "=" * 60)
    print("당신만의 제물포GO 패스가 생성되었습니다!")
    print("=" * 60)
    
    if not pass_obj.recs:
        print("[오류] 조건에 맞는 추천을 찾을 수 없습니다. 다른 조건으로 시도해주세요.")
        return
    
    print(f"패스 정보:")
    print(f"   • 패스 ID: {pass_obj.pass_id}")
    print(f"   • 생성 시간: {pass_obj.created_at}")
    print(f"   • 패스 타입: {pass_info.name}")
    print(f"   • 패스 가격: {pass_info.price:,}원")
    print(f"   • 혜택 개수: {len(pass_obj.recs)}개")
    print(f"   • 총 혜택 가치: {pass_obj.total_value:,}원")
    print(f"   • 가치 대비 효과: {(pass_obj.total_value / pass_info.price * 100):.0f}%")
    print(f"   • 평균 상생 점수: {pass_obj.avg_synergy:.1f}점")
    
    if pass_obj.qr_code_path:
        print(f"   • QR 코드: {pass_obj.qr_code_path}")
    
    print()
    
    print("포함된 혜택:")
    print("-" * 60)
    
    for i, rec in enumerate(pass_obj.recs, 1):
        print(f"{i}. 상점: {rec['store_name']}")
        print(f"   혜택: {rec['benefit_desc']}")
        print(f"   가치: {rec['eco_value']:,}원")
        print(f"   추천 이유: {rec['reason']}")
        print()
    
    print("-" * 60)
    
    # 가치 평가
    value_ratio = pass_obj.total_value / pass_info.price
    if value_ratio >= 2.0:
        print("[평가] 훌륭한 가성비! 패스 가격의 2배 이상 가치를 제공합니다!")
    elif value_ratio >= 1.5:
        print("[평가] 좋은 가성비! 패스 가격의 1.5배 이상 가치를 제공합니다!")
    else:
        print("[평가] 적당한 가성비의 패스입니다!")
    
    # 상생 효과 평가
    if pass_obj.avg_synergy >= 70:
        print("[상생] 우수한 지역 상생 효과를 가진 패스입니다!")
    elif pass_obj.avg_synergy >= 50:
        print("[상생] 좋은 지역 상생 효과를 가진 패스입니다!")
    else:
        print("[상생] 관광 만족도에 집중된 패스입니다!")


def main():
    """메인 애플리케이션 루프 (터미널 모드)"""
    # 환경 변수 로드
    load_dotenv()
    
    # 데이터 로드
    print("데이터를 로드하는 중...")
    stores, benefits = load_data()
    
    if not stores or not benefits:
        print("[오류] 데이터 로드에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    print(f"[완료] {len(stores)}개 상점, {len(benefits)}개 혜택이 로드되었습니다.")
    print()
    
    while True:
        print_welcome()
        
        # 사용자 입력 받기
        user_prefs = get_user_input()
        
        print(f"\n[처리 중] {PASS_TYPES[user_prefs.pass_type].name}를 생성하는 중...")
        
        # 패스 생성
        generated_pass = generate_pass(user_prefs, stores, benefits)
        
        # 패스 저장을 위한 사용자 입력 정보
        user_input_data = {
            'themes': user_prefs.themes,
            'request': user_prefs.request,
            'pass_type': user_prefs.pass_type
        }
        
        # 패스 저장 (선택적으로 사용자 이메일도 받을 수 있음)
        print(f"\n[저장] 패스 데이터를 저장하는 중...")
        save_success = save_pass_to_file(generated_pass, None, user_input_data)
        
        if save_success:
            print(f"[완료] 패스 ID: {generated_pass.pass_id}")
        
        # 결과 출력
        print_pass_result(generated_pass, user_prefs)
        
        # 계속 진행 여부 확인
        print("\n" + "=" * 60)
        while True:
            continue_choice = input("다시 생성하시겠습니까? (y/n): ").strip().lower()
            if continue_choice in ['y', 'yes', 'ㅇ']:
                print()
                break
            elif continue_choice in ['n', 'no', 'ㄴ']:
                print("\n[종료] 제물포GO 패스를 이용해주셔서 감사합니다!")
                return
            else:
                print("y 또는 n을 입력해주세요.")


if __name__ == "__main__":
    main()
