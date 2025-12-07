# 배포 체크리스트 (Deployment Checklist)

이 문서는 Refresh Plus 로그인 시스템을 프로덕션 환경에 배포하기 위한 단계별 가이드입니다.

---

## 📦 배포 전 준비

### 1. 보안 키 생성

**중요**: 프로덕션 환경에서는 반드시 강력한 랜덤 키를 사용해야 합니다.

```bash
# ENCRYPTION_MASTER_KEY 생성 (32바이트)
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# ENCRYPTION_SALT 생성 (16바이트)
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(16)).decode())"

# JWT_SECRET_KEY 생성
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

**보안 주의사항**:
- ⚠️ 생성된 키를 안전한 곳에 백업
- ⚠️ 절대 Git에 커밋하지 않음
- ⚠️ 키가 노출되면 즉시 변경 및 모든 사용자 재인증 필요

### 2. 환경 변수 준비

필요한 모든 환경 변수를 정리합니다:

```bash
# Backend (Railway)
ENCRYPTION_MASTER_KEY=<생성한_키>
ENCRYPTION_SALT=<생성한_솔트>
JWT_SECRET_KEY=<생성한_시크릿>
LULU_LALA_USERNAME=<실제_계정>
LULU_LALA_PASSWORD=<실제_비밀번호>
LULU_LALA_RSA_PUBLIC_KEY=<RSA_공개키>
DATABASE_URL=<프로덕션_DB_URL>
CORS_ORIGINS=["https://your-frontend.vercel.app"]
ENVIRONMENT=production
DEBUG=False

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 🚂 Backend 배포 (Railway)

### Phase 1: 데이터베이스 준비

#### 1.1 프로덕션 DB 선택

**옵션 A: Railway PostgreSQL (권장)**
```bash
# Railway 대시보드에서 PostgreSQL 플러그인 추가
# DATABASE_URL 자동 생성됨
```

**옵션 B: Turso (Serverless SQLite)**
```bash
# Turso DB 생성
turso db create refresh-plus-prod

# URL 가져오기
turso db show refresh-plus-prod --url
```

#### 1.2 환경 변수 설정

Railway 대시보드 → 프로젝트 → Variables:

```
ENCRYPTION_MASTER_KEY=<생성한_키>
ENCRYPTION_SALT=<생성한_솔트>
JWT_SECRET_KEY=<생성한_시크릿>
DATABASE_URL=<프로덕션_DB_URL>
CORS_ORIGINS=["https://your-frontend.vercel.app"]
LULU_LALA_USERNAME=<실제_계정>
LULU_LALA_PASSWORD=<실제_비밀번호>
LULU_LALA_RSA_PUBLIC_KEY=<RSA_공개키>
FIREBASE_CREDENTIALS_BASE64=<Base64_인코딩된_credential>
KAKAO_REST_API_KEY=<카카오_키>
OPENAI_API_KEY=<OpenAI_키>
ENVIRONMENT=production
DEBUG=False
PORT=${{PORT}}  # Railway가 자동 할당
```

**Firebase Credentials Base64 인코딩**:
```bash
base64 -i firebase-credentials.json | tr -d '\n'
```

#### 1.3 마이그레이션 실행

**Railway에서 마이그레이션 실행**:

방법 1: Railway CLI
```bash
railway run alembic upgrade head
```

방법 2: 배포 시 자동 실행 (Procfile)
```
release: alembic upgrade head
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Phase 2: 백엔드 배포

#### 2.1 코드 푸시

```bash
cd backend
git add .
git commit -m "feat: 로그인 시스템 구현 및 배포 준비"
git push origin main
```

#### 2.2 Railway 배포 확인

1. Railway 대시보드에서 배포 로그 확인
2. 빌드 성공 확인
3. Health check 확인: `https://your-backend.railway.app/health`

**예상 응답**:
```json
{
  "status": "ok",
  "environment": "production"
}
```

#### 2.3 API 테스트

```bash
# 로그인 테스트
curl -X POST https://your-backend.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "테스트계정",
    "password": "테스트비밀번호"
  }'
```

**체크리스트**:
- [ ] `/health` 엔드포인트 정상 응답
- [ ] `/docs` (Swagger UI) 접근 가능
- [ ] 로그인 API 정상 작동 (8-10초)
- [ ] 사용자 정보 조회 성공
- [ ] 토큰 갱신 성공
- [ ] DB에 사용자 데이터 저장 확인

---

## ▲ Frontend 배포 (Vercel)

### Phase 1: 환경 변수 설정

