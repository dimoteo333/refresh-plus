# 🏨 Refresh Plus - 신한은행 임직원 숙소 예약 플랫폼

**임직원들을 위한 스마트한 연성소(호텔/펜션/리조트) 예약 시스템**

포인트 기반 티켓팅, 직접 예약, 실시간 알림, AI 챗봇을 통합한 웹/모바일 플랫폼

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

- **이중 예약 시스템**: 공정한 티켓팅과 즉시 예약을 모두 지원
  - **티켓팅 시스템**: 포인트 기반으로 매일 자정(00:00 KST) 배치 작업을 통해 최고 점수자에게 자동 배정
  - **직접 예약**: 실시간으로 lulu-lala에 직접 예약 요청 (08:00~21:00 KST 시간 제한)
- **자동화된 크롤링**: 기존 웹사이트에서 숙소 정보, FAQ, 실시간 신청 현황 자동 수집
- **실시간 알림**: Firebase FCM 푸시 알림으로 예약 기회를 놓치지 않음
- **AI 챗봇**: FAQ 기반 RAG 챗봇으로 즉시 답변
- **모던 UI/UX**: Next.js 15 + React 19 기반 반응형 웹 인터페이스

### 🌟 핵심 비즈니스 로직

#### 1. 티켓팅 시스템 (공정한 배정)

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

#### 2. 직접 예약 시스템 (실시간 예약)

```
사용자가 숙소 상세에서 날짜 선택
           ↓
"예약하기" 버튼 클릭
           ↓
시간 제한 체크 (08:00~21:00 KST)
           ↓
연락처 입력 & 개인정보 동의
           ↓
lulu-lala API로 직접 POST 요청
           ↓
HTTP 302 응답 → 성공
           ↓
즉시 WON 상태로 Booking 생성
           ↓
포인트 10점 차감
```

**차이점**:
- **티켓팅**: 신청 시 PENDING → 자정에 배치 작업으로 WON/LOST 결정
- **직접 예약**: 즉시 lulu-lala API 호출 → 성공 시 바로 WON 상태

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
- `accommodation_crawler.py`: 전체 숙소 정보 수집 (매일 01:00 KST)
- `faq_crawler.py`: FAQ 정보 수집 (매일 02:00 KST)
- `today_accommodation_realtime.py`: 오늘자 실시간 신청 현황 갱신 (매시간)

**인증 방식**:
- RSA 공개키로 비밀번호 암호화
- 세션 쿠키 저장하여 재사용
- 직접 예약 시 사용자의 session_cookies 활용

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

### 3. 직접 예약 시스템

```
[직접 예약 흐름]
숙소 상세 페이지에서 예약 가능 날짜 선택
    ↓
"예약하기" 버튼 표시
    ↓
버튼 클릭 → 예약 모달 표시
    ↓
시간 제한 실시간 체크 (08:00~21:00 KST)
    ↓
숙박자 정보 자동 입력 (현재 로그인 사용자)
연락처 입력 (010-XXXX-XXXX)
개인정보 동의 체크
    ↓
"예약하기" 버튼 클릭
    ↓
Backend에서 lulu-lala API로 POST 요청
(사용자의 session_cookies로 인증)
    ↓
HTTP 302 응답 확인 → 성공
    ↓
Booking 테이블에 WON 상태로 즉시 저장
포인트 10점 차감
    ↓
성공 메시지 표시
"예약에 성공했습니다. 해당 숙박에 대한 배정 결과는 익일 07시에 확인 가능합니다."
```

**주요 특징**:
- **시간 제한**: 08:00~21:00 KST만 예약 가능
- **실시간 경고**: 20:00 이후 "예약 가능 시간이 얼마 남지 않았습니다" 표시
- **모바일 최적화**: 연락처 입력 필드 모바일 화면에 맞게 조정
- **즉시 반영**: 성공 시 바로 WON 상태로 저장 (PENDING 단계 없음)
- **세션 재사용**: 로그인된 사용자의 session_cookies로 인증

**API 엔드포인트**:
```
POST /api/bookings/direct-reserve
{
  "accommodation_id": "숙소 ID",
  "check_in_date": "2024-12-25",
  "phone_number": "010-1234-5678"
}
```

**성공 기준**:
- lulu-lala API 응답 HTTP 302 (리다이렉트)

