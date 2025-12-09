#!/bin/bash
# Docker 빌드 및 테스트 스크립트

set -e  # 에러 발생 시 즉시 중단

echo "🐳 Refresh Plus Backend Docker 빌드 및 테스트"
echo "=============================================="

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Dockerfile 문법 검증
echo ""
echo "📋 1단계: Dockerfile 문법 검증..."
if docker build --no-cache --target base -t refresh-plus-backend:syntax-check -f Dockerfile . > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Dockerfile 문법 검증 통과${NC}"
else
    echo -e "${RED}✗ Dockerfile 문법 오류${NC}"
    exit 1
fi

# 2. 전체 이미지 빌드
echo ""
echo "🔨 2단계: Docker 이미지 빌드 중..."
echo -e "${YELLOW}⏳ 시간이 다소 걸릴 수 있습니다 (특히 Playwright 브라우저 설치)...${NC}"

if docker build -t refresh-plus-backend .; then
    echo -e "${GREEN}✓ 이미지 빌드 완료${NC}"
else
    echo -e "${RED}✗ 이미지 빌드 실패${NC}"
    exit 1
fi

# 3. 이미지 크기 확인
echo ""
echo "📊 3단계: 이미지 정보 확인..."
docker images refresh-plus-backend:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

IMAGE_SIZE=$(docker images refresh-plus-backend:latest --format "{{.Size}}")
echo -e "${GREEN}✓ 이미지 크기: ${IMAGE_SIZE}${NC}"

# 4. 환경 변수 파일 확인
echo ""
echo "🔐 4단계: 환경 변수 파일 확인..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 파일 존재${NC}"
    ENV_FILE=".env"
else
    echo -e "${YELLOW}⚠ .env 파일 없음 (.env.example 사용)${NC}"
    if [ -f ".env.example" ]; then
        ENV_FILE=".env.example"
        echo -e "${YELLOW}⚠ 주의: .env.example을 사용하면 실제 서비스 연결이 안될 수 있습니다${NC}"
    else
        echo -e "${RED}✗ 환경 변수 파일이 없습니다${NC}"
        exit 1
    fi
fi

# 5. 컨테이너 실행 (백그라운드)
echo ""
echo "🚀 5단계: 컨테이너 실행 중..."
docker run -d \
    --name refresh-plus-backend-test \
    -p 8000:8000 \
    --env-file "$ENV_FILE" \
    -e PORT=8000 \
    refresh-plus-backend

echo -e "${YELLOW}⏳ 서버 시작 대기 중 (30초)...${NC}"
sleep 30

# 6. 헬스 체크
echo ""
echo "🏥 6단계: 헬스 체크..."
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 헬스 체크 성공!${NC}"
        HEALTH_CHECK_PASSED=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}⏳ 재시도 ${RETRY_COUNT}/${MAX_RETRIES}...${NC}"
        sleep 5
    fi
done

if [ -z "$HEALTH_CHECK_PASSED" ]; then
    echo -e "${RED}✗ 헬스 체크 실패${NC}"
    echo ""
    echo "컨테이너 로그:"
    docker logs refresh-plus-backend-test --tail 50
    docker stop refresh-plus-backend-test > /dev/null 2>&1
    docker rm refresh-plus-backend-test > /dev/null 2>&1
    exit 1
fi

# 7. API 문서 접근 테스트
echo ""
echo "📚 7단계: API 문서 접근 테스트..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API 문서 접근 가능${NC}"
else
    echo -e "${YELLOW}⚠ API 문서 접근 실패 (인증 필요할 수 있음)${NC}"
fi

# 8. 정리
echo ""
echo "🧹 8단계: 테스트 환경 정리..."
read -p "컨테이너를 중지하고 삭제하시겠습니까? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker stop refresh-plus-backend-test > /dev/null 2>&1
    docker rm refresh-plus-backend-test > /dev/null 2>&1
    echo -e "${GREEN}✓ 테스트 컨테이너 정리 완료${NC}"
else
    echo -e "${YELLOW}ℹ 컨테이너가 계속 실행 중입니다${NC}"
    echo "   - 중지: docker stop refresh-plus-backend-test"
    echo "   - 삭제: docker rm refresh-plus-backend-test"
    echo "   - 로그: docker logs -f refresh-plus-backend-test"
fi

# 최종 요약
echo ""
echo "=============================================="
echo -e "${GREEN}✅ 모든 테스트 완료!${NC}"
echo ""
echo "📝 다음 단계:"
echo "   1. Railway 배포: railway up"
echo "   2. 또는 로컬에서 계속 실행: docker run -p 8000:8000 --env-file .env -e PORT=8000 refresh-plus-backend"
echo "   3. API 문서: http://localhost:8000/docs"
echo ""
