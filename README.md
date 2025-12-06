# 🏨 Refresh Plus - 신한은행 임직원 숙소 예약 플랫폼

**임직원들을 위한 스마트한 연성소(호텔/펜션/리조트) 예약 시스템**

포인트 기반 티켓팅, 실시간 알림, AI 챗봇을 통합한 웹/모바일 플랫폼

---

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [배포 가이드](#배포-가이드)
- [개발 가이드](#개발-가이드)

---

## 프로젝트 개요

### 🎯 배경

기존 신한은행 임직원용 연성소(호텔/펜션/리조트) 예약 시스템의 불편함을 개선하여, 다음을 제공합니다:

- **공정한 티켓팅 시스템**: 포인트 기반으로 매일 자정(00:00 KST) 배치 작업을 통해 최고 점수자에게 자동 배정
- **자동화된 크롤링**: 기존 웹사이트에서 숙소 정보, FAQ, 실시간 신청 현황 자동 수집
- **실시간 알림**: 개인화된 푸시 알림으로 예약 기회를 놓치지 않음
- **AI 챗봇**: FAQ 기반 RAG 챗봇으로 즉시 답변
- **모던 UI/UX**: Next.js 15 + React 19 기반 반응형 웹 인터페이스

### 🌟 핵심 비즈니스 로직

```
사용자 예약 신청 → PENDING 상태
           ↓
매일 00:00 (KST) 배치 작업 실행
           ↓
PENDING 예약을 점수 순으로 정렬
           ↓
최고 점수자 → WON (당첨)
기타 신청자 → LOST (탈락)
           ↓
WON 상태일 때만 포인트 차감
```

---

## 주요 기능

### 1. 자동화된 숙소 정보 크롤링

```
기존 웹사이트 (lulu-lala.zzzmobile.co.kr)
           ↓
Playwright 기반 크롤러
           ↓
✓ 숙소 기본 정보 (이름, 주소, 연락처, 이미지)
✓ 날짜별 신청 점수 및 인원
✓ 실시간 신청 현황
           ↓
DB 저장 (Accommodations, AccommodationDates, TodayAccommodations)
```

**크롤링 배치 작업**:
- `accommodation_crawler.py`: 전체 숙소 정보 수집 (일 1회)
- `faq_crawler.py`: FAQ 정보 수집 (일 1회 또는 필요 시)
- `today_accommodation_realtime.py`: 오늘자 실시간 신청 현황 갱신 (시간당 1회)

### 2. 공정한 티켓팅 시스템

```
[예약 신청 흐름]
사용자가 숙소 예약 신청
    ↓
PENDING 상태로 DB 저장
    ↓
사용자의 현재 점수를 winning_score_at_time에 저장
    ↓
매일 00:00 (KST) daily_ticketing 배치 작업 실행
    ↓
각 숙소/날짜별로 PENDING 예약을 winning_score_at_time 순으로 정렬
    ↓
최고 점수 1명 → WON (포인트 차감)
나머지 → LOST (포인트 그대로)
    ↓
WON 사용자에게 푸시 알림 발송
```

**특징**:
- 선착순이 아닌 점수 기반 공정 배정
- 포인트는 WON 상태일 때만 차감 (PENDING/LOST는 차감 안됨)
- 배치 작업 시점의 점수가 아닌 신청 시점의 점수(`winning_score_at_time`)로 비교

### 3. 실시간 알림 기능

```
플랫폼별 알림 전달:
┌─────────────────────────────────────┐
│     알림 이벤트 발생                    │
└──────────────┬──────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
 Android   iOS & PC
    │         │
    ▼         ▼
Firebase  Kakao
  FCM      Talk
```

**알림 타입**:
1. **예약 결과 알림**: 티켓팅 결과 (WON/LOST)
2. **찜한 숙소 알림**: 관심 숙소가 내 점수로 예약 가능할 때
3. **포인트 회복 알림**: 일정 시간 경과 후 포인트 회복
4. **인기 숙소 알림**: 경쟁률 높은 숙소 남은 자리 공지

### 4. FAQ 기반 RAG 챗봇

```
사용자 질문
    │
    ▼
FAQ 데이터베이스 검색
    │
    ▼
관련 FAQ 추출
    │
    ▼
LLM으로 맥락화된 응답 생성
    │
    ▼
사용자에게 표시
```

**기능**:
- 크롤링한 FAQ 데이터 기반 RAG
- 예약 정책, 점수 시스템, 취소/변경 정보 자동 응답
- 웹사이트 하단에 Chainlit 위젯으로 제공

### 5. 찜하기 & 스마트 알림

- 최대 20개 숙소 찜하기 가능
- 찜한 숙소가 내 점수로 예약 가능해지면 푸시 알림
- 주말/휴일 자동 필터링
- 신청 점수 변동 시 추가 알림 옵션

---

## 기술 스택

### Frontend
```
Framework:          Next.js 15 (App Router, TypeScript, React 19)
UI Components:      Shadcn/ui (Tailwind CSS)
State Management:   React Query (TanStack Query)
Push Notifications: Firebase Cloud Messaging
Kakao Integration:  Kakao Talk Channel API (iOS/PC 알림)
Forms:              React Hook Form + Zod
HTTP Client:        Axios
Charts/Analytics:   Recharts
```

### Backend
```
Framework:          FastAPI (Python 3.11+)
ORM:                SQLAlchemy 2.0 (async)
Database:           Turso (SQLite Edge) / PostgreSQL
Notifications:      Firebase Admin SDK
Kakao Integration:  Kakao Talk Channel API
Crawling:           Playwright (async)
Task Queue:         Railway Cron Jobs
RAG Chatbot:        Chainlit + LangChain
Vector DB:          Supabase pgvector (선택)
```

### Infrastructure
```
Frontend Hosting:   Vercel
Backend Hosting:    Railway
Database:           Turso (SQLite) / Railway PostgreSQL
File Storage:       Vercel Blob
Monitoring:         Sentry
Logging:            Railway Logs
CI/CD:              GitHub Actions + Vercel + Railway
```

---

## 프로젝트 구조

### 고수준 구조
```
refresh-plus/
├── frontend/          # Next.js 15 + React 19 (TypeScript)
├── backend/           # FastAPI + Python
└── docs/              # 문서
```

### Backend 구조
```
backend/
├── app/
│   ├── main.py              # FastAPI 앱 초기화
│   ├── config.py            # 환경 설정
│   ├── database.py          # DB 연결 (async)
│   ├── dependencies.py      # 의존성 주입 (JWT 인증 등)
│   │
│   ├── models/              # SQLAlchemy ORM 모델
│   │   ├── user.py
│   │   ├── accommodation.py
│   │   ├── accommodation_date.py
│   │   ├── today_accommodation.py
│   │   ├── booking.py
│   │   ├── wishlist.py
│   │   └── faq.py
│   │
│   ├── schemas/             # Pydantic 스키마 (요청/응답 검증)
│   ├── routes/              # API 엔드포인트
│   ├── services/            # 비즈니스 로직
│   │
│   ├── batch/               # 배치 작업 (Railway Cron)
│   │   ├── daily_ticketing.py               # 매일 00:00 티켓팅
│   │   ├── accommodation_crawler.py         # 숙소 정보 크롤링
│   │   ├── faq_crawler.py                   # FAQ 크롤링
│   │   └── today_accommodation_realtime.py  # 실시간 현황 갱신
│   │
│   ├── integrations/        # 외부 서비스 통합
│   │   ├── firebase_service.py  # FCM 푸시 알림
│   │   └── kakao_service.py     # 카카오톡 알림
│   │
│   └── utils/               # 헬퍼 함수
│       └── logger.py
│
└── batch/                   # Railway Cron 실행 스크립트
    ├── run_daily_ticketing.py
    ├── run_accommodation_crawler.py
    ├── run_faq_crawler.py
    └── run_today_accommodation_realtime.py
```

### Frontend 구조
```
frontend/src/
├── app/              # Next.js 15 App Router
│   ├── (auth)/       # 인증 라우트
│   ├── (protected)/  # 보호된 라우트
│   │   ├── accommodations/
│   │   ├── bookings/
│   │   └── wishlist/
│   └── api/          # API 라우트 (웹훅)
│
├── components/       # React 컴포넌트
│   ├── layout/
│   ├── accommodation/
│   ├── booking/
│   └── ui/           # Shadcn/ui 컴포넌트
│
├── lib/              # 유틸리티 함수
│   ├── api.ts        # API 클라이언트
│   ├── firebase.ts   # Firebase 설정
│   └── utils.ts
│
├── hooks/            # 커스텀 React 훅
│   ├── useAccommodations.ts
│   ├── useBookings.ts
│   └── useWishlist.ts
│
└── types/            # TypeScript 타입
```

---

## 설치 및 실행

### 필수 요구사항
- Node.js 18+
- Python 3.11+
- Git
- Railway CLI (배포용)

### Backend 설치

#### 1. 저장소 클론
```bash
git clone https://github.com/your-org/refresh-plus.git
cd refresh-plus/backend
```

#### 2. 가상 환경 생성
```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 편집
```

**필수 환경 변수**:
```env
# 데이터베이스
DATABASE_URL=sqlite+aiosqlite:///./refresh_plus.db

# Firebase (푸시 알림)
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_PROJECT_ID=your_project_id

# Kakao Talk
KAKAO_REST_API_KEY=your_kakao_api_key
KAKAO_CHANNEL_ID=your_channel_id

# 크롤링 (lulu-lala 로그인 정보)
LULU_LALA_USERNAME=your_username
LULU_LALA_PASSWORD=your_password
LULU_LALA_RSA_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# 앱 설정
MAX_WISHLIST_ITEMS=20
POINTS_PER_BOOKING=10
POINTS_RECOVERY_HOURS=24
MAX_POINTS=100
```

#### 5. 데이터베이스 마이그레이션
```bash
alembic upgrade head
```

#### 6. 서버 실행
```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API 문서: http://localhost:8000/docs
```

### Frontend 설치

#### 1. 프론트엔드 디렉토리로 이동
```bash
cd ../frontend
```

#### 2. 의존성 설치
```bash
npm install
```

#### 3. 환경 변수 설정
```bash
cp .env.local.example .env.local
# .env.local 파일 편집
```

**필수 환경 변수**:
```env
# Firebase (FCM)
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 4. 개발 서버 실행
```bash
npm run dev
# 브라우저: http://localhost:3000
```

---

## 배포 가이드

### Backend 배포 (Railway)

#### 1. Railway CLI 설치
```bash
npm i -g @railway/cli
```

#### 2. Railway 로그인 및 초기화
```bash
railway login
railway init
```

#### 3. 환경 변수 설정
Railway 대시보드에서 다음 환경 변수 추가:
- `DATABASE_URL`
- `FIREBASE_CREDENTIALS_BASE64` (Base64 인코딩된 Firebase 인증 정보)
- `KAKAO_REST_API_KEY`
- `LULU_LALA_USERNAME`
- `LULU_LALA_PASSWORD`
- `LULU_LALA_RSA_PUBLIC_KEY`
- `CORS_ORIGINS`

#### 4. 배포
```bash
cd backend
railway up
```

#### 5. Cron 작업 설정

Railway에서 별도 서비스로 각 배치 작업 추가:

**1) Daily Ticketing (매일 00:00 KST = 15:00 UTC)**
```
Service: Daily Ticketing
Schedule: 0 15 * * *
Command: python batch/run_daily_ticketing.py
```

**2) Accommodation Crawler (매일 01:00 KST = 16:00 UTC)**
```
Service: Accommodation Crawler
Schedule: 0 16 * * *
Command: python batch/run_accommodation_crawler.py
```

**3) FAQ Crawler (매일 02:00 KST = 17:00 UTC)**
```
Service: FAQ Crawler
Schedule: 0 17 * * *
Command: python batch/run_faq_crawler.py
```

**4) Today Accommodation Realtime (매시간)**
```
Service: Today Accommodation Realtime
Schedule: 0 * * * *
Command: python batch/run_today_accommodation_realtime.py
```

### Frontend 배포 (Vercel)

#### 1. Vercel CLI 설치
```bash
npm i -g vercel
```

#### 2. 배포
```bash
cd frontend
vercel
```

#### 3. 환경 변수 설정
Vercel 대시보드에서 환경 변수 추가 (`.env.local`과 동일)

#### 4. 자동 배포 설정
- GitHub 연결
- `main` 브랜치 push 시 자동 배포
- PR 생성 시 미리보기 배포

---

## 개발 가이드

### API 개발

#### 새로운 기능 추가 시

1. **모델 생성**: `backend/app/models/feature.py`
2. **스키마 생성**: `backend/app/schemas/feature.py` (Pydantic)
3. **서비스 로직**: `backend/app/services/feature_service.py`
4. **라우트 생성**: `backend/app/routes/feature.py`
5. **라우터 등록**: `backend/app/main.py`에서 `app.include_router()` 호출

#### 배치 작업 추가 시

1. **배치 작업 함수**: `backend/app/batch/new_job.py`
2. **실행 스크립트**: `backend/batch/run_new_job.py`
3. **Railway 설정**: `backend/batch/railway_new_job.json`
4. **Railway Cron 서비스 추가**

### Frontend 개발

#### 새로운 페이지 추가 시

1. **타입 정의**: `frontend/src/types/feature.ts`
2. **API 함수**: `frontend/src/lib/api.ts`
3. **커스텀 훅**: `frontend/src/hooks/useFeature.ts`
4. **컴포넌트**: `frontend/src/components/feature/`
5. **페이지**: `frontend/src/app/(protected)/feature/page.tsx`

### 테스트

#### Backend
```bash
# 모든 테스트 실행
pytest

# 커버리지 리포트
pytest --cov=app

# 특정 테스트
pytest tests/test_bookings.py -v
```

#### Frontend
```bash
# 유닛 테스트
npm run test

# E2E 테스트
npm run test:e2e
```

---

## 환경 설정

### Backend 환경 변수

| 변수명 | 설명 | 필수 |
|-------|------|-----|
| `DATABASE_URL` | 데이터베이스 연결 문자열 | ✅ |
| `FIREBASE_CREDENTIALS_PATH` | Firebase 인증 파일 경로 | ✅ |
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 | ✅ |
| `LULU_LALA_USERNAME` | 크롤링 로그인 사용자명 | ✅ |
| `LULU_LALA_PASSWORD` | 크롤링 로그인 비밀번호 | ✅ |
| `LULU_LALA_RSA_PUBLIC_KEY` | 로그인 암호화 공개키 | ✅ |
| `CORS_ORIGINS` | 허용된 CORS 오리진 (JSON 배열) | ✅ |
| `MAX_WISHLIST_ITEMS` | 최대 찜하기 개수 | ❌ |
| `POINTS_PER_BOOKING` | 예약당 차감 포인트 | ❌ |
| `POINTS_RECOVERY_HOURS` | 포인트 회복 주기 (시간) | ❌ |
| `MAX_POINTS` | 최대 포인트 | ❌ |

### Frontend 환경 변수

| 변수명 | 설명 | 필수 |
|-------|------|-----|
| `NEXT_PUBLIC_API_URL` | Backend API URL | ✅ |
| `NEXT_PUBLIC_FIREBASE_*` | Firebase 설정 | ✅ |

---

## 문제 해결

### Backend 실행 오류

```bash
# 1. 가상 환경 활성화 확인
source venv/bin/activate

# 2. 의존성 재설치
pip install -r requirements.txt

# 3. DB 마이그레이션 확인
alembic upgrade head

# 4. 환경 변수 확인
cat .env | grep DATABASE_URL
```

### Frontend 실행 오류

```bash
# 1. node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# 2. 캐시 삭제
rm -rf .next

# 3. 환경 변수 확인
cat .env.local
```

### 크롤링 실패

1. `LULU_LALA_USERNAME`, `LULU_LALA_PASSWORD` 확인
2. `LULU_LALA_RSA_PUBLIC_KEY` 형식 확인 (`\n` 문자 포함)
3. Playwright 브라우저 설치: `playwright install chromium`
4. 로그 확인: Railway 대시보드 → Logs

---

## 라이선스

MIT License

---

## 연락처

- 📧 이메일: dev@refresh-plus.com
- 🐛 이슈: [GitHub Issues](https://github.com/your-org/refresh-plus/issues)

---

**마지막 업데이트**: 2024년 12월
**버전**: 1.0.0 (Beta)
