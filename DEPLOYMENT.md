# 제물포GO 패스 - 웹 애플리케이션 배포 가이드

## 🌐 웹 애플리케이션 변경사항

기존 터미널 기반 애플리케이션을 Flask 웹 애플리케이션으로 변환했습니다.

### 새로 추가된 파일들
- `app.py` - Flask 웹 애플리케이션 메인 파일
- `templates/index.html` - 웹 인터페이스 HTML 템플릿
- `app.yaml` - Google Cloud App Engine 배포 설정
- `gunicorn.conf.py` - Gunicorn 서버 설정
- `.env.example` - 환경 변수 템플릿

## 🚀 Google Cloud 배포 방법

### 1. 사전 준비
```bash
# Google Cloud SDK 설치 (Mac)
brew install --cask google-cloud-sdk

# 로그인
gcloud auth login

# 프로젝트 설정 (YOUR_PROJECT_ID를 실제 프로젝트 ID로 변경)
gcloud config set project YOUR_PROJECT_ID

# App Engine 활성화
gcloud app create --region=asia-northeast3
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 실제 Gemini API 키 입력
# GEMINI_API_KEY=your_actual_api_key_here
```

### 3. 로컬 테스트
```bash
# 가상환경 활성화 (이미 설정되어 있음)
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Flask 애플리케이션 실행
python app.py
```

브라우저에서 `http://localhost:5000` 접속하여 테스트

### 4. Google Cloud 배포
```bash
# app.yaml에서 환경 변수 설정
# GEMINI_API_KEY를 실제 API 키로 변경

# 배포 실행
gcloud app deploy

# 브라우저에서 열기
gcloud app browse
```

## 🔧 주요 API 엔드포인트

- `GET /` - 메인 웹 페이지
- `GET /api/themes` - 사용 가능한 테마 목록
- `GET /api/pass-types` - 패스 타입 정보
- `POST /api/generate-pass` - 패스 생성 API
- `GET /health` - 헬스 체크

## 📱 웹 인터페이스 기능

1. **테마 선택**: 클릭으로 여러 테마 선택 가능
2. **자유 요청**: 텍스트로 원하는 것 설명
3. **패스 타입**: 라이트/프리미엄 패스 선택
4. **결과 표시**: 생성된 패스의 상세 정보와 혜택 목록
5. **반응형 디자인**: 모바일에서도 사용 가능

## 🔒 보안 고려사항

- API 키는 환경 변수로 관리
- CORS 설정으로 안전한 요청만 허용
- 입력 검증으로 잘못된 요청 차단

## 💰 비용 예상 (Google Cloud)

- **App Engine Standard**: 
  - 무료 할당량: 월 28시간
  - 유료: 시간당 약 $0.05
- **API 호출**: Gemini API 사용량에 따라

## 📊 모니터링

- Google Cloud Console에서 실시간 모니터링
- 로그 확인: `gcloud app logs tail -s default`
- 헬스 체크: `/health` 엔드포인트

## 🔄 업데이트 방법

코드 변경 후:
```bash
gcloud app deploy
```

## 📞 문제 해결

1. **배포 실패**: `gcloud app logs tail -s default`로 로그 확인
2. **API 오류**: Gemini API 키 확인
3. **데이터 로드 오류**: `stores.json`, `benefits.json` 파일 확인
