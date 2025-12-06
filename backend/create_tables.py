"""
데이터베이스 테이블 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, Base
from app.models import (
    User,
    Accommodation,
    AccommodationDate,
    TodayAccommodation,
    Wishlist,
    FAQ,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_tables():
    """모든 테이블 생성"""
    logger.info("Creating database tables...")

    try:
        async with engine.begin() as conn:
            # 모든 테이블 생성 (이미 존재하면 스킵)
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✓ All tables created successfully!")
        logger.info("Tables:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")

    except Exception as e:
        logger.error(f"✗ Failed to create tables: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(create_tables())
    sys.exit(exit_code)
