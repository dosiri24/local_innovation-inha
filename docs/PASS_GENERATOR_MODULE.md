# 제물포GO 패스 생성 모듈

## 📖 개요
`pass_generator.py`는 제물포GO 프로젝트의 패스 생성 기능을 모듈화한 전용 모듈입니다. AI 기반 맞춤형 관광 패스 생성을 담당합니다.

## 🏗️ 구조

### 핵심 클래스: `PassGenerator`
```python
from pass_generator import PassGenerator, generate_pass
```

### 주요 기능
1. **AI 기반 상점 추천** - Google Gemini AI 활용
2. **테마별 상점 필터링** - 음식, 문화, 쇼핑, 엔터테인먼트
3. **혜택 매칭** - 상점과 혜택 자동 연결
4. **패스 생성 및 저장** - JSON 형태로 영구 저장
5. **캐싱 시스템** - 성능 최적화

## 🚀 사용법

### 1. 기본 사용법 (호환성 유지)
```python
from models import UserPrefs, PassType, Theme
from pass_generator import generate_pass

# 사용자 선호도 설정
user_prefs = UserPrefs(
    budget='보통',
    interests=['해산물', '카페'],
    dietary_restrictions=[],
    group_size=2,
    duration='반나절',
    transportation='도보'
)

# 패스 생성
generated_pass = generate_pass(
    user_prefs=user_prefs,
    pass_type=PassType.LIGHT,
    theme=Theme.FOOD
)
```

### 2. 클래스 인스턴스 사용법
```python
from pass_generator import PassGenerator

# 생성기 인스턴스 생성
generator = PassGenerator()

# 데이터 로드
stores = generator.load_stores()
benefits = generator.load_benefits()

# 패스 생성
generated_pass = generator.generate_pass(user_prefs, pass_type, theme)
```

### 3. 싱글톤 패턴 사용법
```python
from pass_generator import get_pass_generator

# 싱글톤 인스턴스 가져오기
generator = get_pass_generator()
generated_pass = generator.generate_pass(user_prefs, pass_type, theme)
```

## 📊 데이터 구조

### UserPrefs (사용자 선호도)
```python
UserPrefs(
    budget: str,           # '저렴', '보통', '고급'
    interests: List[str],  # ['해산물', '카페', '전통', ...]
    dietary_restrictions: List[str],  # 식이 제한사항
    group_size: int,       # 그룹 크기
    duration: str,         # '반나절', '하루종일'
    transportation: str    # '도보', '대중교통', '자동차'
)
```

### PassType (패스 타입)
- `PassType.LIGHT` - 스탠다드 패스
- `PassType.PREMIUM` - 프리미엄 패스  
- `PassType.CITIZEN` - 시민 우대 패스

### Theme (테마)
- `Theme.FOOD` - 음식 테마
- `Theme.CULTURE` - 문화 테마
- `Theme.SHOPPING` - 쇼핑 테마
- `Theme.ENTERTAINMENT` - 엔터테인먼트 테마

## 🔧 메서드 설명

### PassGenerator 클래스 메서드

#### 데이터 로드
```python
load_stores() -> List[Store]           # 상점 데이터 로드
load_benefits() -> List[Benefit]       # 혜택 데이터 로드
load_stores_raw() -> List[Dict]        # 원본 상점 데이터 로드
```

#### 필터링 및 추천
```python
filter_stores_by_theme(stores: List[Store], theme: Theme) -> List[Store]
generate_ai_prompt(user_prefs, pass_type, theme, stores) -> str
get_ai_recommendations(prompt: str) -> List[str]
```

#### 매칭 및 생성
```python
match_stores_and_benefits(store_names, stores, benefits) -> tuple
create_pass_object(user_prefs, pass_type, theme, stores, benefits) -> Pass
save_pass_to_file(pass_obj: Pass) -> bool
```

#### 유틸리티
```python
clear_cache()  # 캐시 초기화
```

## 🎯 핵심 알고리즘

### 1. 패스 생성 프로세스
```
사용자 입력 → 테마별 필터링 → AI 추천 → 혜택 매칭 → 패스 생성 → 저장
```

### 2. AI 추천 시스템
- Google Gemini 1.5 Flash 모델 사용
- 사용자 선호도 + 상점 정보를 프롬프트로 구성
- JSON 형태로 3-5개 상점 추천받음

### 3. 혜택 매칭 시스템
- 상점명 → 상점 ID 매핑
- 상점 ID → 혜택 목록 매핑
- 자동 해시 코드 생성

## 🔒 환경 설정

### 필수 환경 변수
```bash
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash  # 선택사항 (기본값)
```

### 의존성 패키지
```bash
pip install google-generativeai python-dotenv
```

## 📁 파일 구조
```
src/
├── pass_generator.py     # 패스 생성 모듈 (NEW)
├── services.py          # 기타 서비스 (패스 생성 제외)
├── models.py            # 데이터 모델
├── routes.py            # Flask 라우트
└── app.py              # Flask 앱

data/
├── stores.json         # 상점 데이터
└── benefits.json       # 혜택 데이터

storage/
└── saved_passes/       # 생성된 패스 저장소
```

## 🧪 테스트

### 테스트 실행
```bash
python test_pass_generator.py
```

### 테스트 항목
- ✅ 모듈 로드 테스트
- ✅ 데이터 로드 테스트
- ✅ 테마별 필터링 테스트
- ✅ AI 추천 테스트
- ✅ 패스 생성 및 저장 테스트

## 🚀 성능 최적화

### 캐싱 시스템
- 상점 데이터 캐싱
- 혜택 데이터 캐싱
- 원본 데이터 캐싱

### 싱글톤 패턴
- PassGenerator 인스턴스 재사용
- AI 모델 초기화 최적화

## 🔄 마이그레이션 가이드

### 기존 코드에서 새 모듈로 전환

#### Before (services.py)
```python
from services import generate_pass
```

#### After (pass_generator.py)
```python
from pass_generator import generate_pass  # 동일한 인터페이스 유지
```

### 변경 사항
1. **새 파일**: `src/pass_generator.py` 추가
2. **기존 파일**: `src/services.py`에서 패스 생성 관련 함수 제거
3. **import 변경**: `routes.py`에서 import 경로 수정
4. **호환성 유지**: 기존 `generate_pass()` 함수 인터페이스 동일

## 📝 로그 시스템

### 로그 프리픽스
- `[패스 생성기]` - 일반 정보
- `[패스 생성기] AI API 키 존재: True/False` - API 설정 상태
- `[패스 생성기] 테마 '음식' 필터링: N개 상점` - 필터링 결과
- `[패스 생성기] 추천된 상점들: [...]` - AI 추천 결과
- `[패스 생성기] 혜택 매칭: 상점명 -> 상점ID` - 매칭 과정
- `[패스 생성기] 패스 생성 완료: 패스ID` - 생성 완료

## 💡 사용 팁

1. **환경 변수 확인**: AI 기능 사용 전 `GEMINI_API_KEY` 설정 필수
2. **캐시 활용**: 동일한 인스턴스 재사용으로 성능 향상
3. **오류 처리**: AI API 호출 실패 시 적절한 예외 처리
4. **로그 모니터링**: 패스 생성 과정 추적 가능

## 🎉 완료!

패스 생성 기능이 독립적인 모듈로 분리되어 코드의 모듈성과 유지보수성이 크게 향상되었습니다!
