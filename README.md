# 🏨 Refresh Plus - 임직원 복지 숙소 예약 플랫폼

**임직원들을 위한 스마트한 호텔/리조트 예약 시스템**

포인트 기반 티켓팅, 실시간 알림, AI 챗봇을 통합한 하이브리드 모바일 앱

---

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [API 엔드포인트](#api-엔드포인트)
- [배포 가이드](#배포-가이드)
- [기여 가이드](#기여-가이드)

---

## 프로젝트 개요

### 🎯 배경
기존의 임직원용 호텔/리조트 예약 웹사이트의 불편함을 개선하여, 다음을 제공합니다:

- **포인트 기반 예약 시스템**: 임직원들은 일정 점수를 보유하며, 예약할 때마다 차감되고 일정 시간이 경과하면 회복
- **공정한 티켓팅**: 매일 각 숙소별로 티켓팅을 진행하여 점수가 높은 사람이 예약됨
- **스마트 알림**: 개인화된 알림으로 예약 기회를 놓치지 않음
- **AI 챗봇**: 기존 Q&A 게시판 기반 RAG 챗봇으로 즉시 답변


---

## 주요 기능

### 1. 숙소 정보 & 예약 가능성 확인
```
사용자가 볼 수 있는 정보:
- 숙소 상세 정보 (이미지, 설명, 편의시설)
- 현재 본인의 점수로 예약 가능 여부
- 최근 4주간 평균 당첨에 필요한 점수
- 과거 승률 및 통계
```

**구현 방식**:
- 매일 밤 12:00 배치 작업으로 당일 통계 계산
- 실시간 사용자 점수 조회
- 필터링 & 정렬 (인기도, 지역, 가격대)

### 2. 실시간 알림 기능
```
플랫폼별 알림 전달:
┌─────────────────────────────────────┐
│     알림 이벤트 발생                    │
└──────────────┬──────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
 Android   iOS & PC   기타
    │         │
    ▼         ▼
Firebase  Kakao
  FCM      Talk
```

**알림 타입**:
1. **즉시 알림**: 티켓팅 결과, 예약 성공/실패
2. **관심 숙소 알림**: 찜한 숙소가 내 점수로 예약 가능할 때
3. **점수 회복 알림**: 일정 시간 경과 후 점수 회복됨
4. **인기 숙소 알림**: 인기 숙소 남은 자리 공지

### 3. RAG 챗봇 (Chainlit)
```
사용자 질문
    │
    ▼
문서 검색 (임직원 Q&A 게시판)
    │
    ▼
관련 문서 추출
    │
    ▼
LLM으로 응답 생성
    │
    ▼
사용자에게 표시
```

**기능**:
- Q&A 게시판 데이터 기반 RAG
- 예약 정책, 점수 시스템, 취소/변경 정보 자동 응답
- 웹사이트 하단에 Chainlit 위젯으로 제공

### 4. 찜하기 & 스마트 알림
```
사용자 찜하기
    │
    ▼
내 점수로 예약 가능해짐
    │
    ▼
푸시 알림 즉시 발송
    │
    ▼
사용자가 예약 페이지로 이동
```

**특징**:
- 최대 10개 숙소 찜하기 가능
- 주말/휴일 자동 필터링
- 신청 점수 변동시 추가 알림 옵션

---

## 기술 스택

### Frontend
```
Framework:          Next.js 14+ (App Router, TypeScript)
UI Components:      Shadcn/ui (Tailwind CSS)
State Management:   Context API + React Query
Authentication:     Clerk
Push Notifications: Firebase Cloud Messaging
Push (iOS/PC):      Kakao Talk Channel API
Forms:              React Hook Form + Zod
HTTP Client:        Axios / Fetch API
Charts/Analytics:   Chart.js / Recharts
```

### Backend
```
Framework:          FastAPI (Python 3.11+)
ORM:                SQLAlchemy 2.0
Database:           Turso (SQLite Edge)
Task Queue:         AWS Lambda + EventBridge
Authentication:     Clerk SDK (JWT 검증)
Notifications:      Firebase Admin SDK
Kakao Integration:  Kakao Talk Channel API
RAG Chatbot:        Chainlit + LangChain
Vector DB:          Supabase pgvector (선택)
```

### Infrastructure
```
Frontend Hosting:   Vercel
Backend Hosting:    Vercel Functions / AWS Lambda
Database:           Turso (SQLite)
File Storage:       AWS S3 / Vercel Blob
Cache:              Redis (Upstash)
Monitoring:         Sentry
Logging:            CloudWatch / Axiom
CI/CD:              GitHub Actions
```

---

## 프로젝트 구조

### 고수준 구조
```
refresh-plus/
├── frontend/          # Next.js + React (TypeScript)
├── backend/           # FastAPI + Python
├── infra/             # AWS/Vercel 설정
└── docs/              # 문서
```

### Frontend 구조
```
frontend/src/
├── app/              # Next.js App Router
│   ├── (auth)/       # 인증 라우트
│   ├── (protected)/  # 보호된 라우트
│   └── api/          # API 라우트 (웹훅, 대리 요청)
├── components/       # React 컴포넌트
│   ├── layout/       # 레이아웃 컴포넌트
│   ├── accommodation/# 숙소 관련 컴포넌트
│   ├── booking/      # 예약 관련 컴포넌트
│   └── ui/           # Shadcn/ui 컴포넌트
├── lib/              # 유틸리티 함수
│   ├── api.ts        # API 클라이언트
│   ├── firebase.ts   # Firebase 설정
│   └── notifications.ts
├── hooks/            # 커스텀 React 훅
├── context/          # Context API
└── types/            # TypeScript 타입
```

### Backend 구조
```
backend/app/
├── main.py           # FastAPI 앱 초기화
├── config.py         # 설정 (환경 변수)
├── database.py       # DB 연결
├── models/           # SQLAlchemy 모델
├── schemas/          # Pydantic 스키마
├── routes/           # API 라우터
├── services/         # 비즈니스 로직
├── batch/            # AWS Lambda 배치
├── integrations/     # 외부 서비스 통합
└── utils/            # 헬퍼 함수
```

---

## 설치 및 실행

### 필수 요구사항
- Node.js 18+
- Python 3.11+
- Docker (선택사항)
- Git

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
# .env 파일 편집하여 필요한 값 입력
```

#### 5. 데이터베이스 마이그레이션
```bash
alembic upgrade head
```

#### 6. 서버 실행
```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend 설치

#### 1. 저장소 클론 (위에서 했으면 생략)
```bash
cd refresh-plus/frontend
```

#### 2. 의존성 설치
```bash
npm install
# 또는
yarn install
```

#### 3. 환경 변수 설정
```bash
cp .env.local.example .env.local
# .env.local 파일 편집하여 필요한 값 입력
```

필수 환경 변수:
```env
# Clerk 인증
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_key
CLERK_SECRET_KEY=your_secret

# Firebase
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_id

# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Kakao
NEXT_PUBLIC_KAKAO_APP_ID=your_id
```

#### 4. 개발 서버 실행
```bash
npm run dev
# 또는
yarn dev
```

브라우저에서 `http://localhost:3000` 접속

### Docker 환경에서 실행

#### 전체 스택 시작
```bash
docker-compose up -d
```

서비스:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

#### 특정 서비스만 시작
```bash
docker-compose up -d backend
docker-compose up -d frontend
```

---

## API 엔드포인트

### 숙소 API

#### 전체 숙소 조회
```http
GET /api/accommodations?filter=available&sort=popularity

Query Parameters:
  - filter: available | all | bookable
  - sort: popularity | price | rating
  - region: 지역 코드
  - page: 페이지 번호 (기본값: 1)
  - limit: 페이지당 개수 (기본값: 20)

Response:
{
  "total": 150,
  "page": 1,
  "items": [
    {
      "id": "acc_123",
      "name": "샬레 펜션",
      "region": "강원",
      "price": 120000,
      "image_url": "...",
      "can_book_with_current_score": true,
      "avg_winning_score_4weeks": 85,
      "availability": 3,
      "rating": 4.8
    }
  ]
}
```

#### 숙소 상세 조회
```http
GET /api/accommodations/{accommodation_id}

Response:
{
  "id": "acc_123",
  "name": "샬레 펜션",
  "description": "...",
  "images": ["..."],
  "amenities": ["WiFi", "주방", "..."],
  "price": 120000,
  "capacity": 4,
  "bookings_4weeks": [
    {"date": "2024-12-20", "status": "available", "winning_score": 85},
    ...
  ],
  "my_score": 92,
  "can_book": true,
  "past_bookings": 5,
  "win_rate": 0.35
}
```

### 예약 API

#### 예약 생성 (티켓팅)
```http
POST /api/bookings

Request:
{
  "accommodation_id": "acc_123",
  "check_in": "2024-12-20",
  "check_out": "2024-12-22",
  "guests": 2
}

Response:
{
  "id": "booking_456",
  "status": "won",  # won | lost | pending
  "accommodation_id": "acc_123",
  "score_deducted": 15,
  "remaining_score": 85,
  "confirmation_number": "REFRESH-20241220-001"
}
```

#### 예약 목록
```http
GET /api/bookings?status=completed

Query Parameters:
  - status: pending | won | lost | completed | cancelled
  - sort: date | status

Response:
{
  "items": [
    {
      "id": "booking_456",
      "accommodation": {...},
      "check_in": "2024-12-20",
      "check_out": "2024-12-22",
      "status": "won",
      "created_at": "2024-12-10T14:30:00Z"
    }
  ]
}
```

### 찜하기 API

#### 찜하기 추가
```http
POST /api/wishlist

Request:
{
  "accommodation_id": "acc_123",
  "notify_when_bookable": true
}

Response:
{
  "id": "wishlist_789",
  "accommodation_id": "acc_123",
  "created_at": "2024-12-10T14:30:00Z"
}
```

#### 찜하기 목록
```http
GET /api/wishlist

Response:
{
  "items": [
    {
      "id": "wishlist_789",
      "accommodation": {...},
      "bookable_with_current_score": true,
      "created_at": "2024-12-10T14:30:00Z"
    }
  ]
}
```

### 사용자 API

#### 내 프로필 & 점수
```http
GET /api/users/me

Response:
{
  "id": "user_123",
  "email": "user@company.com",
  "name": "김임직",
  "current_score": 100,
  "total_bookings": 5,
  "success_rate": 0.6,
  "next_score_recovery": "2024-12-15T00:00:00Z",
  "tier": "gold"  # silver | gold | platinum
}
```

#### 점수 회복 스케줄 조회
```http
GET /api/users/me/score-recovery-schedule

Response:
{
  "current_score": 85,
  "max_score": 100,
  "recovery_per_period": 10,
  "recovery_period_hours": 24,
  "next_recovery": "2024-12-15T00:00:00Z",
  "recoveries_remaining_today": 2
}
```

### 알림 설정 API

#### 알림 설정 조회
```http
GET /api/notifications/preferences

Response:
{
  "push_enabled": true,
  "push_on_booking_result": true,
  "push_on_wishlist_bookable": true,
  "push_on_score_recovery": false,
  "kakao_enabled": true,
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00"
  }
}
```

#### 알림 설정 업데이트
```http
PUT /api/notifications/preferences

Request:
{
  "push_enabled": true,
  "push_on_booking_result": true,
  "kakao_enabled": true
}

Response: {설정된 preferences}
```

더 자세한 API 문서는 [API.md](./docs/API.md) 참고

---

## 배포 가이드

### Frontend 배포 (Vercel)

#### 1. Vercel 연결
```bash
npx vercel login
```

#### 2. 프로젝트 초기 배포
```bash
cd frontend
npx vercel
```

#### 3. 환경 변수 설정 (Vercel Dashboard)
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
NEXT_PUBLIC_API_URL=https://api.refresh-plus.com
# 기타 환경 변수 추가
```

#### 4. 자동 배포 설정
- GitHub 연결: Vercel에서 GitHub 저장소 선택
- 자동 배포: main 브랜치에 push시 자동 배포
- 미리보기: PR 생성시 자동 preview 배포

### Backend 배포

#### 옵션 1: Vercel (Node.js)
FastAPI를 Vercel에 배포할 수 없으므로 다음 옵션 중 선택:

#### 옵션 2: AWS Lambda + API Gateway
```bash
cd backend

# 환경 변수 설정
cp .env.example .env.production
# .env.production 편집

# Lambda 함수로 배포
serverless deploy --stage production
```

#### 옵션 3: Railway/Render
```bash
# Railway 배포 (추천)
railway login
railway init
railway up

# 또는 Render
# render.yaml 설정 후 Render 대시보드에서 배포
```

#### 옵션 4: Docker (AWS ECS)
```bash
# ECR에 이미지 푸시
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.ap-northeast-2.amazonaws.com

docker build -t refresh-plus-backend .
docker tag refresh-plus-backend:latest \
  123456789.dkr.ecr.ap-northeast-2.amazonaws.com/refresh-plus-backend:latest
docker push \
  123456789.dkr.ecr.ap-northeast-2.amazonaws.com/refresh-plus-backend:latest

# ECS 배포
# (CloudFormation 또는 Terraform으로 자동화)
```

### 배치 작업 배포 (AWS Lambda)

#### 1. 함수 생성
```bash
cd backend/app/batch

# daily_ticketing 함수
zip -r ../../../daily_ticketing.zip daily_ticketing.py requirements.txt

aws lambda create-function \
  --function-name refresh-plus-daily-ticketing \
  --runtime python3.11 \
  --role arn:aws:iam::123456789:role/lambda-role \
  --handler daily_ticketing.handler \
  --zip-file fileb://daily_ticketing.zip
```

#### 2. EventBridge 트리거 설정
```bash
# 매일 00:00 (UTC+9) 실행
aws events put-rule \
  --name refresh-plus-daily-ticketing \
  --schedule-expression "cron(0 15 * * ? *)"  # UTC 기준

aws events put-targets \
  --rule refresh-plus-daily-ticketing \
  --targets "Id"="1","Arn"="arn:aws:lambda:ap-northeast-2:123456789:function:refresh-plus-daily-ticketing"
```

---

## 모니터링 & 로깅

### Sentry 설정

#### Backend
```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
    environment=settings.ENVIRONMENT
)
```

#### Frontend
```typescript
// frontend/src/lib/sentry.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 1.0,
  environment: process.env.NODE_ENV,
});
```

### 로깅

#### Backend 로그 레벨
```
DEBUG:   개발 단계 상세 정보
INFO:    일반 정보 (예약 생성, 점수 회복)
WARNING: 경고 (높은 에러율, 이상 거래)
ERROR:   오류 (DB 연결 실패, API 에러)
CRITICAL: 심각한 오류 (시스템 다운)
```

---

## 성능 최적화

### Frontend 최적화
- **Next.js Image**: 이미지 자동 최적화 및 lazy loading
- **Code Splitting**: 자동 route-based splitting
- **Caching**: 정적 자산 장기 캐싱
- **Database Queries**: React Query로 스마트 캐싱

### Backend 최적화
- **Async/Await**: FastAPI 전체에서 비동기 처리
- **Connection Pooling**: SQLAlchemy 커넥션 풀
- **Caching**: Redis로 자주 조회되는 데이터 캐싱
- **Pagination**: 대량 데이터 조회시 페이지네이션

### 데이터베이스 최적화
- **Index**: 검색 칼럼에 인덱스 생성
- **Query Optimization**: N+1 문제 해결
- **Backup**: 일일 자동 백업

---

## 보안

### 인증 & 인가
- **Clerk**: JWT 기반 인증
- **RBAC**: 역할 기반 접근 제어
- **CORS**: 안전한 크로스 도메인 요청

### 데이터 보안
- **HTTPS**: 모든 통신 암호화
- **환경 변수**: 민감한 정보 저장
- **Input Validation**: Pydantic으로 자동 검증
- **Rate Limiting**: DDoS 방지

### 컴플라이언스
- **GDPR**: 개인정보 보호
- **로그 감시**: 의심 활동 모니터링
- **정기 감사**: 보안 취약점 검사

---

## 테스트

### Backend 테스트
```bash
# 모든 테스트 실행
pytest

