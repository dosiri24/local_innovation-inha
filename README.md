# 제물포GO 패스 - AI 맞춤형 관광 추천 시스템

> 인천 제물포구의 관광 불균형 문제를 해결하는 AI 기반 개인 맞춤형 관광 솔루션

## 📝 프로젝트 개요

"제물포GO 패스"는 관광객이 특정 유명 관광지에만 몰리는 '관광 쏠림' 현상을 해결하고, 잠재력 있는 골목 상권의 소상공인들에게도 기회를 제공하는 혁신적인 추천 시스템입니다.

### 🎯 핵심 목표
- **가치 점수(Value Score)**: 관광객의 만족도 최적화
- **상생 점수(Synergy Score)**: 지역 소상공인과의 상생 효과 극대화
- **하이브리드 AI**: 규칙 기반 + LLM 기반 추천 알고리즘

### 💳 패스 시스템
| 패스 타입 | 가격 | 혜택 개수 | 설명 |
|----------|------|-----------|------|
| **스탠다드 패스** | 9,900원 | 3개 | 기본적인 혜택으로 구성된 가성비 패스 |
| **프리미엄 패스** | 14,900원 | 5개 | 다양한 혜택으로 구성된 풀 패키지 패스 |
| **시민 우대 패스** | 7,000원 | 4개 | 인천 시민을 위한 특별 혜택 패스 |

---

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 수정)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### 2. 실행 방법

#### 터미널 모드 (대화형)
```bash
python main.py
```

#### 웹 서버 모드
```bash
python app.py
```

### 3. 사용 예시

#### 스탠다드 패스 (9,900원)
```
테마: 카페, 조용함
요청사항: 조용한 곳에서 책을 읽으며 커피를 마시고 싶어요
패스 선택: 1 (스탠다드 패스)
```

#### 프리미엄 패스 (14,900원)
```
테마: 해산물, 바다전망, 전통, 체험
요청사항: 신선한 해산물을 먹고 전통 문화도 체험하고 싶어요
패스 선택: 2 (프리미엄 패스)
```

---

## 📁 프로젝트 구조

```
local_innovation-inha/
├── main.py                 # 메인 애플리케이션 (터미널 모드)
├── app.py                  # Flask 웹 서버
├── stores.json             # 상점 데이터
├── benefits.json           # 혜택 데이터
├── requirements.txt        # 의존성 목록
├── .env                    # 환경 변수
├── templates/
│   └── index.html         # 웹 인터페이스
└── README.md              # 프로젝트 문서
```

### 환경 설정

#### 가상 환경 (이미 설정됨)
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

#### 의존성 설치 (이미 설치됨)
```bash
pip install -r requirements.txt
```

---

## 알고리즘 동작 원리

### 1. 규칙 기반 후보 필터링
- **가치 점수 (40%)**: 사용자 만족도
- **상생 점수 (40%)**: 지역 경제 기여도  
- **테마 매칭 (20%)**: 사용자 선호도
- 상위 20개 후보 선정

### 2. LLM 기반 순위 재조정
- Gemini API를 통한 자연어 이해
- 사용자 요청사항과 패스 타입 종합 고려
- 패스별 최적 혜택 개수 조합 생성

### 3. 최종 검증 및 패스 생성
- 상생 점수 최소 기준 (40점) 검증
- 패스 가격 이상의 혜택 가치 검증
- 백업 규칙 기반 추천 제공

---

## 데이터 구조

### 파일 구조
- **`stores.json`**: 상점 정보 관리
- **`benefits.json`**: 혜택 정보 관리

### 데이터 클래스
| 클래스 | 설명 | 주요 필드 |
|--------|------|-----------|
| **Store** | 상점 정보 | `id`, `name`, `category`, `area`, `themes`, `synergy` |
| **Benefit** | 혜택 정보 | `id`, `store_id`, `desc`, `value`, `eco_value` |
| **UserPrefs** | 사용자 선호 | `themes`, `request`, `pass_type`, `budget` |
| **Pass** | 생성된 패스 | `recs`, `avg_synergy`, `total_value` |

---

## 🔧 함수별 기능 정리

### 📊 데이터 관리 함수

