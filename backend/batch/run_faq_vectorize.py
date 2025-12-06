"""
FAQ 벡터화 배치 작업 실행 스크립트 (Railway Cron용)
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 배치 작업 실행
from app.batch.faq_vectorize import vectorize_faqs
import asyncio

if __name__ == "__main__":
    asyncio.run(vectorize_faqs())
