# 제물포GO 패스 ✨
> AI 가이드와 맞춤형 패스로 동인천을 재발견하는 스마트 관광 플랫폼

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green.svg)](https://flask.palletsprojects.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)](https://ai.google.dev)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](#)

---

## 목차
- [프로젝트 한눈에 보기](#프로젝트-한눈에-보기)
- [왜 제물포GO인가](#왜-제물포go인가)
- [핵심 기능](#핵심-기능)
- [기술 스택](#기술-스택)
- [시스템 구성](#시스템-구성)
- [디렉터리 구조](#디렉터리-구조)
- [데이터 흐름](#데이터-흐름)
- [빠른 시작](#빠른-시작)
- [환경 변수](#환경-변수)
- [실행 & 배포](#실행--배포)
- [주요 API](#주요-api)
- [프런트엔드 화면](#프런트엔드-화면)
- [스토리지 & 백업 전략](#스토리지--백업-전략)
- [추가 문서](#추가-문서)
- [개발 노트](#개발-노트)
- [라이선스](#라이선스)

---

## 프로젝트 한눈에 보기
- **제물포GO 패스**는 인천 동인천 로컬 상권을 위한 맞춤형 관광 패스를 생성하고 관리하는 Flask 기반 웹 애플리케이션입니다.
- **Google Gemini**를 이용해 여행자 대화 내용을 이해하고, 예산·관심사·동행자 정보를 반영한 패스를 자동으로 설계합니다.
- 정적인 JSON 데이터(`data/`)와 실시간 AI 결과를 조합하여, 누구나 쉽게 제물포의 매력을 경험하도록 돕습니다.

## 왜 제물포GO인가
- **현장 중심 설계**: 상권 데이터를 직접 수집해 매장 설명, 위치, 영업시간까지 세밀하게 구성했습니다.
- **안정적인 세션 관리**: `SECRET_KEY` 고정값과 Flask-Session 파일백업으로, 로그인 유지와 패스 재조회가 끊기지 않습니다.
- **다중 백업 전략**: 생성된 패스는 `storage/saved_passes/`에 JSON으로 저장되고, 프로덕션에서는 Google Cloud Datastore에도 동기화합니다.
- **안심 혜택 관리**: 혜택별 전역 특수 코드를 안정적으로 생성해(`services._stable_redemption_code`) 중복 사용을 차단합니다.
- **지도 & 길찾기 연동**: Kakao 지도 API를 사용해 매장 위치를 시각화하고, 도보/차량 길찾기까지 제공합니다.

## 핵심 기능
### 🤖 AI Concierge
- Gemini 기반 대화형 챗봇이 여행자의 관심 테마를 자연스럽게 수집하고 요약합니다 (`src/chatbot.py`).
- 규칙 기반 검증을 곁들여, 부적절한 대화나 미완성 정보를 자동으로 차단합니다.

### 🎫 Pass Studio
- `src/pass_generator.py`가 사용자 선호도, 테마, 패스 타입을 바탕으로 하이브리드 추천 로직을 실행합니다.
- 가치 대비 효과(≥150%)·상생 점수(≥70)와 같은 품질 기준을 자동 점검하며, 부족하면 재생성합니다.

### 🧾 혜택 & 검증
- `POST /api/benefits/validate`로 전역 특수 코드를 검증하고, `POST /api/benefits/redeem`으로 1회성 사용 처리를 기록합니다.
- 사용 이력은 `storage/redemptions.json`에 저장되어 관리자가 쉽게 확인할 수 있습니다.

### 🗺 길찾기 & 위치 서비스
- Kakao Directions API를 호출해 도보/차량 경로를 제공합니다 (`src/routes.py`의 `get_*_directions`).
- 패스 상세 페이지는 모든 제휴 매장을 지도와 카드 UI로 안내합니다.

### 🔐 인증 & 세션
- 이메일/비밀번호 기반의 간단한 로그인·회원가입 플로우가 준비되어 있으며, 세션은 서버 파일 시스템에 안전하게 보관합니다 (`static/js/auth.js`).

## 기술 스택
| 분류 | 사용 기술 |
|------|-----------|
| Backend | Flask, Flask-Session, Flask-CORS |
| AI & NLP | Google Gemini (Flash & Pro), 맞춤형 프롬프트, 안전 필터링 |
| Frontend | Jinja2 템플릿, Vanilla JS, CSS3 |
| Storage | JSON 파일(`data/`, `storage/`), Google Cloud Datastore(선택) |
| Maps & External | Kakao Map/Directions API, dotenv |

## 시스템 구성
- `main.py`: 애플리케이션 진입점, 앱 팩토리 등록과 데이터 초기화 수행.
- `src/app.py`: CORS, 세션, 템플릿 경로를 포함한 Flask 앱 설정.
- `src/routes.py`: 웹 페이지, REST API, AI 챗봇, 길찾기, 패스 조회 등 모든 엔드포인트 관리.
- `src/services.py`: 데이터 로딩, 혜택 코드 검증, 패스 직렬화와 같은 비즈니스 로직.
- `src/pass_generator.py`: Gemini 기반 패스 생성기와 테마 필터링, 품질 보증 로직.
- `src/chatbot.py`: 여행 대화 수집 및 요약 챗봇.
- `src/datastore_service.py`: Google Cloud Datastore에 대한 읽기/쓰기 어댑터.

```
사용자 브라우저
      │   (HTML/JS 요청)
      ▼
Flask Routes (src/routes.py)
      │   ├─ 인증 · 템플릿 렌더링
      │   ├─ AI Pass 생성 요청
      ▼   └─ 패스/혜택 API 응답
서비스 레이어 (services.py, pass_generator.py, chatbot.py)
      │
      ├─ JSON 데이터 로드 (data/)
      ├─ Google Gemini 호출
      └─ 영구 저장 (storage/, Datastore)
```

## 디렉터리 구조
```
local_innovation-inha/
├── main.py                     # Flask 앱 진입점
├── requirements.txt            # Python 의존성
├── config/
│   └── gunicorn.conf.py        # Production WSGI 설정
├── data/
│   ├── stores.json             # 제휴 매장 정보
│   ├── benefits.json           # 혜택 메타데이터
│   └── themes.json             # 테마 분류
├── docs/                       # 추가 가이드
│   ├── AI_SETUP_GUIDE.md
│   ├── PASS_GENERATOR_MODULE.md
│   ├── README.md
│   └── SECRET_KEY_FIX_GUIDE.md
├── src/
│   ├── app.py
│   ├── chatbot.py
│   ├── datastore_service.py
│   ├── models.py
│   ├── pass_generator.py
│   ├── routes.py
│   └── services.py
├── static/
│   ├── images/
│   └── js/
├── templates/
│   ├── auth.html
│   ├── index.html
│   ├── main.html
│   └── ...
├── storage/
│   ├── qr_codes/
│   └── saved_passes/
└── flask_session/              # 개발 환경 세션 디렉터리
```

## 데이터 흐름
1. 사용자가 테마를 선택하고 챗봇과 대화하면 `src/chatbot.py`가 요약과 선호도를 도출합니다.
2. `/api/generate-pass`가 호출되면 `pass_generator.py`가 상점·혜택 데이터를 조합하여 패스를 생성합니다.
3. 생성된 패스는 세션과 파일(`storage/saved_passes/`)에 즉시 저장되고, 프로덕션에서는 Datastore에도 동기화됩니다.
4. 사용자는 `/pass/<pass_id>` 페이지에서 지도, 혜택, 경로 안내를 한 번에 확인할 수 있습니다.
5. 혜택 사용 시, 특수 코드는 `storage/redemptions.json`에 기록되어 중복 사용을 방지합니다.

## 빠른 시작
1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd local_innovation-inha
   ```
2. **가상환경 생성 및 의존성 설치**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. **환경 변수 설정** – `.env` 파일을 생성해 아래 값을 입력합니다.
4. **로컬 실행**
   ```bash
   python main.py
   ```
   서버는 기본적으로 `http://localhost:8080`에서 동작합니다.

## 환경 변수
| 변수 | 필수 | 설명 | 기본값 |
|------|------|------|--------|
| `GEMINI_API_KEY` | ✅ | Gemini API 호출용 키 | 없음 |
| `GEMINI_CHATBOT_MODEL` | ⬜️ | 챗봇 모델 이름 | `gemini-2.5-flash` |
| `GEMINI_PASS_MODEL` | ⬜️ | 패스 생성 모델 이름 | `gemini-2.5-pro` |
| `KAKAO_API_KEY` | ⬜️ | Kakao 지도/길찾기용 REST 키 | 샘플 키 내장 |
| `SECRET_KEY` | ✅(배포) | Flask 세션 서명 키 | 개발용 기본값 |
| `PORT` | ⬜️ | 서비스 포트 | `8080` |

## 실행 & 배포
- **로컬 개발**: `python main.py`
- **Gunicorn (prod-like)**: `gunicorn -c config/gunicorn.conf.py main:app`
- **Google Cloud Datastore 연동**: `GOOGLE_CLOUD_PROJECT` 및 자격 증명을 설정하면 `src/datastore_service.py`가 자동으로 활성화됩니다.

## 주요 API
| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/health`, `/_ah/health` | GET | 애플리케이션 상태 확인 |
| `/api/login`, `/api/signup`, `/api/logout`, `/api/session-check` | POST/GET | 이메일 기반 인증 & 세션 관리 |
| `/api/themes`, `/api/pass-types`, `/api/stores` | GET | 프런트엔드용 메타데이터 제공 |
| `/api/chat/start`, `/api/chat/message`, `/api/chat/complete`, `/api/chat/reset` | POST | Gemini 챗봇 대화 제어 |
| `/api/generate-pass` | POST | 사용자 선호도 기반 맞춤 패스 생성 |
| `/api/pass/<pass_id>` | GET | 저장된 패스 상세 조회 |
| `/api/user/passes` | GET | 로그인한 사용자의 패스 목록 |
| `/api/benefits/validate`, `/api/benefits/redeem` | POST | 혜택 특수 코드 검증/사용 처리 |
| `/api/directions`, `/api/directions/car`, `/api/directions/walking` | POST | Kakao 길찾기 API 프록시 |

## 프런트엔드 화면
- `templates/index.html`: 비로그인 사용자를 위한 소개 및 인증 페이지.
- `templates/main.html`: 로그인 이후 메인 허브, 테마별 페이지와 패스 생성기로 연결.
- `templates/pass_detail.html`: 생성된 패스 상세, 지도, 혜택, 길찾기 버튼 제공.
- `templates/help.html` 등: 사용자 안내 및 테마별 소개 페이지 모음.
- `static/js/auth.js`: 로그인/로그아웃/회원가입 요청을 처리하는 공용 스크립트.

## 스토리지 & 백업 전략
- `storage/saved_passes/`: 개별 패스 JSON 스냅샷을 보관.
- `storage/redemptions.json`: 혜택 코드 사용 이력.
- `storage/qr_codes/`: 추후 QR 아티팩트 보관용 디렉터리.
- `flask_session/`: 개발 환경에서 Flask-Session이 생성하는 서버 세션 파일.
- Google Cloud 환경에서는 추가로 Datastore에 패스 데이터를 복제하여 장애에 대비합니다.

## 추가 문서
- `docs/AI_SETUP_GUIDE.md`: Gemini API 키 설정 및 모델 구성 가이드.
- `docs/PASS_GENERATOR_MODULE.md`: 패스 생성 로직 상세 설명.
- `docs/SECRET_KEY_FIX_GUIDE.md`: 세션 안정화를 위한 SECRET_KEY 가이드.
- `check_secret_key.py`: 배포 전 SECRET_KEY 누락을 점검하는 유틸리티.

## 개발 노트
- 현재 자동화된 테스트는 포함되어 있지 않습니다. `pytest`를 도입해 서비스 레이어(`src/services.py`)와 API 엔드포인트 검증을 권장합니다.
- 새로운 데이터는 `data/` 디렉터리의 JSON 스키마에 맞춰 추가하고, 변경 사항이 있다면 패스 생성 품질 기준을 함께 검토하세요.
- 민감 정보(`.env`, `storage/`)는 Git에 커밋하지 않도록 주의합니다.

## 라이선스
- 이 저장소에는 아직 공식 `LICENSE` 파일이 포함되어 있지 않습니다. 사용 전 프로젝트 소유자와 라이선스 정책을 확인하세요.