### 4. 실시간 알림 기능

```
Firebase Cloud Messaging (FCM)
           ↓
Android / iOS / Web 푸시 알림
```

**알림 타입**:
1. **예약 결과 알림**: 티켓팅 결과 (WON/LOST)
2. **찜한 숙소 알림**: 관심 숙소가 내 점수로 예약 가능할 때
3. **포인트 회복 알림**: 일정 시간 경과 후 포인트 회복
4. **인기 숙소 알림**: 경쟁률 높은 숙소 남은 자리 공지

### 5. FAQ 기반 RAG 챗봇

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

### 6. 찜하기 & 스마트 알림

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
Push Notifications: Firebase Cloud Messaging (FCM)
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
Crawling:           Playwright (async)
Task Queue:         Railway Cron Jobs
RAG Chatbot:        Chainlit + LangChain
Vector DB:          Supabase pgvector (선택)
Timezone:           pytz (KST 시간 처리)
HTTP Client:        httpx (async)
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
│   │   ├── booking.py       # DirectReservationCreate, DirectReservationResponse 포함
│   │   └── ...
│   │
│   ├── routes/              # API 엔드포인트
│   │   ├── bookings.py      # POST /direct-reserve 포함
│   │   └── ...
│   │
│   ├── services/            # 비즈니스 로직
│   │   ├── booking_service.py  # create_direct_reservation() 포함
│   │   └── ...
│   │
│   ├── batch/               # 배치 작업 (Railway Cron)
│   │   ├── daily_ticketing.py               # 매일 00:00 티켓팅
│   │   ├── accommodation_crawler.py         # 숙소 정보 크롤링
│   │   ├── faq_crawler.py                   # FAQ 크롤링
│   │   └── today_accommodation_realtime.py  # 실시간 현황 갱신
│   │
│   ├── integrations/        # 외부 서비스 통합
│   │   └── firebase_service.py  # FCM 푸시 알림
│   │
│   └── utils/               # 헬퍼 함수
│       ├── logger.py
│       ├── time_utils.py    # KST 시간 제한 체크
│       └── phone_utils.py   # 전화번호 파싱
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
│   │   ├── accommodations/[id]/page.tsx  # 숙소 상세 (직접 예약 포함)
│   │   ├── bookings/
│   │   └── wishlist/
│   └── api/          # API 라우트 (웹훅)
│
├── components/       # React 컴포넌트
│   ├── layout/
│   ├── accommodation/
│   │   ├── DirectReservationModal.tsx  # 직접 예약 모달
│   │   └── ...
│   ├── booking/
│   └── ui/           # Shadcn/ui 컴포넌트
│
├── lib/              # 유틸리티 함수
│   ├── api.ts        # API 클라이언트 (createDirectReservation 포함)
│   ├── firebase.ts   # Firebase 설정
│   └── utils.ts
│
├── hooks/            # 커스텀 React 훅
│   ├── useAccommodations.ts
│   ├── useBookings.ts
│   └── useWishlist.ts
│
└── types/            # TypeScript 타입
    ├── booking.ts    # DirectReservationCreate, DirectReservationResponse 포함
    └── ...
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

### 직접 예약 실패

1. **시간 제한 확인**: 08:00~21:00 KST만 예약 가능
2. **세션 쿠키 확인**: 사용자가 로그인되어 있고 session_cookies가 유효한지 확인
3. **HTTP 302 응답 확인**: lulu-lala API가 302 리다이렉트를 반환하는지 확인
4. **포인트 충분 여부**: 사용자 포인트가 10점 이상인지 확인
5. **중복 예약 확인**: 동일 날짜에 이미 WON 상태 예약이 있는지 확인

---

## 주요 API 엔드포인트

### 티켓팅 예약
```
POST /api/bookings
{
  "accommodation_id": "string",
  "check_in": "datetime",
  "check_out": "datetime",
  "guests": 2
}
```

### 직접 예약
```
POST /api/bookings/direct-reserve
{
  "accommodation_id": "string",
  "check_in_date": "2024-12-25",
  "phone_number": "010-1234-5678"
}
```

### 예약 내역 조회
```
GET /api/bookings?status=WON
```

### 찜하기 추가
```
POST /api/wishlist
{
  "accommodation_id": "string",
  "desired_date": "2024-12-25",
  "notify_enabled": true
}
```

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
