# Docker 배포 가이드

## 🐳 로컬 Docker 테스트

### 1. Docker 이미지 빌드

```bash
# backend 디렉토리에서 실행
cd backend

# 이미지 빌드
docker build -t refresh-plus-backend .
```

### 2. 로컬에서 컨테이너 실행

```bash
# 환경 변수 파일을 사용하여 실행
docker run -p 8000:8000 \
  --env-file .env \
  -e PORT=8000 \
  refresh-plus-backend
```

### 3. API 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# API 문서
open http://localhost:8000/docs
```

## 🚂 Railway 배포

### 방법 1: Railway CLI 사용 (권장)

```bash
# Railway CLI 설치
npm i -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 배포
railway up
```

### 방법 2: GitHub 연동 (자동 배포)

1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택: `refresh-plus`
4. Root Directory: `backend` 설정
5. 환경 변수 설정:
   - `DATABASE_URL`
   - `FIREBASE_CREDENTIALS_BASE64`
   - `KAKAO_REST_API_KEY`
   - `LULU_LALA_USERNAME`
   - `LULU_LALA_PASSWORD`
   - `LULU_LALA_RSA_PUBLIC_KEY`
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS`

### 방법 3: Dockerfile 직접 사용

Railway는 자동으로 Dockerfile을 감지하고 사용합니다.

**railway.json 설정 업데이트** (선택사항):

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 📊 배포 확인

### 로그 확인

```bash
railway logs
```

### 배포 상태 확인

```bash
railway status
```

### Railway 대시보드 열기

```bash
railway open
```

## 🔧 트러블슈팅

### 문제: Playwright 브라우저 설치 실패

**해결**:
- Dockerfile에서 `playwright install-deps chromium` 명령이 실행되는지 확인
- 빌드 로그에서 에러 메시지 확인

### 문제: PORT 바인딩 오류

**해결**:
- Railway는 자동으로 `PORT` 환경 변수를 주입합니다
- 시작 명령어에서 `$PORT` 또는 `${PORT:-8000}` 사용 확인

### 문제: 메모리 부족

**해결**:
- Railway 플랜 업그레이드
- 또는 Dockerfile 최적화:
  ```dockerfile
  # 멀티스테이지 빌드로 최종 이미지 크기 축소
  # chromadb, sentence-transformers 등 큰 패키지가 필요하지 않으면 제거
  ```

### 문제: 크롤러 실행 오류

**해결**:
- 환경 변수 확인:
  ```bash
  railway variables
  ```
- 로그에서 인증 오류 확인:
  ```bash
  railway logs --service backend
  ```

## 🎯 최적화 팁

### 1. 이미지 크기 축소

필요한 패키지만 설치:
```dockerfile
# requirements.txt를 프로덕션용과 개발용으로 분리
# requirements-prod.txt 생성
RUN pip install --no-cache-dir -r requirements-prod.txt
```

### 2. 빌드 캐싱 활용

requirements.txt 변경이 없으면 캐시 사용:
```dockerfile
# COPY . . 전에 requirements.txt만 먼저 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### 3. 헬스체크 활성화

Railway에서 자동 재시작:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health').read()" || exit 1
```

## 📝 체크리스트

배포 전 확인사항:

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] Railway에 모든 환경 변수가 설정되어 있는지 확인
- [ ] `requirements.txt`에 모든 의존성이 포함되어 있는지 확인
- [ ] 로컬에서 Docker 빌드가 성공하는지 테스트
- [ ] Railway 플랜이 충분한지 확인 (메모리, CPU)
- [ ] 데이터베이스 마이그레이션 완료 확인
- [ ] CORS 설정이 프론트엔드 도메인을 포함하는지 확인

## 🔐 보안 권장사항

1. **환경 변수 관리**:
   - `.env` 파일을 절대 커밋하지 마세요
   - Railway 대시보드에서 환경 변수 설정

2. **Firebase 인증 정보**:
   ```bash
   # Base64 인코딩
   base64 -i firebase-credentials.json | pbcopy
   # Railway에서 FIREBASE_CREDENTIALS_BASE64 환경 변수로 설정
   ```

3. **RSA 공개키**:
   ```bash
   # 줄바꿈을 실제 \n으로 변환
   echo "-----BEGIN PUBLIC KEY-----
   MIIBIjAN...
   -----END PUBLIC KEY-----" | tr '\n' '\\n'
   ```

## 📚 추가 리소스

- [Railway 공식 문서](https://docs.railway.app/)
- [Dockerfile 베스트 프랙티스](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/docker/)

---

**작성일**: 2025-12-09
**프로젝트**: Refresh Plus Backend
