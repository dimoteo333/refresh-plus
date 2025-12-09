"""
숙소 날짜별 온라인 가격 크롤링 배치 작업
- accommodation_dates 테이블의 내일 이후 날짜에 대해 네이버 호텔에서 가격 크롤링
- 네이버 호텔 ID를 우선 사용하여 상세 페이지에서 가격 조회 (없으면 자동검색 폴백)
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.accommodation import Accommodation
from app.models.accommodation_date import AccommodationDate
from app.batch.naver_hotel_price import search_hotel_price_on_naver
from app.utils.logger import get_logger
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = get_logger(__name__)

def _adult_count_from_capacity(capacity: Optional[int]) -> int:
    try:
        return max(1, int(capacity)) if capacity is not None else 2
    except (TypeError, ValueError):
        return 2


async def get_accommodation_dates_to_update() -> List[Dict]:
    """
    내일 이후의 날짜를 가진 accommodation_dates 레코드 가져오기
    """
    async with AsyncSessionLocal() as db:
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            tomorrow_str = tomorrow.isoformat()

            logger.info(f"Fetching accommodation_dates records from {tomorrow_str} onwards...")

            result = await db.execute(
                select(
                    AccommodationDate.id,
                    AccommodationDate.accommodation_id,
                    AccommodationDate.date,
                    Accommodation.name,
                    Accommodation.accommodation_type,
                    Accommodation.naver_hotel_id,
                    Accommodation.capacity,
                )
                .join(Accommodation, AccommodationDate.accommodation_id == Accommodation.id)
                .where(
                    (AccommodationDate.date >= tomorrow_str) &
                    (Accommodation.naver_hotel_id.isnot(None)) &  # 네이버 호텔 ID가 있는 것만
                    (AccommodationDate.online_price.is_(None))  # 가격이 아직 업데이트되지 않은 것만
                )
                .order_by(AccommodationDate.date)
            )

            records = []
            for row in result.fetchall():
                records.append({
                    "date_id": row[0],
                    "accommodation_id": row[1],
                    "date": row[2],
                    "accommodation_name": row[3],
                    "room_type": row[4],
                    "naver_hotel_id": row[5],
                    "capacity": row[6],
                })

            logger.info(f"Found {len(records)} accommodation_dates records to process")
            logger.info(f"  (Filtered: naver_hotel_id IS NOT NULL AND online_price IS NULL)")
            return records

        except Exception as e:
            logger.error(f"Error fetching accommodation_dates records: {str(e)}")
            return []


async def update_online_price_in_db(date_id: str, online_price: float) -> bool:
    """
    accommodation_dates 테이블의 online_price 업데이트
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(AccommodationDate).where(AccommodationDate.id == date_id)
            )
            record = result.scalar_one_or_none()

            if record:
                if record.online_price is not None:
                    logger.info(f"  Skipping {date_id}: online_price already set")
                    return False

                record.online_price = online_price
                record.updated_at = datetime.utcnow()
                db.add(record)
                await db.commit()
                logger.debug(f"  Updated online_price: ₩{online_price:,.0f}")
                return True
            else:
                logger.warning(f"  AccommodationDate record not found: {date_id}")
                return False

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating online_price for {date_id}: {str(e)}")
            raise


async def process_accommodation_dates_price_crawler() -> Dict:
    """
    숙소 날짜별 온라인 가격 크롤링 메인 함수
    """
    async with async_playwright() as p:
        browser: Browser = None
        context: BrowserContext = None
        page: Page = None

        try:
            logger.info("=" * 60)
            logger.info("Starting accommodation dates price crawler batch job...")
            logger.info("Using Naver Hotel (hotel.naver.com)")
            logger.info("=" * 60)

            records = await get_accommodation_dates_to_update()

            if not records:
                logger.warning("No accommodation_dates records to process")
                return {
                    "status": "warning",
                    "message": "No records to process",
                    "timestamp": datetime.utcnow().isoformat()
                }

            logger.info("Launching browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',  # Docker/메모리 제한 환경 최적화
                    '--no-sandbox',  # Docker 환경 호환성
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="ko-KR"
            )
            page = await context.new_page()

            total_processed = 0
            total_updated = 0
            total_failed = 0
            total_skipped = 0

            # 같은 숙소/날짜/타입에 대한 중복 크롤링 방지
            price_cache = {}

            for idx, record in enumerate(records, 1):
                logger.info(f"[{idx}/{len(records)}] Processing {record['accommodation_name']} on {record['date']}")

                try:
                    if not record.get("naver_hotel_id"):
                        logger.info("  Skipping: naver_hotel_id is missing")
                        total_skipped += 1
                        total_processed += 1
                        continue

                    check_in_date = record['date']
                    check_in = datetime.strptime(check_in_date, "%Y-%m-%d").date()
                    check_out = check_in + timedelta(days=1)
                    check_out_date = check_out.isoformat()
                    adult_cnt = _adult_count_from_capacity(record.get("capacity"))

                    # 캐시 확인
                    cache_key = (
                        f"{record.get('naver_hotel_id') or record['accommodation_name']}"
                        f"|{record.get('room_type') or ''}|{check_in_date}|{adult_cnt}"
                    )
                    if cache_key in price_cache:
                        price = price_cache[cache_key]
                        logger.info(f"  ✓ Using cached price: ₩{price:,.0f}")
                    else:
                        # 네이버 호텔에서 가격 검색
                        price = await search_hotel_price_on_naver(
                            page,
                            record['accommodation_name'],
                            record['room_type'],
                            check_in_date,
                            check_out_date,
                            naver_hotel_id=record.get("naver_hotel_id"),
                            capacity=adult_cnt,
                        )

                        if price:
                            price_cache[cache_key] = price

                    if price:
                        updated = await update_online_price_in_db(record['date_id'], price)
                        if updated:
                            total_updated += 1
                        else:
                            total_skipped += 1
                    else:
                        total_failed += 1

                    total_processed += 1

                    # 과부하 방지
                    await page.wait_for_timeout(2000)

                except Exception as e:
                    logger.warning(f"Error processing record {record['date_id']}: {str(e)}")
                    total_failed += 1
                    continue

            logger.info("=" * 60)
            logger.info(f"Batch job completed:")
            logger.info(f"  Total processed: {total_processed}")
            logger.info(f"  Successfully updated: {total_updated}")
            logger.info(f"  Skipped: {total_skipped}")
            logger.info(f"  Failed: {total_failed}")
            logger.info(f"  Cache hits: {len(price_cache)}")
            logger.info("=" * 60)

            return {
                "status": "success",
                "total_processed": total_processed,
                "total_updated": total_updated,
                "total_skipped": total_skipped,
                "total_failed": total_failed,
                "cache_hits": len(price_cache),
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
        result = asyncio.run(process_accommodation_dates_price_crawler())
        return {
            "statusCode": 200,
            "body": result
        }
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "message": str(e)
            }
        }
