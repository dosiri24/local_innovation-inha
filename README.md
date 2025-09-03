# 제물포GO 패스 🎫

> AI 기반 동인천 관광 추천 시스템

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Google AI](https://img.shields.io/badge/Google-Gemini%20AI-orange.svg)](https://ai.google.dev/)

## 📁 프로젝트 구조

```
제물포GO/
├── 📋 main.py                 # 애플리케이션 진입점
├── 📋 requirements.txt        # Python 의존성
├── 🔐 .env                   # 환경변수 (API 키 등)
├── 
├── 📂 src/                   # 소스 코드
│   ├── 🐍 models.py          # 데이터 모델 (Store, Benefit, Pass 등)
│   ├── 🐍 services.py        # 비즈니스 로직 (AI 추천, 데이터 처리)
│   ├── 🐍 routes.py          # Flask 라우트 (웹 API)
│   └── 🐍 app.py             # Flask 앱 설정
│   
├── 📂 data/                  # 데이터 파일
│   ├── 📊 stores.json        # 상점 정보
│   ├── 📊 benefits.json      # 혜택 정보
│   └── 📊 themes.json        # 테마 데이터
│   
├── 📂 storage/               # 저장소
│   ├── 📂 saved_passes/      # 생성된 패스 파일들
│   └── 📂 redemptions.json   # 혜택 코드 사용 내역
│   
├── 📂 static/                # 정적 파일
│   ├── 📂 css/               # 스타일시트
│   ├── 📂 js/                # JavaScript
│   └── 📂 images/            # 이미지 파일
│   
├── 📂 templates/             # HTML 템플릿
├── 📂 config/                # 설정 파일
│   ├── ⚙️ app.yaml           # Google Cloud 배포 설정
│   └── ⚙️ gunicorn.conf.py   # Gunicorn 설정
│   
└── 📂 docs/                  # 문서
    ├── 📖 README.md          # 프로젝트 설명서
    ├── 📖 AI_SETUP_GUIDE.md  # AI 설정 가이드
    └── 📖 DEPLOYMENT.md      # 배포 가이드
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd local_innovation-inha

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일에 Google Gemini API 키 설정:

```env
GEMINI_API_KEY=your_google_api_key_here
# 챗봇용 모델 (2.5 flash)
GEMINI_CHATBOT_MODEL=gemini-2.5-flash
# 패스 생성용 모델 (2.5 pro)
GEMINI_PASS_MODEL=gemini-2.5-pro
```

### 3. 애플리케이션 실행

```bash
python main.py
```

서버가 http://localhost:8080 에서 실행됩니다.

## 🏗️ 아키텍처

### 모듈화된 구조

- **models.py**: 데이터 클래스 정의
- **services.py**: AI 추천 엔진 및 비즈니스 로직
- **routes.py**: 웹 API 엔드포인트
- **app.py**: Flask 애플리케이션 설정

### 데이터 관리

- **data/**: JSON 형태의 상점, 혜택, 테마 데이터
- **storage/**: 생성된 패스와 혜택 사용 내역 저장

## 🤖 AI 기능

- **Google Gemini AI**: 사용자 선호도 기반 맞춤 추천
- **스마트 필터링**: 테마별 상점 분류
- **개인화 추천**: 예산, 관심사, 그룹 크기 고려

## 🔧 API 엔드포인트

- `POST /api/generate-pass` - AI 패스 생성
- `GET /api/pass/{id}` - 패스 조회
- `GET /api/user/passes` - 사용자 패스 목록
- `GET /api/themes` - 테마 목록
- `POST /api/benefits/validate` - 혜택 코드 검증
- `POST /api/benefits/redeem` - 혜택 코드 사용 처리

## 📱 주요 기능

1. **AI 기반 추천**: 사용자 선호도를 분석하여 최적의 관광 코스 생성
2. **혜택 코드 사용**: 혜택별 전역 특수코드 입력으로 사용 처리
3. **세션 관리**: 사용자별 패스 관리
4. **반응형 웹**: 모바일과 데스크톱 지원

## 🚀 배포

Google Cloud Platform에 배포 가능:

```bash
gcloud app deploy config/app.yaml
```

자세한 배포 가이드는 `docs/DEPLOYMENT.md`를 참고하세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.
