# 🚨 중요: 패스 유실 방지 - SECRET_KEY 관리 가이드

## 문제 상황
데모 버전에서 패스를 생성한 후 로그아웃하고 다시 로그인하면 패스가 사라지는 문제가 발생했습니다.

## 근본 원인
**SECRET_KEY 무작위 생성 문제**
- 기존 코드에서 `app.config['SECRET_KEY'] = secrets.token_hex(16)`로 앱 시작시마다 새로운 SECRET_KEY 생성
- Flask 세션은 SECRET_KEY로 암호화되므로, 키가 변경되면 기존 세션 데이터가 모두 무효화됨
- 결과적으로 사용자의 로그인 정보와 패스 정보가 모두 사라짐

## 해결 방법

### 1. SECRET_KEY 고정화 ✅
```python
# app.py - 수정 전 (문제 코드)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # 매번 변경됨!

# app.py - 수정 후 (해결 코드)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    secret_key = 'jemulpogo-demo-secret-key-fixed-2024-do-not-change-this-value-or-sessions-will-be-lost'
app.config['SECRET_KEY'] = secret_key  # 고정된 키 사용
```

### 2. 환경 변수 설정 ✅
```bash
# .env 파일
SECRET_KEY="jemulpogo-production-secret-key-fixed-2024-do-not-change-this-value-sessions-will-break"
```

### 3. 영구 세션 설정 강화 ✅
```python
# 모든 세션 저장 시점에서 영구 세션 설정
session.permanent = True
app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24*30  # 30일
```

### 4. 프로덕션 환경 설정 ✅
```yaml
# app.yaml
env_variables:
  SECRET_KEY: "jemulpogo-production-secret-key-fixed-2024-do-not-change-this-value-sessions-will-break"
```

## 주의사항

### ⚠️ 절대 해서는 안 되는 것
1. **SECRET_KEY 변경 금지**: 한 번 설정된 SECRET_KEY는 절대 변경하면 안 됩니다
2. **랜덤 키 생성 금지**: `secrets.token_hex()` 등으로 런타임에 키 생성 금지
3. **환경별 키 다름**: 개발/스테이징/프로덕션에서 각각 다른 키 사용 금지

### ✅ 반드시 해야 하는 것
1. **키 고정화**: 모든 환경에서 동일한 고정 SECRET_KEY 사용
2. **환경 변수 설정**: .env, app.yaml에 SECRET_KEY 명시적 설정
3. **영구 세션**: `session.permanent = True` 설정
4. **정기 확인**: `python check_secret_key.py` 실행하여 설정 검증

## 검증 방법

### SECRET_KEY 설정 확인
```bash
python check_secret_key.py
```

### 세션 유지 테스트
1. 로그인 후 패스 생성
2. 브라우저 재시작 (세션 쿠키 테스트)
3. 서버 재시작 (SECRET_KEY 고정 테스트)
4. 로그아웃 후 재로그인 (패스 복원 테스트)

## 추가 보안 강화

### 다중 저장소 백업
```python
# 패스 저장 시 3단계 백업
1. 세션 저장 (즉시 접근)
2. 쿠키 저장 (브라우저 재시작 대응)
3. Datastore/파일 저장 (영구 보관)
```

### 복원 로직 강화
```python
# 로그인 시 모든 저장소에서 패스 복원
1. 세션에서 확인
2. 쿠키에서 복원
3. Datastore에서 복원
4. 결과 병합 및 중복 제거
```

## 결론
SECRET_KEY 고정화만으로도 대부분의 패스 유실 문제가 해결됩니다. 이는 가장 근본적이고 중요한 수정사항입니다.

---
**작성일**: 2024-01-07  
**최종 업데이트**: 2024-01-07  
**중요도**: 🚨 CRITICAL