#### `load_data() -> tuple[List[Store], List[Benefit]]`
- **기능**: stores.json과 benefits.json 파일을 읽어 Store와 Benefit 객체 생성
- **반환**: (상점 리스트, 혜택 리스트) 튜플
- **특징**: 파일 읽기 실패 시 빈 리스트 반환

#### `get_synergy_score(store: Store) -> int`
- **기능**: 상점의 상생 점수 계산 (0-100점)
- **계산 요소**:
  - 프랜차이즈 여부 (-30점)
  - 리뷰 수 (적을수록 +30~10점)
  - 지역 특성 (골목상권 +25점, 제물포시장 +25점)
- **용도**: 지역 경제 기여도 측정

#### `get_value_score(benefit: Benefit) -> int`
- **기능**: 혜택의 사용자 만족도 점수 반환
- **반환**: benefit.value 값 (이미 정의된 점수)

### 🎯 추천 알고리즘 함수

#### `calculate_theme_match_score(benefit: Benefit, store: Store, user_themes: List[str]) -> int`
- **기능**: 사용자 테마와 상점 테마 매칭 점수 계산
- **계산법**: (매칭된 테마 수 / 사용자 테마 수) × 100
- **반환**: 0-100점의 매칭 점수

#### `generate_pass(prefs: UserPrefs, stores: List[Store], benefits: List[Benefit]) -> Pass`
- **기능**: 메인 추천 엔진 - 하이브리드 추천 알고리즘
- **과정**:
  1. 규칙 기반 후보 필터링 (상위 20개)
  2. LLM 기반 순위 재조정 (Gemini API)
  3. 최종 검증 및 패스 생성
- **백업**: API 실패 시 규칙 기반 추천으로 전환

#### `generate_rule_based_pass(prefs: UserPrefs, stores: List[Store], benefits: List[Benefit], existing_recs: List[Dict] = None) -> Pass`
- **기능**: 규칙 기반 추천 (백업 또는 보완용)
- **가중치**: 만족도(40%) + 상생점수(40%) + 테마매칭(20%)
- **특징**: AI 실패 시나 보완 추천에 사용

### 🖥️ 사용자 인터페이스 함수

#### `print_welcome()`
- **기능**: 환영 메시지 및 프로그램 소개 출력
- **내용**: 제물포GO 패스 타이틀과 설명

#### `get_user_input() -> UserPrefs`
- **기능**: 사용자로부터 입력 받기
- **입력 항목**:
  1. 관심 테마 (쉼표로 구분)
  2. 자유 요청사항
  3. 패스 타입 선택 (1: 스탠다드, 2: 프리미엄, 3: 시민우대)
- **반환**: UserPrefs 객체

#### `print_pass_result(pass_obj: Pass, prefs: UserPrefs)`
- **기능**: 생성된 패스 결과를 포맷팅하여 출력
- **출력 내용**:
  - 패스 정보 (타입, 가격, 혜택 개수, 총 가치, 효율성)
  - 포함된 혜택 목록 (상점명, 혜택 설명, 가치, 추천 이유)
  - 가치 평가 (가성비 평가)
  - 상생 효과 평가

#### `main()`
- **기능**: 메인 애플리케이션 루프 (터미널 모드)
- **과정**:
  1. 환경 변수 로드
  2. 데이터 로드
  3. 사용자 입력 → 패스 생성 → 결과 출력 반복
  4. 재생성 여부 확인

### 📦 데이터 클래스

#### `@dataclass Store`
- **용도**: 파트너 상점 정보 저장
- **필드**: `id`, `name`, `category`, `area`, `themes`, `desc`, `reviews`, `is_franchise`, `synergy`

#### `@dataclass Benefit`
- **용도**: 상점에서 제공하는 혜택 정보 저장
- **필드**: `id`, `store_id`, `desc`, `value`, `eco_value`

#### `@dataclass UserPrefs`
- **용도**: 사용자의 요청 정보 저장
- **필드**: `themes`, `request`, `pass_type`, `budget`

#### `@dataclass PassType`
- **용도**: 패스 타입 정보 저장
- **필드**: `name`, `price`, `max_benefits`, `description`

#### `@dataclass Pass`
- **용도**: 최종 생성된 맞춤형 패스 정보 저장
- **필드**: `user_id`, `recs`, `avg_synergy`, `total_value`

