#!/usr/bin/env python3
"""
실제 작동 중인 배치에서 HTML 덤프
"""

import asyncio
import sys
import os
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

            if not nav_success:
                logger.error("Navigation failed")
                return

            # 첫 번째 숙소 (ID: 1)로 이동
            acc_url = "https://shbrefresh.interparkb2b.co.kr/condo/1"
            logger.info(f"Navigating to: {acc_url}")
            await page.goto(acc_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # HTML 구조 확인
            logger.info("=" * 80)
            logger.info("Dumping HTML from first 3 roomInfo elements...")
            logger.info("=" * 80)

            room_info_elements = await page.query_selector_all('[data-role="roomInfo"]')
            logger.info(f"Found {len(room_info_elements)} room info elements\n")

            # 처음 3개만 확인
            for idx, room_info in enumerate(room_info_elements[:3]):
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Room Info Element #{idx + 1}")
                logger.info(f"{'=' * 80}")

                # data-rblockdate 속성
                date_str = await room_info.get_attribute("data-rblockdate")
                logger.info(f"data-rblockdate: {date_str}")

                # 모든 속성 출력
                all_attrs = await room_info.evaluate("el => Array.from(el.attributes).map(a => `${a.name}=\"${a.value}\"`).join(' ')")
                logger.info(f"Attributes: {all_attrs}")

                # 전체 HTML
                html = await room_info.inner_html()
                logger.info(f"\nFull HTML:\n{html}\n")

                # 텍스트 내용
                text = await room_info.inner_text()
                logger.info(f"Text content:\n{text}\n")

                # room_status 요소 찾기
                room_status = await room_info.query_selector(".room_status, [class*='room_status']")
                if room_status:
                    status_html = await room_status.inner_html()
                    status_text = await room_status.inner_text()
                    logger.info(f"room_status HTML:\n{status_html}\n")
                    logger.info(f"room_status Text:\n{status_text}\n")
                else:
                    logger.info("No room_status element found\n")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
