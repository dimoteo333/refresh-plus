"""
오늘자 숙소 실시간 정보 갱신 배치 작업
- today_accommodation_info 테이블을 실시간으로 갱신
- 최초 실행: 신청가능한 날짜만 크롤링해서 저장
- 반복 실행: 기존 데이터 실시간 갱신
"""

import asyncio
import json
import re
from datetime import datetime, date as date_obj
from typing import List, Dict, Optional, Set, Tuple
from sqlalchemy import select, func, delete, or_
from app.database import AsyncSessionLocal
from app.models.accommodation import Accommodation
from app.models.today_accommodation import TodayAccommodation
from app.config import settings
from app.utils.logger import get_logger
from app.utils.sol_score import calculate_sol_scores_for_today_accommodation
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from auth.lulu_lala_auth import (
    login_to_lulu_lala,
    navigate_to_reservation_page,
)

logger = get_logger(__name__)

# 숙소 조회 URL
SHB_REFRESH_INTRO_URL = "https://shbrefresh.interparkb2b.co.kr/intro"
SHB_REFRESH_INDEX_URL = "https://shbrefresh.interparkb2b.co.kr/index"


async def check_if_today_accommodation_empty() -> bool:
    """
    today_accommodation_info 테이블이 비어있는지 확인
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(func.count(TodayAccommodation.id))
            )
            count = result.scalar()
            is_empty = count == 0
            logger.info(f"TodayAccommodation table {'is empty' if is_empty else f'has {count} records'}")
            return is_empty
        except Exception as e:
            logger.error(f"Error checking TodayAccommodation table: {str(e)}")
            return True


async def get_all_accommodation_ids() -> List[str]:
    """
    모든 숙소 ID 가져오기
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Accommodation.id))
            ids = [row[0] for row in result.fetchall()]
            logger.info(f"Found {len(ids)} accommodations in database")
            return ids
        except Exception as e:
            logger.error(f"Error fetching accommodation IDs: {str(e)}")
            return []


