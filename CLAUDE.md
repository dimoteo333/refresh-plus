# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소의 코드를 작업할 때 참고하는 가이드입니다.

---

## 프로젝트 개요

**Refresh Plus**는 신한은행 임직원을 위한 연성소(호텔/펜션/리조트) 예약 플랫폼입니다. 포인트 기반 티켓팅 시스템을 사용하여 공정하게 숙소를 배정합니다.

**핵심 비즈니스 로직**:
- 사용자가 예약 신청 시 PENDING 상태로 저장
- 매일 자정(00:00 KST) `daily_ticketing` 배치 작업이 Railway Cron으로 실행
- 각 숙소/날짜별로 PENDING 예약을 사용자 점수(`winning_score_at_time`) 순으로 정렬
- 최고 점수자만 WON으로 변경하고 포인트 차감, 나머지는 LOST로 변경
- WON 상태일 때만 포인트가 차감됨 (PENDING/LOST는 차감 안됨)

**크롤링 시스템**:
- 기존 웹사이트(lulu-lala.zzzmobile.co.kr)에서 숙소 정보, FAQ, 실시간 신청 현황을 Playwright로 크롤링
- 크롤링한 데이터를 DB에 저장하여 사용자에게 제공

---

## 개발 커맨드

### Backend (FastAPI + Python)
```bash
# 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 단일 테스트 모듈 실행
pytest tests/test_bookings.py -v

# 커버리지 포함 전체 테스트
pytest --cov=app

# 데이터베이스 마이그레이션
alembic revision --autogenerate -m "description"
alembic upgrade head

# 배치 작업 로컬 테스트
python backend/batch/run_daily_ticketing.py
python backend/batch/run_accommodation_crawler.py
python backend/batch/run_faq_crawler.py
python backend/batch/run_today_accommodation_realtime.py
```

### Frontend (Next.js 15 + TypeScript)
```bash
# 설정
cd frontend
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
npm start

# 린트
npm run lint
```

### Railway 배포
```bash
# Railway CLI 설치
npm i -g @railway/cli

# 로그인 및 초기화
railway login
railway init

# Backend 배포
cd backend
railway up

# 로그 확인
railway logs

# Railway 대시보드 열기
railway open
```

---

## 아키텍처 & 핵심 개념

### Backend 아키텍처 (3계층)

1. **Routes 계층** (`backend/app/routes/`): API 엔드포인트, 요청 검증
2. **Services 계층** (`backend/app/services/`): 비즈니스 로직, 오케스트레이션
3. **Models 계층** (`backend/app/models/`): SQLAlchemy ORM 모델

**패턴**: Routes는 Services를 호출하고, Services는 Models + Integrations를 조율합니다. 절대 서비스 계층을 건너뛰지 마세요.

### 예약 상태 머신

```
사용자가 예약 생성 → PENDING
                         ↓
매일 00:00 배치 작업 실행 → WON (최고 점수) 또는 LOST
                         ↓
WON 예약 → COMPLETED (체크아웃 날짜 이후)
```

**중요**: 예약은 PENDING 상태로 시작합니다. 포인트는 즉시 차감되지 않으며, 배치 작업이 상태를 WON으로 변경할 때만 차감됩니다.

### 인증 흐름

- Frontend: Clerk 인증 → JWT 토큰
- Backend: `app/dependencies.py::get_current_user()`가 `app/integrations/clerk.py::verify_token()`을 통해 JWT 검증
- 모든 보호된 라우트는 `Depends(get_current_user)` 사용

### 알림 시스템

이중 채널 알림:
- **Android**: Firebase Cloud Messaging (`app/integrations/firebase_service.py`)
- **iOS/PC**: Kakao Talk Channel API (`app/integrations/kakao_service.py`)

서비스가 알림 통합을 직접 호출합니다. 현재 이벤트 큐 시스템은 구현되지 않았습니다.

### Frontend 데이터 흐름

```
Component → Custom Hook (useAccommodations, useBookings, useWishlist)
                ↓
        React Query (캐싱)
                ↓
        API Client (lib/api.ts)
                ↓
        Backend API
```

**패턴**: 컴포넌트는 API를 직접 호출하지 않습니다. 항상 React Query로 캐싱 및 상태 관리를 래핑하는 커스텀 훅을 사용하세요.

### 배치 작업 (Railway Cron)

