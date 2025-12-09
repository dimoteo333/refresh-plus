# Railway 배포용 Dockerfile
# Python 3.11 + Playwright 지원

FROM python:3.11-slim as base

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (Playwright + 일반 도구)
RUN apt-get update && apt-get install -y \
    # 기본 빌드 도구
    gcc \
    g++ \
    make \
    # Playwright 브라우저 실행에 필요한 시스템 라이브러리
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    # 추가 유틸리티
    wget \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치 (Chromium만 설치하여 용량 절약)
RUN playwright install chromium
RUN playwright install-deps chromium

# 애플리케이션 코드 복사
COPY . .

# 시작 명령어 
CMD ["python", "run_accommodation_crawler.py"]