async def get_existing_today_accommodations() -> List[Tuple[str, str]]:
    """
    기존 TodayAccommodation 레코드의 (accommodation_id, date) 쌍 가져오기
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(TodayAccommodation.accommodation_id, TodayAccommodation.date)
            )
            records = [(row[0], row[1]) for row in result.fetchall()]
            logger.info(f"Found {len(records)} existing TodayAccommodation records")
            return records
        except Exception as e:
            logger.error(f"Error fetching existing TodayAccommodation records: {str(e)}")
            return []


async def cleanup_outdated_today_accommodations(batch_date: date_obj) -> int:
    """
    updated_at 날짜가 배치 실행 일자와 다른 레코드 삭제
    """
    async with AsyncSessionLocal() as db:
        try:
            batch_date_str = batch_date.isoformat()
            stmt = delete(TodayAccommodation).where(
                or_(
                    TodayAccommodation.updated_at.is_(None),
                    func.date(TodayAccommodation.updated_at) != batch_date_str
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            deleted_rows = result.rowcount or 0
            logger.info(f"Cleanup completed - removed {deleted_rows} rows not matching {batch_date_str}")
            return deleted_rows
        except Exception as e:
            await db.rollback()
            logger.error(f"Error during cleanup for batch date {batch_date.isoformat()}: {str(e)}")
            raise


async def crawl_bookable_dates_for_accommodation(
    page: Page,
    accommodation_id: str
) -> List[Dict]:
    """
    특정 숙소의 신청가능한 날짜 크롤링

    Returns:
        List[Dict]: 날짜별 정보 리스트
        [
            {
                "date": "YYYY-MM-DD",
                "status": "신청가능",
                "score": float,
                "applicants": int
            }
        ]
    """
    try:
        acc_url = f"https://shbrefresh.interparkb2b.co.kr/condo/{accommodation_id}"
        logger.info(f"Crawling bookable dates for accommodation {accommodation_id}: {acc_url}")

        await page.goto(acc_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        bookable_dates = []

        logger.info(f"  Extracting bookable dates from calendar...")

        # calendar 클래스 또는 data-role="roomInfo" 요소 찾기
        room_info_elements = await page.query_selector_all('[data-role="roomInfo"]')

        if not room_info_elements:
            # 대안: calendar 클래스 내부에서 찾기
            calendars = await page.query_selector_all('.calendar, [class*="calendar"]')
            for calendar in calendars:
                room_info_elements.extend(await calendar.query_selector_all('[data-role="roomInfo"]'))

        logger.info(f"  Found {len(room_info_elements)} room info elements")

        for room_info in room_info_elements:
            try:
                # data-rblockdate 속성에서 날짜 추출
                date_str = await room_info.get_attribute("data-rblockdate")
                if not date_str:
                    continue

                # room_status 요소 찾기
                room_status_element = await room_info.query_selector(".room_status, [class*='room_status']")
                if not room_status_element:
                    room_status_element = room_info

                room_status_html = await room_status_element.inner_html()
                room_status_text = await room_status_element.inner_text()

                # 상태 확인 - 신청가능한 날짜만 추출
                status = "Unknown"
                is_bookable = False

                if "신청중" in room_status_text or "신청 중" in room_status_text or "신청가능" in room_status_text:
                    status = "신청중"
                    is_bookable = True
                elif "최초" in room_status_text and "실" in room_status_text:
                    status = "신청가능(최초 객실오픈)"
                    is_bookable = True
                elif "마감" not in room_status_text and "신청불가" not in room_status_text and "객실없음" not in room_status_text:
                    # 명시적으로 불가능하지 않으면 신청 가능으로 간주
                    if re.search(r'\d+\.?\d*\s*점', room_status_text) or re.search(r'\d+\s*명', room_status_text):
                        status = "신청가능(상시 신청중)"
                        is_bookable = True

                if not is_bookable:
                    continue

                # 최초 점수와 상시 점수를 data 속성에서 직접 추출 (가장 정확)
                choi_score = 0.0  # 최초 점수
                sangsi_score = 0.0  # 상시 점수

                # data-first-room-score 속성에서 최초 점수 추출
                first_score_attr = await room_info.get_attribute("data-first-room-score")
                if first_score_attr and first_score_attr.strip():
                    try:
                        choi_score = float(first_score_attr)
                    except:
                        pass

                # data-permanent-room-score 속성에서 상시 점수 추출
                permanent_score_attr = await room_info.get_attribute("data-permanent-room-score")
                if permanent_score_attr and permanent_score_attr.strip():
                    try:
                        sangsi_score = float(permanent_score_attr)
                    except:
                        pass

                # data 속성에서 추출 실패 시, HTML에서 파싱 시도 (fallback)
                if choi_score == 0.0 and sangsi_score == 0.0:
                    # <span>최초</span> 다음의 점수 추출
                    choi_match = re.search(r'<span[^>]*>최초</span>\s*\d+\s*실\s*-\s*(\d+\.?\d*)\s*점', room_status_html)
                    if choi_match:
                        choi_score = float(choi_match.group(1))

                    # <span>상시</span> 다음의 점수 추출
                    sangsi_match = re.search(r'<span[^>]*>상시</span>\s*\d+\s*실\s*-\s*(\d+\.?\d*)\s*점', room_status_html)
                    if sangsi_match:
                        sangsi_score = float(sangsi_match.group(1))

                    # <span>예상점수</span> 추출 (최초/상시가 없는 경우)
                    if choi_score == 0.0 and sangsi_score == 0.0:
                        expected_match = re.search(r'<span[^>]*>예상점수</span>\s*(\d+\.?\d*)', room_status_html)
                        if expected_match:
                            sangsi_score = float(expected_match.group(1))

                # 두 점수 중 더 높은 점수 선택
                score = max(choi_score, sangsi_score)

                # 인원 추출 (data 속성 우선, 없으면 HTML 파싱)
                applicants = 0
                apply_count_attr = await room_info.get_attribute("data-apply-count")
                if apply_count_attr and apply_count_attr.strip():
                    try:
                        applicants = int(apply_count_attr)
                    except:
                        pass

                # data 속성에서 추출 실패 시 HTML 파싱
                if applicants == 0:
                    applicants_patterns = [
                        r'<span[^>]*>신청인원</span>\s*(\d+)',
                        r'신청인원[\s:]*(\d+)',
                        r'(\d+)\s*명',
                    ]

                for pattern in applicants_patterns:
                    match = re.search(pattern, room_status_text)
                    if match:
                        applicants = int(match.group(1))
                        break

                bookable_dates.append({
                    "date": date_str,
                    "status": status,
                    "score": score,
                    "applicants": applicants
                })

                logger.info(f"    Found bookable date: {date_str} - {status}, {score}점 (최초: {choi_score}, 상시: {sangsi_score}), {applicants}명")

            except Exception as e:
                logger.debug(f"Error parsing room info: {str(e)}")
                continue

        logger.info(f"  Found {len(bookable_dates)} bookable dates for accommodation {accommodation_id}")
        return bookable_dates

    except Exception as e:
        logger.warning(f"Error crawling bookable dates for {accommodation_id}: {str(e)}")
        return []


async def crawl_realtime_info_for_date(
    page: Page,
    accommodation_id: str,
    target_date: str = None
) -> List[Dict]:
    """
    특정 숙소의 모든 예약 가능한 날짜에 대한 실시간 정보 크롤링

    Args:
        page: Playwright page object
        accommodation_id: 숙소 ID
        target_date: (Deprecated) 하위 호환성을 위해 유지, 사용되지 않음

    Returns:
        List[Dict]: 날짜별 정보 리스트
        [
            {
                "date": "YYYY-MM-DD",
                "status": str,
                "score": float,
                "applicants": int
            },
            ...
        ]
    """
    try:
        acc_url = f"https://shbrefresh.interparkb2b.co.kr/condo/{accommodation_id}"
        logger.info(f"Crawling all bookable dates for accommodation {accommodation_id}")

        await page.goto(acc_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        logger.info(f"  Looking for bookable dates using calendar_table and rm_always classes...")

        # calendar_table 클래스에서 rm_always 클래스 찾기
        calendar_table = await page.query_selector('.calendar_table, [class*="calendar_table"]')

        if not calendar_table:
            logger.warning("  calendar_table not found")
            return []

        rm_always_elements = await calendar_table.query_selector_all('.rm_always, [class*="rm_always"]')
        logger.info(f"  Found {len(rm_always_elements)} rm_always elements (bookable dates)")

        bookable_dates = []
        for rm_always in rm_always_elements:
            try:
                # rm_always 내부의 <a> 태그에서 data-rblockdate 추출
                link_element = await rm_always.query_selector('a')
                if not link_element:
                    logger.debug(f"    No <a> tag found in rm_always element")
                    continue

                date_str = await link_element.get_attribute("data-rblockdate")
                if not date_str:
                    continue

                # 날짜 발견!
                logger.info(f"    Processing date: {date_str}")

                # room_status 요소 찾기
                room_status_element = await rm_always.query_selector(".room_status, [class*='room_status']")
                if not room_status_element:
                    room_status_element = rm_always

                room_status_html = await room_status_element.inner_html()
                room_status_text = await room_status_element.inner_text()

                # 상태 추출
                status = "Unknown"
                if "신청중" in room_status_text or "신청 중" in room_status_text or "신청가능" in room_status_text:
                    status = "신청중"
                elif "최초" in room_status_text and "실" in room_status_text:
                    status = "신청가능(최초 객실오픈)"
                elif "마감" in room_status_text or "신청종료" in room_status_text:
                    status = "마감(신청종료)"
                elif "신청불가" in room_status_text:
                    status = "신청불가(오픈전)"
                elif "객실없음" in room_status_text:
                    status = "객실없음"

                # 최초 점수와 상시 점수를 data 속성에서 직접 추출 (가장 정확)
                choi_score = 0.0  # 최초 점수
                sangsi_score = 0.0  # 상시 점수

                # data-first-room-score 속성에서 최초 점수 추출
                first_score_attr = await link_element.get_attribute("data-first-room-score")
                if first_score_attr and first_score_attr.strip():
                    try:
                        choi_score = float(first_score_attr)
                    except:
                        pass

                # data-permanent-room-score 속성에서 상시 점수 추출
                permanent_score_attr = await link_element.get_attribute("data-permanent-room-score")
                if permanent_score_attr and permanent_score_attr.strip():
                    try:
                        sangsi_score = float(permanent_score_attr)
                    except:
                        pass

                # data 속성에서 추출 실패 시, HTML에서 파싱 시도 (fallback)
                if choi_score == 0.0 and sangsi_score == 0.0:
                    # <span>최초</span> 다음의 점수 추출
                    choi_match = re.search(r'<span[^>]*>최초</span>\s*\d+\s*실\s*-\s*(\d+\.?\d*)\s*점', room_status_html)
                    if choi_match:
                        choi_score = float(choi_match.group(1))

                    # <span>상시</span> 다음의 점수 추출
                    sangsi_match = re.search(r'<span[^>]*>상시</span>\s*\d+\s*실\s*-\s*(\d+\.?\d*)\s*점', room_status_html)
                    if sangsi_match:
                        sangsi_score = float(sangsi_match.group(1))

                    # <span>예상점수</span> 추출 (최초/상시가 없는 경우)
                    if choi_score == 0.0 and sangsi_score == 0.0:
                        expected_match = re.search(r'<span[^>]*>예상점수</span>\s*(\d+\.?\d*)', room_status_html)
                        if expected_match:
                            sangsi_score = float(expected_match.group(1))

                # 두 점수 중 더 높은 점수 선택
                score = max(choi_score, sangsi_score)

                # 인원 추출 (data 속성 우선, 없으면 HTML 파싱)
                applicants = 0
                apply_count_attr = await link_element.get_attribute("data-apply-count")
                if apply_count_attr and apply_count_attr.strip():
                    try:
                        applicants = int(apply_count_attr)
                    except:
                        pass

                # data 속성에서 추출 실패 시 HTML 파싱
                if applicants == 0:
                    applicants_patterns = [
                        r'<span[^>]*>신청인원</span>\s*(\d+)',
                        r'신청인원[\s:]*(\d+)',
                        r'(\d+)\s*명',
                    ]

                    for pattern in applicants_patterns:
                        match = re.search(pattern, room_status_text)
                        if match:
                            applicants = int(match.group(1))
                            break

                logger.info(f"    ✓ {date_str}: {status}, {score}점 (최초: {choi_score}, 상시: {sangsi_score}), {applicants}명")

                bookable_dates.append({
                    "date": date_str,
                    "status": status,
                    "score": score,
                    "applicants": applicants
                })

            except Exception as e:
                logger.debug(f"Error processing room info: {str(e)}")
                continue

        logger.info(f"  Found {len(bookable_dates)} bookable dates for accommodation {accommodation_id}")
        return bookable_dates

    except Exception as e:
        logger.warning(f"Error crawling realtime info for {accommodation_id}: {str(e)}")
        return []


async def save_today_accommodations_to_db(
    accommodation_id: str,
    dates_info: List[Dict]
) -> Tuple[int, int]:
    """
    오늘자 숙소 정보를 DB에 저장/업데이트
    """
    async with AsyncSessionLocal() as db:
        try:
            saved = 0
            updated = 0

            for date_info in dates_info:
                date_str = date_info["date"]

                # 날짜 파싱
                date_parts = date_str.split("-")
                year = int(date_parts[0])
                month = int(date_parts[1])
                day = int(date_parts[2])

                # 날짜 객체 생성
                try:
                    date_value = date_obj(year, month, day)
                    weekday = date_value.weekday()
                    week_number = date_value.isocalendar()[1]
                except ValueError:
                    logger.warning(f"Invalid date: {date_str}")
                    continue

                # TodayAccommodation ID 생성
                today_id = f"today_{accommodation_id}_{date_str}"

                # 기존 레코드 확인
                existing = await db.execute(
                    select(TodayAccommodation).where(TodayAccommodation.id == today_id)
                )
                existing_obj = existing.scalar_one_or_none()

                if existing_obj:
                    # 업데이트
                    existing_obj.applicants = date_info.get("applicants", 0)
                    existing_obj.score = date_info.get("score", 0.0)
                    existing_obj.status = date_info.get("status", "Unknown")
                    existing_obj.updated_at = datetime.utcnow()
                    db.add(existing_obj)
                    updated += 1
                else:
                    # 새로 생성
                    new_today = TodayAccommodation(
                        id=today_id,
                        year=year,
                        month=month,
                        day=day,
                        weekday=weekday,
                        week_number=week_number,
                        date=date_str,
                        accommodation_id=accommodation_id,
                        applicants=date_info.get("applicants", 0),
                        score=date_info.get("score", 0.0),
                        status=date_info.get("status", "Unknown"),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_today)
                    saved += 1

            await db.commit()
            logger.info(f"  DB save - Saved: {saved}, Updated: {updated}")
            return saved, updated

        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving to database: {str(e)}")
            raise


async def process_today_accommodation_realtime(
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Dict:
    """
    오늘자 숙소 실시간 정보 갱신 메인 함수
    """
    # 설정에서 로드
    if username is None:
        username = settings.LULU_LALA_USERNAME
    if password is None:
        password = settings.LULU_LALA_PASSWORD

    if not username or not password:
        error_msg = (
            "로그인 정보가 설정되지 않았습니다. "
            ".env 파일에 LULU_LALA_USERNAME과 LULU_LALA_PASSWORD를 설정하세요."
        )
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

    rsa_public_key = settings.LULU_LALA_RSA_PUBLIC_KEY
    if not rsa_public_key:
        error_msg = (
            "RSA 공개키가 설정되지 않았습니다. "
            ".env 파일에 LULU_LALA_RSA_PUBLIC_KEY를 설정하세요."
        )
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

    batch_date = datetime.utcnow().date()
    batch_date_str = batch_date.isoformat()

    async with async_playwright() as p:
        browser: Browser = None
        context: BrowserContext = None
        page: Page = None

        try:
            logger.info("=" * 60)
            logger.info("Starting today accommodation realtime update batch job...")
            logger.info("=" * 60)

            # Cleanup outdated data before loading new ones
            logger.info("=" * 60)
            logger.info(f"STEP 0: Cleaning up data not updated on {batch_date_str} ...")
            logger.info("=" * 60)
            cleaned_rows = await cleanup_outdated_today_accommodations(batch_date)
            logger.info(f"✓ Cleanup complete. Removed {cleaned_rows} stale rows.")

            # 브라우저 시작
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # 로그인
            logger.info("=" * 60)
            logger.info("STEP 1: Logging in to lulu-lala...")
            logger.info("=" * 60)
            login_success = await login_to_lulu_lala(page, username, password, rsa_public_key)
            if not login_success:
                return {
                    "status": "error",
                    "message": "Login failed",
                    "step": "login",
                    "timestamp": datetime.utcnow().isoformat()
                }

            logger.info("✓ Login successful")

            # Reservation 페이지로 이동
            logger.info("=" * 60)
            logger.info("STEP 2: Navigating to reservation page...")
            logger.info("=" * 60)
            nav_success, page = await navigate_to_reservation_page(page, context)
            if not nav_success:
                return {
                    "status": "error",
                    "message": "Failed to navigate to reservation page",
                    "step": "navigation",
                    "timestamp": datetime.utcnow().isoformat()
                }

            logger.info(f"✓ Successfully navigated to: {page.url}")

            # 명시적으로 /index URL로 이동
            logger.info(f"Navigating to index page: {SHB_REFRESH_INDEX_URL}")
            await page.goto(SHB_REFRESH_INDEX_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            logger.info(f"✓ Successfully navigated to index page: {page.url}")

            # 처리할 숙소/날짜 결정
            total_processed = 0
            total_saved = 0
            total_updated = 0

            logger.info("=" * 60)
            logger.info(f"STEP 3: Crawling realtime info for batch date {batch_date_str}")
            logger.info("=" * 60)

            accommodation_ids = await get_all_accommodation_ids()

            if not accommodation_ids:
                logger.warning("No accommodations found in database")
                return {
                    "status": "warning",
                    "message": "No accommodations found",
                    "timestamp": datetime.utcnow().isoformat(),
                    "batch_date": batch_date_str,
                    "cleaned_rows": cleaned_rows
                }

            logger.info(f"Processing {len(accommodation_ids)} accommodations for {batch_date_str}...")

            for idx, acc_id in enumerate(accommodation_ids, 1):
                logger.info(f"[{idx}/{len(accommodation_ids)}] Processing accommodation {acc_id}")

                try:
                    dates_info = await crawl_realtime_info_for_date(page, acc_id)

                    if dates_info:
                        saved, updated = await save_today_accommodations_to_db(acc_id, dates_info)
                        total_processed += 1
                        total_saved += saved
                        total_updated += updated
                    else:
                        logger.info(f"  No bookable dates found for accommodation {acc_id}")

                    # 과부하 방지를 위한 짧은 대기
                    await page.wait_for_timeout(1000)

                except Exception as e:
                    logger.warning(f"Error processing accommodation {acc_id}: {str(e)}")
                    continue

            logger.info(
                f"Crawl completed for {batch_date_str}: "
                f"{total_processed} accommodations, saved {total_saved}, updated {total_updated}"
            )

            # SOL점수 계산 및 업데이트
            logger.info("=" * 50)
            logger.info("Calculating SOL scores for today accommodations...")
            logger.info("=" * 50)
            async with AsyncSessionLocal() as db:
                sol_stats = await calculate_sol_scores_for_today_accommodation(db)
                logger.info(f"✓ SOL score calculation completed:")
                logger.info(f"  - Total records: {sol_stats['total']}")
                logger.info(f"  - Calculated: {sol_stats['calculated']}")
                logger.info(f"  - Skipped: {sol_stats['skipped']}")

            return {
                "status": "success",
                "mode": "daily",
                "batch_date": batch_date_str,
                "cleaned_rows": cleaned_rows,
                "accommodations_processed": total_processed,
                "dates_saved": total_saved,
                "dates_updated": total_updated,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Batch job failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()


def handler(event, context):
    """AWS Lambda 핸들러"""
    try:
        result = asyncio.run(process_today_accommodation_realtime())
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }
