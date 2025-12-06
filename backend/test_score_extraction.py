#!/usr/bin/env python3
"""
점수 추출 테스트
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.batch.today_accommodation_realtime import login_to_lulu_lala, navigate_to_reservation_page
from app.config import settings
from app.utils.logger import get_logger
from playwright.async_api import async_playwright

logger = get_logger(__name__)


async def main():
    """메인 실행 함수"""
    username = settings.LULU_LALA_USERNAME
    password = settings.LULU_LALA_PASSWORD
    rsa_public_key = settings.LULU_LALA_RSA_PUBLIC_KEY

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            # 로그인
            logger.info("Logging in...")
            await login_to_lulu_lala(page, username, password, rsa_public_key)

            # Reservation 페이지로 이동
            logger.info("Navigating to reservation page...")
            nav_success, page = await navigate_to_reservation_page(page, context)

            # 첫 번째 숙소로 이동
            acc_url = "https://shbrefresh.interparkb2b.co.kr/condo/1"
            logger.info(f"Navigating to: {acc_url}")
            await page.goto(acc_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Room info 요소 찾기
            room_info_elements = await page.query_selector_all('[data-role="roomInfo"]')
            logger.info(f"\nFound {len(room_info_elements)} room info elements\n")

            # 처음 5개 확인
            for idx, room_info in enumerate(room_info_elements[:5]):
                date_str = await room_info.get_attribute("data-rblockdate")
                first_score = await room_info.get_attribute("data-first-room-score")
                perm_score = await room_info.get_attribute("data-permanent-room-score")
                apply_count = await room_info.get_attribute("data-apply-count")

                # 점수 변환
                choi_score = float(first_score) if first_score and first_score.strip() else 0.0
                sangsi_score = float(perm_score) if perm_score and perm_score.strip() else 0.0
                score = max(choi_score, sangsi_score)
                applicants = int(apply_count) if apply_count and apply_count.strip() else 0

                logger.info(f"[{idx+1}] {date_str}")
                logger.info(f"  data-first-room-score: '{first_score}' → {choi_score}")
                logger.info(f"  data-permanent-room-score: '{perm_score}' → {sangsi_score}")
                logger.info(f"  data-apply-count: '{apply_count}' → {applicants}")
                logger.info(f"  Final score: {score}점 (최초: {choi_score}, 상시: {sangsi_score})\n")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