`backend/app/batch/`에 위치:
- `daily_ticketing.py`: 매일 00:00 KST (15:00 UTC) 실행, PENDING 예약 처리
- `accommodation_crawler.py`: 매일 01:00 KST 실행, 전체 숙소 정보 크롤링
- `faq_crawler.py`: 매일 02:00 KST 실행, FAQ 정보 크롤링
- `today_accommodation_realtime.py`: 매시간 실행, 오늘자 실시간 신청 현황 갱신

**배포**: Railway Cron 서비스가 독립 실행 스크립트를 트리거합니다:
- `backend/batch/run_daily_ticketing.py`
- `backend/batch/run_accommodation_crawler.py`
- `backend/batch/run_faq_crawler.py`
- `backend/batch/run_today_accommodation_realtime.py`

이 스크립트들은 배치 작업 함수를 import하여 실행합니다. Railway 대시보드 또는 `railway.toml`에서 cron 스케줄을 설정하세요.

### 크롤링 시스템

**Playwright 기반 자동화 크롤러**:

1. **숙소 정보 크롤링** (`accommodation_crawler.py`):
   - lulu-lala 웹사이트 로그인 (RSA 암호화)
   - shbrefresh 페이지로 SSO 이동
   - 모든 숙소의 기본 정보, 이미지, 날짜별 신청 점수/인원 크롤링
   - Accommodation, AccommodationDate 테이블에 저장

2. **FAQ 크롤링** (`faq_crawler.py`):
   - FAQ 페이지 접속
   - 카테고리별 FAQ 질문/답변 크롤링
   - FAQ 테이블에 저장

3. **실시간 현황 갱신** (`today_accommodation_realtime.py`):
   - 최초 실행 시: 신청 가능한 모든 날짜 크롤링
   - 반복 실행 시: 기존 데이터만 실시간 업데이트
   - TodayAccommodation 테이블에 저장

**크롤링 인증**:
- `LULU_LALA_USERNAME`, `LULU_LALA_PASSWORD`: 로그인 정보
- `LULU_LALA_RSA_PUBLIC_KEY`: 비밀번호 암호화용 RSA 공개키

---

## 배포 아키텍처

```
Railway Project
├── Service: Backend API
│   ├── Start: uvicorn app.main:app
│   └── Port: $PORT (자동 할당)
├── Service: Daily Ticketing Cron
│   ├── Schedule: 0 15 * * * (00:00 KST)
│   └── Command: python batch/run_daily_ticketing.py
├── Service: Accommodation Crawler Cron
│   ├── Schedule: 0 16 * * * (01:00 KST)
│   └── Command: python batch/run_accommodation_crawler.py
├── Service: FAQ Crawler Cron
│   ├── Schedule: 0 17 * * * (02:00 KST)
│   └── Command: python batch/run_faq_crawler.py
└── Service: Today Accommodation Realtime Cron
    ├── Schedule: 0 * * * * (매시간)
    └── Command: python batch/run_today_accommodation_realtime.py

Vercel Project
└── Frontend (Next.js 15)
```

### Railway 설정 파일

- `backend/railway.json`: 메인 API 서비스 설정
- `backend/Procfile`: Railway용 프로세스 정의
- `backend/nixpacks.toml`: 빌드 설정
- `backend/runtime.txt`: Python 버전 명세
- `backend/batch/railway_*.json`: Cron 작업 설정

---

## 파일 구조 패턴

### Backend 신규 기능 추가

1. `backend/app/models/feature.py`에 모델 생성
2. `backend/app/schemas/feature.py`에 스키마 생성 (Pydantic 검증용)
3. `backend/app/services/feature_service.py`에 서비스 생성 (비즈니스 로직)
4. `backend/app/routes/feature.py`에 라우트 생성 (API 엔드포인트)
5. `backend/app/main.py`에 라우터 등록

### Frontend 신규 기능 추가

1. `frontend/src/types/feature.ts`에 타입 정의
2. `frontend/src/lib/api.ts`에 API 함수 생성
3. `frontend/src/hooks/useFeature.ts`에 커스텀 훅 생성
4. `frontend/src/components/feature/`에 컴포넌트 생성
5. `frontend/src/app/(protected)/feature/page.tsx`에 페이지 생성

### 배치 작업 추가

1. `backend/app/batch/new_job.py`에 작업 함수 생성
2. `backend/batch/run_new_job.py`에 독립 실행 스크립트 생성
3. `backend/batch/railway_new_job.json`에 Railway 설정 생성
4. Railway에서 새 Cron 서비스로 배포