# 커버리지 리포트
pytest --cov=app

# 특정 테스트만 실행
pytest tests/test_bookings.py -v
```

### Frontend 테스트
```bash
# 유닛 테스트
npm run test

# E2E 테스트
npm run test:e2e

# 커버리지
npm run test:coverage
```

---

## 기여 가이드

### 개발 워크플로우

1. **이슈 선택**: GitHub Issues에서 작업할 이슈 선택
2. **브랜치 생성**: `git checkout -b feature/issue-description`
3. **코드 작성**: 커밋 메시지 규칙 준수
4. **푸시**: `git push origin feature/issue-description`
5. **PR 생성**: PR에 변경사항 상세 설명
6. **코드 리뷰**: 팀 리뷰 후 머지

### 커밋 메시지 규칙
```
[type]: [subject]

[body]

Fixes #[issue-number]
```

타입:
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 변경
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가
- `chore`: 빌드, 의존성 등

예시:
```
feat: 찜하기 알림 기능 추가

사용자가 찜한 숙소가 내 점수로 예약 가능해지면 푸시 알림 발송

Fixes #123
```

---

## 문제 해결

### Backend 시작 안될 때
```bash
# 1. 가상 환경 활성화 확인
source venv/bin/activate

# 2. 모든 의존성 설치 확인
pip install -r requirements.txt

# 3. DB 마이그레이션 확인
alembic upgrade head

# 4. 환경 변수 확인
cat .env | grep DATABASE_URL

# 5. 로그 확인
tail -f logs/app.log
```

### Frontend 시작 안될 때
```bash
# 1. node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# 2. 환경 변수 확인
cat .env.local

# 3. 캐시 삭제
rm -rf .next

# 4. 포트 체크
lsof -i :3000
```

### Firebase 푸시 알림 안 올 때
1. FCM 토큰 저장 확인
2. Firebase 프로젝트 설정 확인
3. 기기의 알림 권한 확인
4. Firebase 콘솔에서 테스트 메시지 전송

---

## 라이선스

MIT License - 자세한 내용은 [LICENSE](./LICENSE) 참고

---

## 연락처

- 📧 이메일: [dev@refresh-plus.com]
- 🐛 이슈: [GitHub Issues](https://github.com/your-org/refresh-plus/issues)
- 💬 토론: [GitHub Discussions](https://github.com/your-org/refresh-plus/discussions)

---

## 지원

이 프로젝트가 도움이 되었다면 ⭐ Star를 눌러주세요!

**마지막 업데이트**: 2024년 12월
**버전**: 1.0.0 (Alpha)
