"""
데이터베이스 재생성 스크립트
새로운 스키마에 맞게 테이블을 재생성합니다.
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import (
    Accommodation,
    AccommodationDate,
    User,
    Wishlist,
    TodayAccommodation,
)

async def recreate_database():
    """데이터베이스 재생성"""
    print("데이터베이스 재생성 시작...")
    
    # 기존 테이블 삭제
    async with engine.begin() as conn:
        print("기존 테이블 삭제 중...")
        await conn.run_sync(Base.metadata.drop_all)
        print("기존 테이블 삭제 완료")
        
        # 새 테이블 생성
        print("새 테이블 생성 중...")
        await conn.run_sync(Base.metadata.create_all)
        print("새 테이블 생성 완료")
    
    print("\n생성된 테이블:")
    print("1. accommodations (숙소 정보 원장)")
    print("2. accommodation_dates (날짜별 숙소 내역)")
    print("3. users (사용자 정보)")
    print("4. wishlists (사용자별 즐겨찾기 목록)")
    print("5. today_accommodation_info (오늘자 숙소 내역)")
    print("\n데이터베이스 재생성 완료!")

if __name__ == "__main__":
    asyncio.run(recreate_database())

