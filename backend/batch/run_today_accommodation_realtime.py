#!/usr/bin/env python3
"""
오늘자 숙소 실시간 정보 갱신 배치 실행 스크립트
Railway Cron 또는 로컬에서 실행
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.batch.today_accommodation_realtime import process_today_accommodation_realtime
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """메인 실행 함수"""
    logger.info("=" * 80)
    logger.info("오늘자 숙소 실시간 정보 갱신 배치 시작")
    logger.info("=" * 80)

    try:
        result = await process_today_accommodation_realtime()

        logger.info("=" * 80)
        logger.info("배치 작업 완료")
        logger.info(f"결과: {result}")
        logger.info("=" * 80)

        if result["status"] == "success":
            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"배치 실행 실패: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
