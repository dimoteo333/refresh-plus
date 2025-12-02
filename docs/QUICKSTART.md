# Refresh Plus - Quick Start Guide

## 빠른 시작 (5분 안에)

### 1. 필수 요구사항
- Node.js 18+
- Python 3.11+
- Git
- Railway CLI (배포시): `npm i -g @railway/cli`

### 2. 프로젝트 클론
```bash
git clone <repository-url>
cd refresh_plus
```

### 3. Backend 설정
```bash
cd backend

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 입력

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend가 http://localhost:8000 에서 실행됩니다.
API 문서: http://localhost:8000/docs

### 4. Frontend 설정
```bash
cd ../frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.local.example .env.local
# .env.local 파일을 편집하여 필요한 값 입력

# 개발 서버 실행
npm run dev
```

Frontend가 http://localhost:3000 에서 실행됩니다.

## 배치 작업 테스트 (로컬)

```bash
# 일일 티켓팅 배치 작업
cd backend
python batch/run_daily_ticketing.py

# 점수 회복 배치 작업
python batch/run_score_recovery.py
```

## Railway 배포 (프로덕션)

### Backend API 배포
```bash
cd backend
railway login
railway init
railway up

# 환경 변수 설정
railway variables set DATABASE_URL=<your-database-url>
railway variables set CLERK_SECRET_KEY=<your-key>
# ... 기타 환경 변수
```

### Frontend 배포 (Vercel)
```bash
cd frontend
npm install -g vercel
vercel login
vercel
```

### 배치 작업 배포

Railway Dashboard에서:
1. New Service 클릭
2. Same GitHub Repo 선택
3. Service Type: Cron
4. Root Directory: `backend`
5. Cron Schedule 설정:
   - Daily Ticketing: `0 15 * * *` (00:00 KST)
   - Score Recovery: `0 * * * *` (매시간)
6. Start Command:
   - `python batch/run_daily_ticketing.py`
   - `python batch/run_score_recovery.py`

자세한 내용은 [Railway 배포 가이드](RAILWAY_DEPLOYMENT.md) 참고

## 주요 기능

- **숙소 예약**: 포인트 기반 티켓팅 시스템
- **찜하기**: 관심 숙소 저장 및 알림
- **실시간 알림**: Firebase FCM + Kakao Talk
- **AI 챗봇**: RAG 기반 질문 응답 (예정)

## 다음 단계

- [전체 README](../README.md) 참고
- [Railway 배포 가이드](RAILWAY_DEPLOYMENT.md) 읽기
- [API 문서](http://localhost:8000/docs) 확인
- [개발 가이드](DEVELOPMENT_GUIDE.md) 읽기 (있는 경우)

## 문제 해결

### Backend 시작 안될 때
```bash
# 가상 환경 활성화 확인
which python  # venv 경로여야 함

# 의존성 재설치
pip install -r requirements.txt --force-reinstall

# 환경 변수 확인
cat .env | grep DATABASE_URL
```

### Frontend 시작 안될 때
```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# 환경 변수 확인
cat .env.local | grep NEXT_PUBLIC
```

### Railway 배포 실패시
```bash
# 로그 확인
railway logs

# 특정 서비스 로그
railway logs --service <service-name>

# 환경 변수 확인
railway variables
```

## 지원

이슈가 있으면 GitHub Issues에 문의하세요!
