#!/usr/bin/env python3
"""
패스 생성 모듈 테스트 스크립트
"""
import sys
import os

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pass_generator import PassGenerator
from models import UserPrefs, PassType, Theme

def test_pass_generation():
    """패스 생성 기능 테스트"""
    print("🧪 패스 생성 모듈 테스트 시작")
    
    # PassGenerator 인스턴스 생성
    generator = PassGenerator()
    print("✅ PassGenerator 인스턴스 생성 완료")
    
    # 테스트용 사용자 선호도 생성
    user_prefs = UserPrefs(
        budget='보통',
        interests=['해산물', '카페'],
        dietary_restrictions=[],
        group_size=2,
        duration='반나절',
        transportation='도보'
    )
    print("✅ 사용자 선호도 객체 생성 완료")
    
    # 패스 생성 테스트
    try:
        print("🤖 AI 기반 패스 생성 중...")
        generated_pass = generator.generate_pass(
            user_prefs=user_prefs,
            pass_type=PassType.LIGHT,
            theme=Theme.FOOD
        )
        
        if generated_pass:
            print("✅ 패스 생성 성공!")
            print(f"   - 패스 ID: {generated_pass.pass_id}")
            print(f"   - 패스 타입: {generated_pass.pass_type.value}")
            print(f"   - 테마: {generated_pass.theme.value}")
            print(f"   - 포함된 상점 수: {len(generated_pass.stores)}")
            print(f"   - 포함된 혜택 수: {len(generated_pass.benefits)}")
            
            print("\n📍 추천된 상점들:")
            for i, store in enumerate(generated_pass.stores, 1):
                print(f"   {i}. {store.name} ({store.category})")
            
            print("\n🎁 포함된 혜택들:")
            for i, benefit in enumerate(generated_pass.benefits, 1):
                print(f"   {i}. {benefit.description} (코드: {getattr(benefit, 'redemption_code', 'N/A')})")
            
            return True
        else:
            print("❌ 패스 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 패스 생성 중 오류: {e}")
        return False

def test_module_functions():
    """모듈 기능들 개별 테스트"""
    print("\n🔧 모듈 기능 테스트")
    
    generator = PassGenerator()
    
    # 데이터 로드 테스트
    stores = generator.load_stores()
    print(f"✅ 상점 데이터 로드: {len(stores)}개")
    
    benefits = generator.load_benefits()
    print(f"✅ 혜택 데이터 로드: {len(benefits)}개")
    
    stores_raw = generator.load_stores_raw()
    print(f"✅ 원본 상점 데이터 로드: {len(stores_raw)}개")
    
    # 테마별 필터링 테스트
    filtered_stores = generator.filter_stores_by_theme(stores, Theme.FOOD)
    print(f"✅ 음식 테마 필터링: {len(filtered_stores)}개")
    
    return True

if __name__ == "__main__":
    print("🎯 제물포GO 패스 생성 모듈 테스트")
    print("=" * 50)
    
    # 기본 기능 테스트
    if test_module_functions():
        print("\n✅ 모듈 기능 테스트 완료")
    else:
        print("\n❌ 모듈 기능 테스트 실패")
        sys.exit(1)
    
    # 패스 생성 테스트
    if test_pass_generation():
        print("\n🎉 패스 생성 모듈화 성공!")
        print("   새로운 pass_generator.py 모듈이 정상적으로 작동합니다.")
    else:
        print("\n❌ 패스 생성 테스트 실패")
        print("   AI API 키가 설정되지 않았거나 네트워크 문제일 수 있습니다.")
        sys.exit(1)
