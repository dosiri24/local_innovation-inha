# 제물포GO 패스 - AI 맞춤형 관광 추천 시스템

> 인천 제물포구의 관광 불균형 문제를 해결하는 AI 기반 개인 맞춤형 관광 솔루션

## 프로젝트 개요

"제물포GO 패스"는 관광객이 특정 유명 관광지에만 몰리는 '관광 쏠림' 현상을 해결하고, 잠재력 있는 골목 상권의 소상공인들에게도 기회를 제공하는 혁신적인 추천 시스템입니다.

### 핵심 목표
- **가치 점수(Value Score)**: 관광객의 만족도 최적화
- **상생 점수(Synergy Score)**: 지역 소상공인과의 상생 효과 극대화
- **하이브리드 AI**: 규칙 기반 + LLM 기반 추천 알고리즘

### 패스 시스템
| 패스 타입 | 가격 | 혜택 개수 | 설명 |
|----------|------|-----------|------|
| **라이트 패스** | 7,000원 | 3개 | 기본적인 혜택으로 구성된 가성비 패스 |
| **프리미엄 패스** | 15,000원 | 5개 | 다양한 혜택으로 구성된 풀 패키지 패스 |

---

## 빠른 시작

### 1. API 키 설정

### 2. 프로그램 실행
```bash
python main.py
```

### 3. 패스 타입 선택

#### 라이트 패스 (7,000원)
```
테마: 카페, 조용함
요청사항: 조용한 곳에서 책을 읽으며 커피를 마시고 싶어요
패스 선택: 1 (라이트 패스)
```

#### 프리미엄 패스 (15,000원)
```
테마: 해산물, 바다전망, 전통, 체험
요청사항: 신선한 해산물을 먹고 전통 문화도 체험하고 싶어요
패스 선택: 2 (프리미엄 패스)
```

---

## 설치 및 설정

### 프로젝트 구조
```
local_innovation-inha/
├── .venv/              # Python 가상 환경
├── .env                # 환경 변수 (API 키)
├── .gitignore          # Git 무시 파일
├── requirements.txt    # Python 의존성
├── stores.json         # 상점 데이터
├── benefits.json       # 혜택 데이터
├── main.py            # 메인 애플리케이션
└── README.md          # 프로젝트 문서
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

## 주요 특징

- **개인 맞춤형**: 테마, 요청사항, 예산 종합 고려
- **지역 상생**: 소상공인 우선 추천 알고리즘
- **하이브리드 AI**: 규칙 기반 + LLM의 장점 결합
- **안전성**: API 실패 시 백업 시스템 동작

---

## 사용 팁

- **구체적인 요청**: 상세할수록 정확한 추천
- **패스 타입 선택**: 
  - 라이트 패스: 간단한 나들이, 혼자 여행
  - 프리미엄 패스: 데이트, 가족 여행, 특별한 날
- **여러 번 시도**: 다양한 패스 조합 탐색

---

## 문제 해결

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

---

## 확장 계획

- **실제 데이터 연동**: DB 연결
- **사용자 시스템**: 회원가입/로그인  
- **패스 관리**: 저장/공유 기능
- **리뷰 시스템**: 피드백 수집
- **지도 연동**: 위치 기반 서비스
- **모바일 앱**: 네이티브 앱 개발

---

## 라이센스
교육용 프로토타입 프로젝트
