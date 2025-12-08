#!/usr/bin/env python3
"""
숙소 날짜별 온라인 가격 크롤링 배치 작업 실행 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from app.batch.accommodation_dates_price_crawler import process_accommodation_dates_price_crawler


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Starting accommodation dates price crawler...")
        print("=" * 60)

        result = asyncio.run(process_accommodation_dates_price_crawler())

        print("\n" + "=" * 60)
        print("Batch job completed successfully!")
        print(f"Result: {result}")
        print("=" * 60)

        if result.get("status") == "error":
            sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
