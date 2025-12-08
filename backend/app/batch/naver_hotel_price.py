import json
import re
from datetime import datetime, timedelta
from typing import List, Optional

from playwright.async_api import Page

from app.utils.logger import get_logger

logger = get_logger(__name__)

# hotels.naver.com 사용 (검색 → CID 추출 → 상세 URL 진입)
NAVER_HOTEL_BASE_URL = "https://hotels.naver.com"
NAVER_HOTEL_SEARCH_URL = NAVER_HOTEL_BASE_URL
HOTEL_DETAIL_URL_TEMPLATE = (
    NAVER_HOTEL_BASE_URL
    + "/detail/hotels/{cid}?rateTab=&placeId=detail&checkIn={check_in}&checkOut={check_out}"
    + "&adultCnt={adult_cnt}&childAges=&dChildAges="
)
INFO_PRICE_SELECTOR = '[class^="Info_Info__"] [class^="common_price__"]'

# 가격 추출 패턴/셀렉터
PRICE_SELECTORS = [
    '[class*="price"]',
    '[class*="Price"]',
    '[class*="amount"]',
    '[class*="Amount"]',
    '[data-testid*="price"]',
    '[aria-label*="가격"]',
    '[class*="pay"]',
    '[class*="Sale"]',
]
PRICE_PATTERNS = [
    r"₩\s*([\d,]+)",
    r"([\d,]+)\s*원",
    r"최저\s*([\d,]+)",
    r"1박당\s*([\d,]+)",
]
MIN_PRICE = 10_000
MAX_PRICE = 10_000_000


def _normalize_prices(text: str) -> List[float]:
    if not text:
        return []

    prices: List[float] = []
    for pattern in PRICE_PATTERNS:
        for match in re.findall(pattern, text):
            try:
                value = float(str(match).replace(",", "").strip())
                if MIN_PRICE <= value <= MAX_PRICE:
                    prices.append(value)
            except ValueError:
                continue
    return prices