---

## 환경 설정

### Backend 필수 변수 (.env 또는 Railway Variables)

- `DATABASE_URL`: PostgreSQL/Turso 연결 문자열
- `CLERK_SECRET_KEY`: JWT 검증용
- `FIREBASE_CREDENTIALS_PATH`: 푸시 알림용 (또는 FIREBASE_CREDENTIALS_BASE64 사용)
- `KAKAO_REST_API_KEY`: 카카오톡 통합용
- `LULU_LALA_USERNAME`: 크롤링 로그인 사용자명
- `LULU_LALA_PASSWORD`: 크롤링 로그인 비밀번호
- `LULU_LALA_RSA_PUBLIC_KEY`: 비밀번호 암호화용 RSA 공개키
- `PORT`: Railway가 자동 할당 (커맨드에서 $PORT 사용)
- `ENVIRONMENT`: production/development
- `CORS_ORIGINS`: 허용된 프론트엔드 오리진 JSON 배열

### Frontend 필수 변수 (.env.local 또는 Vercel Environment)

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk 공개 키
- `NEXT_PUBLIC_API_URL`: Backend API URL (Railway URL)
- `NEXT_PUBLIC_FIREBASE_*`: FCM용 Firebase 설정

**참고**: `NEXT_PUBLIC_` 접두사가 붙은 변수는 브라우저에 노출됩니다.

### Railway 전용 환경 설정

Railway는 자동으로 `PORT` 변수를 주입합니다. 시작 커맨드에서 항상 `$PORT`를 사용하세요:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Cron 작업의 경우, 데이터베이스 연결 및 API 접근을 보장하기 위해 메인 서비스의 모든 환경 변수를 복사하세요.

---

## 데이터베이스 스키마 참고사항

### 주요 테이블

- **Users**: `current_points`는 사용 가능한 포인트를 추적, `last_point_recovery`는 회복 타이밍용
- **Bookings**: `winning_score_at_time`은 예약 생성 시점의 사용자 점수를 저장 (배치 작업 정렬용)
- **Accommodations**: `available_rooms`는 수동 관리, 자동 차감 안됨
- **AccommodationDate**: 크롤링한 날짜별 숙소 정보 (점수, 신청 인원, 상태)
- **TodayAccommodation**: 오늘자 실시간 신청 현황 (시간당 갱신)
- **FAQ**: 크롤링한 FAQ 질문/답변 (RAG 챗봇용)
- **Wishlist**: `notify_when_bookable` 플래그는 사용자 점수 >= 평균 당첨 점수일 때 알림 트리거

---

## 중요 통합 포인트

### Clerk 인증

`backend/app/integrations/clerk.py::verify_token()`의 플레이스홀더 구현은 현재 목 사용자 ID를 반환합니다. 프로덕션에서는 실제 Clerk SDK 구현으로 교체하세요.

### Firebase Admin SDK

Firebase 인증 정보가 필요합니다. Railway용 두 가지 옵션:
1. 인증 정보를 Base64로 인코딩하여 `FIREBASE_CREDENTIALS_BASE64` 환경 변수 사용
2. Railway Volumes를 사용하여 인증 파일 마운트

`FirebaseService.__init__()`에서 한 번만 초기화하세요. 다중 초기화 시도는 실패합니다.

### Kakao Talk API

bearer 토큰 인증과 함께 REST API를 사용합니다. 메시지 형식은 Kakao의 템플릿 객체 구조를 따릅니다.

### Playwright 크롤링

- 로그인 시 RSA 공개키로 비밀번호 암호화
- `headless=True` 모드로 실행 (프로덕션)
- `data-role="roomInfo"`, `data-rblockdate` 등의 data 속성으로 정보 추출
- 페이지 로딩 대기: `wait_for_timeout()`, `wait_for_load_state("networkidle")`

---

## 테스트 접근법

- Backend 테스트는 async 지원과 함께 pytest 사용
- API 엔드포인트 테스트에는 httpx의 `AsyncClient` 사용
- 테스트에서 외부 서비스(Firebase, Kakao, Playwright) 모킹
- Railway cron에 배포하기 전에 배치 작업을 로컬에서 테스트

---

## 일반적인 패턴

### 비동기 데이터베이스 쿼리

SQLAlchemy와 함께 항상 async/await 사용. 예시:
```python
result = await db.execute(select(Model).where(Model.field == value))
item = result.scalar_one_or_none()
```

### Routes의 오류 처리

