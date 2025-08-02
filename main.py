import json
import os
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
    max_benefits: int
    description: str


# 패스 타입 정의
PASS_TYPES = {
    "light": PassType(
        name="라이트 패스",
        price=7000,
        max_benefits=3,
        description="기본적인 혜택 3개로 구성된 가성비 패스"
    ),
    "premium": PassType(
        name="프리미엄 패스", 
        price=15000,
        max_benefits=5,
        description="다양한 혜택 5개로 구성된 풀 패키지 패스"
    )
}


@dataclass
class Pass:
    """최종 생성된 맞춤형 패스 정보를 담는 클래스"""
    user_id: str
    recs: List[Dict[str, Any]]  # 추천된 혜택과 이유
    avg_synergy: float
    total_value: int


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
패스 구성: 최대 {pass_info.max_benefits}개 혜택
---
아래는 추천할 수 있는 혜택 후보 목록입니다. 각 혜택에는 금전적 가치(eco_value)가 포함되어 있습니다.
---
후보 목록:
{candidate_list_text}
---
위 후보 목록 중에서, 사용자의 요청사항을 가장 잘 만족시키면서, {pass_info.name}에 적합한 **정확히 {pass_info.max_benefits}개**의 혜택을 선택해주세요.

중요한 조건들:
1. 정확히 {pass_info.max_benefits}개의 혜택만 선택해야 합니다.
2. 사용자의 요청사항과 선호 테마를 최대한 반영해주세요.
3. 선택된 혜택들의 총 금전적 가치가 패스 가격({pass_info.price:,}원)보다 높아야 합니다.
4. 다양한 카테고리의 혜택을 조합해주세요.

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
        
        benefit_dict = {benefit.id: benefit for benefit in benefits}
        
        for rec in ai_recommendations:
            benefit_id = rec.get('benefit_id')
            reason = rec.get('reason', '추천된 혜택입니다.')
            
            if benefit_id in benefit_dict and len(final_recs) < pass_info.max_benefits:
                benefit = benefit_dict[benefit_id]
                store = store_dict.get(benefit.store_id)
                
                if store:
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
        
        return Pass(
            user_id="user_001",
            recs=final_recs,
            avg_synergy=avg_synergy,
            total_value=total_eco_value
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
    
    # 상위 후보들을 패스 타입에 맞게 선택
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    final_recs = existing_recs.copy() if existing_recs else []
    current_value = total_used_value
    synergy_scores = []
    
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
    
    # 패스 타입에 맞는 개수까지 선택
    for candidate in candidates:
        if len(final_recs) >= pass_info.max_benefits:
            break
            
        benefit = candidate['benefit']
        store = candidate['store']
        
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
    
    return Pass(
        user_id="user_001",
        recs=final_recs,
        avg_synergy=avg_synergy,
        total_value=current_value
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
    
    # 테마 입력
    print("1. 관심 테마를 입력해주세요 (쉼표로 구분):")
    print("   예시: 해산물, 카페, 전통, 레트로, 조용함")
    themes_input = input("테마: ").strip()
    themes = [theme.strip() for theme in themes_input.split(',') if theme.strip()]
    
    # 자유 요청사항 입력
    print("\n2. 자유롭게 원하는 것을 설명해주세요:")
    print("   예시: 조용한 곳에서 책을 읽고 싶어요, 맛있는 해산물을 먹고 싶어요")
    request = input("요청사항: ").strip()
    
    # 패스 타입 선택
    print("\n3. 패스 타입을 선택해주세요:")
    print("   1번 라이트 패스 (7,000원) - 기본적인 혜택 3개")
    print("   2번 프리미엄 패스 (15,000원) - 다양한 혜택 5개")
    
    while True:
        choice = input("선택 (1 또는 2): ").strip()
        if choice == "1":
            pass_type = "light"
            budget = PASS_TYPES["light"].price
            break
        elif choice == "2":
            pass_type = "premium"
            budget = PASS_TYPES["premium"].price
            break
        else:
            print("1 또는 2를 입력해주세요.")
    
    return UserPrefs(themes=themes, request=request, pass_type=pass_type, budget=budget)


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
    print(f"   • 패스 타입: {pass_info.name}")
    print(f"   • 패스 가격: {pass_info.price:,}원")
    print(f"   • 혜택 개수: {len(pass_obj.recs)}/{pass_info.max_benefits}개")
    print(f"   • 총 혜택 가치: {pass_obj.total_value:,}원")
    print(f"   • 가치 대비 효과: {(pass_obj.total_value / pass_info.price * 100):.0f}%")
    print(f"   • 평균 상생 점수: {pass_obj.avg_synergy:.1f}점")
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
    print(f"   • 패스 타입: {pass_info.name}")
    print(f"   • 패스 가격: {pass_info.price:,}원")
    print(f"   • 혜택 개수: {len(pass_obj.recs)}/{pass_info.max_benefits}개")
    print(f"   • 총 혜택 가치: {pass_obj.total_value:,}원")
    print(f"   • 가치 대비 효과: {(pass_obj.total_value / pass_info.price * 100):.0f}%")
    print(f"   • 평균 상생 점수: {pass_obj.avg_synergy:.1f}점")
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
    """메인 애플리케이션 루프"""
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