---

## 🏗️ 아키텍처

### 하이브리드 추천 시스템
1. **규칙 기반 필터링**: 객관적 점수 계산으로 후보 선별
2. **AI 기반 재조정**: 자연어 이해로 사용자 의도 파악
3. **검증 및 백업**: 품질 보장과 안정성 확보

### 상생 점수 알고리즘
```python
base_score = 50
if is_franchise: base_score -= 30
if reviews < 50: base_score += 30
if area in ["골목상권", "제물포시장"]: base_score += 25
return max(0, min(100, base_score))
```

---

## 📊 데이터 구조

### 파일 구조
- **`stores.json`**: 상점 정보 관리 (15개 상점)
- **`benefits.json`**: 혜택 정보 관리 (30개 혜택)

### 주요 필드 설명
| 필드 | 설명 | 예시 |
|------|------|------|
| `synergy` | 상생 점수 (0-100) | 골목상권 비프랜차이즈: 85점 |
| `value` | 만족도 점수 (0-100) | 전통차 체험: 90점 |
| `eco_value` | 금전적 가치 (원) | 모듬회 할인: 4,000원 |
| `themes` | 테마 태그 | ["해산물", "바다전망"] |

---

## 🚀 배포 및 확장

### 웹 서버 모드 (app.py)
- **Flask 기반** 웹 애플리케이션
- **REST API** 엔드포인트 제공
- **CORS 지원**으로 프론트엔드 연동 가능

### Google Cloud 배포 지원
- `app.yaml`: Google App Engine 설정
- `gunicorn.conf.py`: WSGI 서버 설정
- 환경 변수 기반 설정 관리

---

## ⚠️ 문제 해결

### API 키 오류
- `.env` 파일의 Gemini API 키 확인
- API 키 없어도 규칙 기반 추천 동작

### 데이터 로드 오류  
- `stores.json` 및 `benefits.json` 파일 위치 확인
- JSON 형식 유효성 검사

### 의존성 오류
```bash
pip install -r requirements.txt
```

### 터미널에서 실행 안 됨
```bash
# 가상환경 활성화 확인
source .venv/bin/activate

# Python 경로 확인
which python
```

---

## 🎯 사용 팁

- **구체적인 요청**: 상세할수록 정확한 추천
- **패스 타입 선택**: 
  - **스탠다드 패스**: 간단한 나들이, 혼자 여행
  - **프리미엄 패스**: 데이트, 가족 여행, 특별한 날
  - **시민 우대 패스**: 현지인 관점의 알찬 구성
- **여러 번 시도**: 다양한 패스 조합 탐색
- **테마 조합**: 2-3개 테마로 더 정확한 추천

---

## 📈 확장 계획

### 단기 목표
- [ ] 더 많은 상점 및 혜택 데이터 추가
- [ ] 사용자 피드백 수집 시스템
- [ ] 모바일 앱 개발

### 중기 목표
- [ ] 실시간 상점 운영 상태 연동
- [ ] 날씨/계절 기반 추천
- [ ] 다국어 지원

### 장기 목표
- [ ] 다른 지역으로 서비스 확장
- [ ] 블록체인 기반 포인트 시스템
- [ ] AR/VR 관광 가이드 연동

---

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 📞 연락처

- **프로젝트 관리자**: [GitHub Profile](https://github.com/dosiri24)
- **이슈 제보**: [GitHub Issues](https://github.com/dosiri24/local_innovation-inha/issues)
- **브랜치**: `for-server` (서버 배포용)

---

## 🙏 감사의 말

인천 제물포구의 소상공인분들과 관광객 여러분의 상생을 위해 개발된 이 시스템이 지역 경제 활성화에 기여하기를 바랍니다.

**"함께 만들어가는 지속가능한 관광, 제물포GO 패스"**

- **실제 데이터 연동**: DB 연결
- **사용자 시스템**: 회원가입/로그인  
- **패스 관리**: 저장/공유 기능
- **리뷰 시스템**: 피드백 수집
- **지도 연동**: 위치 기반 서비스
- **모바일 앱**: 네이티브 앱 개발

---

## 라이센스
교육용 프로토타입 프로젝트