```python
from fastapi import HTTPException

if not resource:
    raise HTTPException(status_code=404, detail="Resource not found")
```

### React Query 캐시 무효화

```typescript
queryClient.invalidateQueries({ queryKey: ["resource-key"] });
```

### Railway 포트 바인딩

항상 `0.0.0.0`에 바인딩하고 Railway의 `$PORT` 사용:
```python
# ✅ 올바름
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# ❌ 잘못됨 (하드코딩된 포트)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 크롤링 시 RSA 암호화

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64

def encrypt_rsa(plaintext: str, public_key_pem: str) -> str:
    key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(plaintext.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')
```

---

## 배포 워크플로우

### Backend를 Railway에 배포

1. 코드를 커밋하고 GitHub에 푸시
2. Railway가 푸시 시 자동 배포 (연결된 경우)
3. 또는 수동으로: `backend/` 디렉토리에서 `railway up`
4. 배포 확인: `railway logs`
5. 헬스 체크: `curl https://your-app.railway.app/health`

### 배치 작업을 Railway에 배포

1. Railway 프로젝트에서 새 서비스 생성
2. 동일한 GitHub 저장소 선택
3. 루트 디렉토리 설정: `backend`
4. 서비스 유형 설정: Cron
5. 스케줄 설정 (crontab 문법)
6. 커맨드 설정: `python batch/run_*.py`
7. 메인 서비스에서 환경 변수 복사

### Frontend를 Vercel에 배포

1. GitHub 저장소를 Vercel에 연결
2. 루트 디렉토리로 `frontend` 선택
3. Vercel 대시보드에서 환경 변수 설정
4. main 브랜치에 푸시 시 Vercel이 자동 배포
5. PR 생성 시 미리보기 배포

---

## API 문서

프로덕션에서 `https://your-app.railway.app/docs`에서 대화형 API 문서 제공 (FastAPI가 자동 생성하는 Swagger UI).

로컬 개발: `http://localhost:8000/docs`

---

## 문제 해결

### Railway 빌드 실패

- `railway logs --deployment` 확인
- `requirements.txt`에 모든 의존성이 있는지 확인
- `runtime.txt`에 올바른 Python 버전이 명시되어 있는지 확인

### Cron 작업이 실행되지 않음

- cron 스케줄 문법 확인 (crontab.guru 사용)
- cron 서비스에 환경 변수가 설정되어 있는지 확인
- 로그 확인: `railway logs --service <cron-service-name>`

### 데이터베이스 연결 문제

- `DATABASE_URL`이 올바른 async 드라이버를 사용하는지 확인:
  - PostgreSQL: `postgresql+asyncpg://...`
  - Turso: `libsql://...`
- 마이그레이션 실행: `railway run alembic upgrade head`

### 포트 바인딩 오류

- Railway 커맨드에서 항상 `$PORT` 사용
- 프로덕션 설정에서 포트 8000을 하드코딩하지 마세요
- Railway가 랜덤 포트를 할당하므로 앱이 해당 포트에 바인딩해야 합니다

### 크롤링 실패

- `LULU_LALA_USERNAME`, `LULU_LALA_PASSWORD` 확인
- `LULU_LALA_RSA_PUBLIC_KEY` 형식 확인 (`\n` 문자가 실제 줄바꿈으로 처리되는지)
- Playwright 브라우저 설치: `playwright install chromium`
- Railway 대시보드 → Logs에서 로그 확인

---

## 추가 참고사항

### Next.js 15 + React 19 업그레이드

- App Router 사용 (Pages Router 아님)
- Server Components 기본값
- `use client` 지시어로 Client Components 명시
- React Query는 Client Components에서만 사용

### 데이터 모델 관계

```
User (1) ─── (N) Booking
User (1) ─── (N) Wishlist

Accommodation (1) ─── (N) AccommodationDate
Accommodation (1) ─── (N) TodayAccommodation
Accommodation (1) ─── (N) Booking
Accommodation (1) ─── (N) Wishlist

FAQ: 독립 테이블 (관계 없음)
```

### 포인트 시스템

- 초기 포인트: `MAX_POINTS` (기본값: 100)
- 예약당 차감: `POINTS_PER_BOOKING` (기본값: 10)
- 회복 주기: `POINTS_RECOVERY_HOURS` (기본값: 24시간)
- WON 상태일 때만 차감, PENDING/LOST는 차감 안됨

---

**마지막 업데이트**: 2024년 12월
