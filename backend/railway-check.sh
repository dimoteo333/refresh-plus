#!/bin/bash
# Railway 배포 전 체크리스트

echo "🚂 Railway 배포 체크리스트"
echo "=============================="
echo ""

# 1. Dockerfile 존재 확인
echo "1️⃣ Dockerfile 확인..."
if [ -f "Dockerfile" ]; then
    echo "   ✅ Dockerfile 존재"
else
    echo "   ❌ Dockerfile 없음"
    exit 1
fi

# 2. railway.json 확인
echo ""
echo "2️⃣ railway.json 확인..."
if [ -f "railway.json" ]; then
    echo "   ✅ railway.json 존재"
    echo "   📄 내용:"
    cat railway.json | grep -A 2 "build"
else
    echo "   ⚠️  railway.json 없음"
fi

# 3. Git 상태 확인
echo ""
echo "3️⃣ Git 상태 확인..."
if git ls-files Dockerfile > /dev/null 2>&1; then
    echo "   ✅ Dockerfile이 Git에 추가됨"
else
    echo "   ❌ Dockerfile이 Git에 추가되지 않음"
    exit 1
fi

# 4. 최근 커밋 확인
echo ""
echo "4️⃣ 최근 커밋 확인..."
git log --oneline -1

# 5. Remote 확인
echo ""
echo "5️⃣ Remote 확인..."
git remote -v | grep origin

# 6. Push 상태 확인
echo ""
echo "6️⃣ Push 상태 확인..."
if git diff origin/master --quiet; then
    echo "   ✅ 로컬과 리모트가 동기화됨"
else
    echo "   ⚠️  로컬 변경사항이 push되지 않음"
    echo "   실행: git push origin master"
fi

# 7. 필수 파일 확인
echo ""
echo "7️⃣ 필수 파일 확인..."
FILES=("requirements.txt" "app/main.py" ".dockerignore")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file 없음"
    fi
done

# 8. Railway CLI 확인
echo ""
echo "8️⃣ Railway CLI 확인..."
if command -v railway &> /dev/null; then
    echo "   ✅ Railway CLI 설치됨"
    railway --version
else
    echo "   ❌ Railway CLI 미설치"
    echo "   설치: npm i -g @railway/cli"
fi

# 최종 권장사항
echo ""
echo "=============================="
echo "📋 Railway 배포 권장사항"
echo "=============================="
echo ""
echo "1. Railway 대시보드 설정:"
echo "   Settings → Root Directory → 'backend' 입력"
echo ""
echo "2. 환경 변수 설정 확인:"
echo "   - DATABASE_URL"
echo "   - FIREBASE_CREDENTIALS_BASE64"
echo "   - KAKAO_REST_API_KEY"
echo "   - LULU_LALA_USERNAME"
echo "   - LULU_LALA_PASSWORD"
echo "   - LULU_LALA_RSA_PUBLIC_KEY"
echo "   - ENVIRONMENT=production"
echo "   - CORS_ORIGINS"
echo ""
echo "3. 배포 명령어:"
echo "   railway up"
echo ""