async def _find_hotel_cid(page: Page, search_query: str, search_terms: List[str]) -> Optional[str]:
    """
    hotels.naver.com 검색창에 입력 후, 자동완성 결과에서 호텔 CID 추출.
    """
    try:
        await page.goto(NAVER_HOTEL_SEARCH_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(800)
    except Exception as nav_err:
        logger.warning(f"Naver Hotel search page navigation failed: {nav_err}")
        return None

    # 검색어 입력
    try:
        search_input = await page.wait_for_selector('input.Autocomplete_input_txt__2PCxj', timeout=7000)
        await search_input.fill(search_query)
        await page.wait_for_timeout(700)
    except Exception as input_err:
        logger.warning(f"Failed to fill search box on Naver Hotel: {input_err}")
        return None

    # 결과 대기
    try:
        await page.wait_for_selector('div.SearchResults_anchor__xQQnN.hotel_imp', timeout=7000)
    except Exception:
        logger.warning("No search results appeared on Naver Hotel")
        return None

    lowered_terms = [t.lower() for t in search_terms if t]
    best_cid: Optional[str] = None
    best_score = -1

    try:
        candidates = await page.query_selector_all('div.SearchResults_anchor__xQQnN.hotel_imp')
    except Exception:
        candidates = []

    for candidate in candidates:
        cid: Optional[str] = None
        score = 0

        try:
            raw_attr = await candidate.get_attribute("data-nlog-imp-logs")
            if raw_attr:
                # HTML 엔티티 정리 후 JSON 파싱
                cleaned = raw_attr.replace("&quot;", '"')
                parsed = json.loads(cleaned)
                cid = (
                    parsed.get("cid")
                    or parsed.get("hotel", {}).get("cid")
                    or parsed.get("hotel", {}).get("hotelId")
                )
        except Exception:
            cid = None

        try:
            text = (await candidate.inner_text()) or ""
            score = sum(1 for term in lowered_terms if term in text.lower())
        except Exception:
            pass

        if cid and score >= best_score:
            best_cid = cid
            best_score = score

    if best_cid:
        logger.info(f"  ✓ Found Naver Hotel CID: {best_cid} (score={best_score})")
    else:
        logger.warning("No CID extracted from Naver Hotel search results")

    return best_cid


def _build_detail_url(cid: str, check_in_date: str, check_out_date: str, adult_cnt: int = 2) -> str:
    return HOTEL_DETAIL_URL_TEMPLATE.format(
        cid=cid,
        check_in=check_in_date,
        check_out=check_out_date,
        adult_cnt=adult_cnt,
    )


def _ensure_check_out_date(check_in_date: str, check_out_date: Optional[str]) -> str:
    """
    Ensure check-out date is always check-in + 1 day.
    """
    try:
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d").date()
        expected = (check_in + timedelta(days=1)).isoformat()
    except Exception:
        # Fallback to provided values if parsing fails
        return check_out_date or check_in_date

    if check_out_date and check_out_date != expected:
        logger.debug(
            f"Adjusting check-out date to check-in+1. "
            f"received={check_out_date}, expected={expected}"
        )
    return expected


def _sanitize_adult_count(capacity: Optional[int]) -> int:
    """
    Convert capacity to a valid adult count for Naver Hotel URL.
    """
    try:
        adults = int(capacity) if capacity is not None else 2
    except (ValueError, TypeError):
        adults = 2

    return max(1, adults)


def _pick_lowest_price(prices: List[float]) -> Optional[float]:
    unique_prices = sorted(set(price for price in prices if MIN_PRICE <= price <= MAX_PRICE))
    if unique_prices:
        return unique_prices[0]
    return None


async def _wait_for_info_price_block(page: Page) -> None:
    """
    Wait until the info section (Info_Info__*) and its price block (common_price__*)
    are rendered. This section sometimes appears after initial load.
    """
    try:
        await page.wait_for_selector(INFO_PRICE_SELECTOR, timeout=10000)
        await page.wait_for_timeout(500)
    except Exception:
        logger.debug("Info price block did not appear within timeout; using fallbacks.")


async def _extract_price_from_info_block(page: Page) -> List[float]:
    """
    Extract price specifically from the Info_Info__* / common_price__* section.
    """
    prices: List[float] = []
    try:
        info_blocks = await page.query_selector_all('[class^="Info_Info__"]')
    except Exception:
        return prices

    for block in info_blocks:
        try:
            price_el = await block.query_selector('[class^="common_price__"]')
            if not price_el:
                continue

            text = await price_el.inner_text()
            prices.extend(_normalize_prices(text))

            for attr_name in ("data-price", "data-amount", "data-value"):
                attr = await price_el.get_attribute(attr_name)
                if attr:
                    prices.extend(_normalize_prices(attr))
        except Exception:
            continue

    return prices


async def _extract_prices_from_elements(page: Page) -> List[float]:
    prices: List[float] = []

    for selector in PRICE_SELECTORS:
        try:
            elements = await page.query_selector_all(selector)
        except Exception:
            continue

        for element in elements:
            try:
                text = await element.inner_text()
                prices.extend(_normalize_prices(text))

                for attr_name in ("data-price", "data-amount", "data-value"):
                    attr = await element.get_attribute(attr_name)
                    if attr:
                        prices.extend(_normalize_prices(attr))
            except Exception:
                continue

    return prices


async def _extract_price_from_body(page: Page) -> List[float]:
    try:
        body_text = await page.inner_text("body")
        return _normalize_prices(body_text)
    except Exception:
        return []


async def search_hotel_price_on_naver(
    page: Page,
    accommodation_name: str,
    room_type: Optional[str],
    check_in_date: str,
    check_out_date: str,
    naver_hotel_id: Optional[str] = None,
    capacity: Optional[int] = None,
) -> Optional[float]:
    """
    주어진 Naver 호텔 ID로 상세 페이지 진입 후 최저가 추출.
    - ID가 없으면 기존 자동완성 검색 → CID 추출 로직으로 폴백.
    """
    query_parts = [accommodation_name.strip()]
    if room_type:
        query_parts.append(room_type.strip())

    check_out_date = _ensure_check_out_date(check_in_date, check_out_date)
    adult_cnt = _sanitize_adult_count(capacity)
    search_query = " ".join(part for part in query_parts if part)
    logger.info(
        f"Searching Naver Hotel for '{search_query}' "
        f"({check_in_date} -> {check_out_date}, adults={adult_cnt})"
    )

    # 1) ID가 있으면 바로 사용, 없으면 검색으로 CID 추출
    cid = (naver_hotel_id or "").strip() or None
    if cid:
        logger.info(f"  ✓ Using provided Naver Hotel ID: {cid}")
    else:
        cid = await _find_hotel_cid(page, search_query, query_parts)
        if not cid:
            return None

    # 2) 상세 URL 구성 (체크아웃 = 체크인 + 1일 자동 계산됨)
    detail_url = _build_detail_url(cid, check_in_date, check_out_date, adult_cnt=adult_cnt)
    logger.debug(f"Naver Hotel detail URL: {detail_url}")

    try:
        await page.goto(detail_url, wait_until="networkidle", timeout=35000)
        await page.wait_for_timeout(1500)
        await _wait_for_info_price_block(page)
    except Exception as nav_error:
        logger.warning(f"Naver Hotel detail navigation failed for CID {cid}: {nav_error}")
        return None

    prices = await _extract_price_from_info_block(page)
    if not prices:
        prices = await _extract_prices_from_elements(page)
    if not prices:
        prices = await _extract_price_from_body(page)

    price = _pick_lowest_price(prices)
    if price:
        logger.info(f"  ✓ Naver Hotel price found: ₩{price:,.0f}")
    else:
        logger.warning(f"  ⚠️  No Naver Hotel price found for {search_query}")

    return price