Vercel 대시보드 → 프로젝트 → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_FIREBASE_API_KEY=<Firebase_API_Key>
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<Firebase_Auth_Domain>
NEXT_PUBLIC_FIREBASE_PROJECT_ID=<Firebase_Project_ID>
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=<Firebase_Storage_Bucket>
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=<Firebase_Sender_ID>
NEXT_PUBLIC_FIREBASE_APP_ID=<Firebase_App_ID>
NEXT_PUBLIC_FIREBASE_VAPID_KEY=<Firebase_VAPID_Key>
```

**중요**: 모든 환경 (Production, Preview, Development)에 동일하게 설정

### Phase 2: 프론트엔드 배포

#### 2.1 코드 푸시

```bash
cd frontend
git add .
git commit -m "feat: 로그인 시스템 UI 구현"
git push origin main
```

#### 2.2 Vercel 자동 배포

- Vercel이 자동으로 빌드 및 배포
- 빌드 로그 확인
- 배포 완료 후 URL 확인

#### 2.3 프로덕션 테스트

**브라우저에서 테스트**:

1. **홈페이지 접속**
   - `https://your-frontend.vercel.app`
   - [ ] 페이지 정상 로드

2. **로그인 플로우**
   - [ ] MY숙소 클릭 → 로그인 페이지 리다이렉트
   - [ ] 웰컴 스크린 표시
   - [ ] "룰루랄라 계정으로 로그인" 버튼 클릭
   - [ ] 자격증명 입력 폼 표시
   - [ ] 로그인 성공 (8-10초)
   - [ ] 원래 페이지로 리다이렉트

3. **MY숙소 페이지**
   - [ ] 사용자 정보 표시
   - [ ] 포인트 정보 표시
   - [ ] 예약 내역 로드

4. **즐겨찾기 페이지**
   - [ ] 찜한 숙소 목록 표시
   - [ ] 찜 제거 기능 작동

5. **토큰 갱신**
   - [ ] 토큰 만료 후 자동 갱신
   - [ ] 재로그인 없이 계속 사용 가능

6. **로그아웃**
   - [ ] 로그아웃 버튼 클릭
   - [ ] 로그인 페이지로 리다이렉트
   - [ ] 보호된 페이지 접근 시 재로그인 필요

---

## 🔄 CORS 설정 업데이트

**중요**: 프론트엔드 배포 후 백엔드 CORS 설정 업데이트 필요

### Railway 환경 변수 업데이트

```
CORS_ORIGINS=["https://your-frontend.vercel.app","https://your-frontend-preview.vercel.app"]
```

**Preview 배포 지원**:
```python
# backend/app/config.py
CORS_ORIGINS = os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')

# Vercel preview 도메인 자동 허용 (선택)
if settings.ENVIRONMENT == "production":
    CORS_ORIGINS.append("https://*.vercel.app")
```

---

## 📊 모니터링 및 로깅

### 1. Sentry 설정 (선택)

**Backend**:
```bash
# Railway 환경 변수
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**Frontend**:
```bash
# Vercel 환경 변수
NEXT_PUBLIC_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### 2. Railway 로그 모니터링

```bash
# 실시간 로그 확인
railway logs --follow

# 특정 서비스 로그
railway logs --service backend
```

**주요 로그 확인 사항**:
- 로그인 시도 및 성공/실패
- 토큰 갱신 요청
- 401/403 에러
- 서버 에러 (500)

### 3. 성능 모니터링

**체크 항목**:
- [ ] 로그인 응답 시간 < 12초
- [ ] 일반 API 응답 시간 < 1초
- [ ] 토큰 갱신 < 100ms
- [ ] 페이지 로드 시간 < 3초

---

## 🔐 보안 체크리스트

### 백엔드 보안

- [ ] DEBUG=False 설정
- [ ] 강력한 JWT_SECRET_KEY 사용
- [ ] 강력한 ENCRYPTION_MASTER_KEY 사용
- [ ] CORS 설정이 프로덕션 도메인만 허용
- [ ] httpOnly 쿠키 설정 (Secure=True)
- [ ] Rate limiting 적용 (로그인: 5회/15분)
- [ ] 계정 잠금 기능 작동 (5회 실패 시)
- [ ] HTTPS 강제 (Railway 자동 제공)
- [ ] 환경 변수가 코드에 하드코딩되지 않음

### 프론트엔드 보안

- [ ] API URL이 HTTPS
- [ ] 민감한 정보가 localStorage에 평문 저장되지 않음
- [ ] XSS 방지 (React 기본 제공)
- [ ] CSRF 방지 (SameSite 쿠키)
- [ ] Content Security Policy 설정 (선택)

### 데이터베이스 보안

- [ ] 비밀번호가 암호화되어 저장됨 (평문 아님)
- [ ] DB 접근이 Railway 내부 네트워크로 제한
- [ ] 정기 백업 설정 (Railway 자동)
- [ ] 민감한 데이터 암호화

---

## 🧪 배포 후 테스트

### 엔드투엔드 테스트

#### 1. 신규 사용자 로그인

