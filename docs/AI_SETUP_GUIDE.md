# 🔧 제물포GO 패스 - AI 기능 설정 완료 가이드

## ✅ 현재 상태
- ✅ `.env` 파일 생성 완료
- ✅ `.env.example` 파일 생성 완료  
- ✅ `.gitignore` 파일 확인 완료
- ✅ 필요한 Python 패키지 설치됨 (`requirements.txt`)

## 🚀 AI 기능 활성화 단계

### 1단계: Google Gemini API 키 발급
1. https://makersuite.google.com/app/apikey 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. API 키 복사

### 2단계: .env 파일 설정
```bash
# .env 파일 열기
code .env

# 다음 줄 수정:
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3단계: 테스트 실행
```bash
# 터미널에서 AI 기능 테스트
python main.py

# 또는 웹 서버로 테스트
python app.py
```

## 🔍 현재 AI 기능 구현 상태

### ✅ 구현된 기능
- **하이브리드 추천 시스템**: 규칙 기반 + AI 기반
- **Gemini AI 연동**: 자연어 요청사항 이해
- **백업 시스템**: API 실패 시 규칙 기반 추천
- **패스 생성**: 사용자 맞춤형 관광 패스

### 🤖 AI 활용 부분
```python
# main.py의 generate_pass() 함수에서:
1. 규칙 기반으로 상위 20개 후보 선별
2. Gemini AI로 사용자 요청사항 분석
3. AI가 최적 혜택 조합 추천
4. 검증 후 최종 패스 생성
```

## 📁 관련 파일 정리

### 환경 설정 파일
- `.env` - 실제 환경 변수 (Git 업로드 금지)
- `.env.example` - 환경 변수 템플릿
- `.gitignore` - Git 제외 파일 목록

### AI 기능 구현 파일
- `main.py` - AI 추천 엔진 메인 로직
- `app.py` - Flask 웹 서버 (API 엔드포인트)
- `requirements.txt` - 필요한 Python 패키지

### 데이터 파일
- `stores.json` - 상점 정보
- `benefits.json` - 혜택 정보
- `themes.json` - 테마 정보

## ⚡ 빠른 테스트

### 방법 1: 터미널 모드
```bash
python main.py
```

### 방법 2: 웹 서버 모드
```bash
python app.py
# 브라우저에서 http://localhost:8080 접속
```

### 방법 3: API 테스트
```bash
curl -X POST http://localhost:8080/api/generate-pass \
  -H "Content-Type: application/json" \
  -d '{
    "themes": ["카페", "조용함"],
    "request": "조용한 곳에서 책을 읽고 싶어요",
    "pass_type": "light"
  }'
```

## 🔧 문제 해결

### AI 기능이 작동하지 않는 경우
1. **API 키 확인**: `.env` 파일의 `GEMINI_API_KEY` 값
2. **네트워크 확인**: 인터넷 연결 상태
3. **할당량 확인**: Google AI Studio 할당량
4. **백업 동작**: AI 실패 시 규칙 기반 추천 동작

### 로그 확인
```bash
# 터미널에서 실행하면 다음과 같은 로그 확인 가능:
[AI] Gemini 모델 'gemini-1.5-flash' 연결 성공!
[경고] Gemini API 키가 설정되지 않았습니다. 규칙 기반 추천만 사용합니다.
```

## 🎯 AI 기능 특징

### 장점
- **자연어 이해**: "조용한 곳에서 책을 읽고 싶어요" 같은 요청 분석
- **맥락적 추천**: 패스 타입과 예산을 고려한 최적화
- **안정성**: API 실패 시 백업 시스템 동작

### 한계
- **API 의존성**: 인터넷 연결 필요
- **할당량 제한**: 무료 계정 시 월 60회 제한
- **응답 시간**: AI 처리로 인한 약간의 지연

## 📈 다음 단계 확장 가능 기능

### 즉시 추가 가능
- [ ] 사용자 피드백 학습
- [ ] 날씨 정보 연동
- [ ] 실시간 상점 운영 상태
- [ ] 다국어 지원

### 향후 확장 계획
- [ ] 이미지 AI (상점 사진 분석)
- [ ] 음성 인식 (요청사항 음성 입력)
- [ ] 예측 AI (인기 상점 예측)
- [ ] 챗봇 시스템

## 💡 추천 사용법

### 효과적인 요청사항 작성
- ❌ "맛있는 것": 너무 일반적
- ✅ "신선한 해산물을 먹고 바다를 보고 싶어요": 구체적

### 테마 조합 추천
- **데이트**: 카페 + 바다전망 + 조용함
- **가족여행**: 전통 + 체험 + 해산물
- **혼자여행**: 조용함 + 책 + 카페

---

## 📞 지원 및 문의

- **설정 문제**: GitHub Issues 등록
- **AI API 문제**: Google AI Studio 문서 참조
- **기능 개선**: Pull Request 환영

**🎉 설정 완료! 이제 AI 기반 맞춤형 관광 추천을 경험해보세요!**