```
1. 프로덕션 사이트 접속
2. MY숙소 클릭
3. 로그인 페이지 리다이렉트 확인
4. 새 룰루랄라 계정으로 로그인
5. 사용자 정보 자동 생성 확인
6. DB에 암호화된 비밀번호 저장 확인
```

**체크리스트**:
- [ ] 로그인 성공 (8-10초)
- [ ] 사용자 레코드 생성됨
- [ ] JWT 토큰 발급
- [ ] 세션 쿠키 저장
- [ ] 원래 페이지로 리다이렉트

#### 2. 기존 사용자 재로그인

```
1. 로그아웃
2. 같은 계정으로 다시 로그인
3. 기존 사용자 정보 로드 확인
```

**체크리스트**:
- [ ] 새 레코드 생성되지 않음
- [ ] 기존 포인트/박수 유지
- [ ] 로그인 시간 < 10초 (세션 재사용)

#### 3. 토큰 갱신 플로우

```
1. 로그인 후 1시간 대기
2. 페이지 새로고침
3. 자동 토큰 갱신 확인 (Network 탭)
```

**체크리스트**:
- [ ] 자동 갱신 성공
- [ ] 사용자 경험 중단 없음
- [ ] 새 액세스 토큰 발급

#### 4. 다중 기기 테스트

```
1. PC에서 로그인
2. 모바일에서 같은 계정 로그인
3. 두 기기 모두 정상 작동 확인
```

**체크리스트**:
- [ ] 양쪽 모두 로그인 성공
- [ ] 데이터 동기화
- [ ] 한쪽 로그아웃이 다른쪽에 영향 없음

---

## 🚨 롤백 계획

배포 후 문제 발생 시:

### Backend 롤백

```bash
# Railway CLI
railway rollback

# 또는 Railway 대시보드에서 이전 배포 선택
```

### Frontend 롤백

```bash
# Vercel CLI
vercel rollback

# 또는 Vercel 대시보드에서 이전 배포 선택
```

### Database 롤백

```bash
# 마이그레이션 되돌리기
railway run alembic downgrade -1
```

**주의**: 데이터 손실 위험이 있으므로 신중히 진행

---

## 📈 성공 메트릭

배포 성공 기준:

### 기능적 메트릭

- [ ] 로그인 성공률 > 95%
- [ ] 토큰 갱신 성공률 > 99%
- [ ] API 에러율 < 1%
- [ ] 평균 로그인 시간 < 10초

### 성능 메트릭

- [ ] API 응답 시간 (p95) < 1초
- [ ] 페이지 로드 시간 (p95) < 3초
- [ ] 서버 가동 시간 > 99.5%

### 보안 메트릭

- [ ] 무차별 대입 공격 차단율 100%
- [ ] 취약점 스캔 통과
- [ ] HTTPS 적용 100%

---

## 📝 배포 체크리스트 요약

### 배포 전
- [ ] 보안 키 생성 및 백업
- [ ] 환경 변수 준비
- [ ] 로컬 테스트 완료
- [ ] 코드 리뷰 완료
- [ ] 마이그레이션 SQL 검증

### Backend 배포
- [ ] Railway 프로젝트 생성
- [ ] PostgreSQL 플러그인 추가
- [ ] 환경 변수 설정
- [ ] 마이그레이션 실행
- [ ] 코드 푸시 및 배포
- [ ] Health check 확인
- [ ] API 테스트 완료

### Frontend 배포
- [ ] Vercel 프로젝트 연결
- [ ] 환경 변수 설정
- [ ] 코드 푸시 및 배포
- [ ] 빌드 성공 확인
- [ ] UI 테스트 완료

### 배포 후
- [ ] CORS 설정 업데이트
- [ ] 엔드투엔드 테스트
- [ ] 성능 모니터링 설정
- [ ] 로그 확인
- [ ] 사용자 피드백 수집

### 보안 확인
- [ ] 보안 체크리스트 완료
- [ ] 취약점 스캔
- [ ] 침투 테스트 (선택)
- [ ] 백업 확인

---

## 🎯 다음 단계

배포 완료 후:

1. **사용자 온보딩**
   - 로그인 가이드 작성
   - FAQ 업데이트
   - 공지사항 발행

2. **모니터링**
   - Sentry 알림 설정
   - 성능 대시보드 구축
   - 사용자 행동 분석

3. **최적화**
   - 세션 캐싱 효율 분석
   - 로그인 시간 단축
   - 에러 로그 분석 및 개선

4. **보안 강화**
   - 정기 보안 감사
   - 의심스러운 로그인 감지
   - 2FA 추가 고려

---

**배포 일자**: ___________
**배포자**: ___________
**배포 버전**: ___________
**승인자**: ___________

**배포 결과**: ⬜ 성공 / ⬜ 롤백
**메모**: ___________
