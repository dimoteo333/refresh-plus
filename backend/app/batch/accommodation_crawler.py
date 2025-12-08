"""
숙소 정보 크롤링 배치 작업
- lulu-lala.zzzmobile.co.kr에 로그인
- shbrefresh.interparkb2b.co.kr/intro로 이동하여 숙소 정보 크롤링
- DB에 저장
"""

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from urllib.parse import urljoin
from typing import List, Dict, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.accommodation import Accommodation
from app.models.accommodation_date import AccommodationDate
from app.models.today_accommodation import TodayAccommodation
from app.config import settings
from app.utils.logger import get_logger
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64

logger = get_logger(__name__)


@dataclass
class LoginTimingProfile:
    """Playwright 대기 시간을 조절하기 위한 프로파일"""

    preload_delay_ms: int = 2000
    login_func_wait_ms: int = 2000
    post_submit_wait_ms: int = 5000
    final_settle_wait_ms: int = 3000
    nav_poll_interval_ms: int = 1000
    max_nav_wait_seconds: int = 30
    reservation_pre_click_ms: int = 2000
    post_reservation_click_ms: int = 3000


STABLE_LOGIN_TIMING = LoginTimingProfile()
FAST_LOGIN_TIMING = LoginTimingProfile(
    preload_delay_ms=700,
    login_func_wait_ms=600,
    post_submit_wait_ms=2000,
    final_settle_wait_ms=500,
    nav_poll_interval_ms=400,
    max_nav_wait_seconds=12,
    reservation_pre_click_ms=700,
    post_reservation_click_ms=1200,
)

# 로그인 URL
LULU_LALA_LOGIN_URL = "https://lulu-lala.zzzmobile.co.kr/login.html"
# 숙소 조회 URL
SHB_REFRESH_INTRO_URL = "https://shbrefresh.interparkb2b.co.kr/intro"
SHB_REFRESH_INDEX_URL = "https://shbrefresh.interparkb2b.co.kr/index"
SHB_DIRECT_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def _extract_shbrefresh_urls_from_blob(blob: str) -> List[str]:
    """Pull shbrefresh/interpark URLs from a string fragment."""
    if not blob:
        return []

    normalized = unescape(blob)
    normalized = normalized.replace("\\/", "/").replace("\\u002F", "/")
    urls: List[str] = []

    for match in SHB_DIRECT_URL_PATTERN.findall(normalized):
        cleaned = match.strip().rstrip("');, ")
        lowered = cleaned.lower()
        if "shbrefresh" in lowered or "interparkb2b" in lowered:
            if cleaned not in urls:
                urls.append(cleaned)

    return urls


async def _collect_shbrefresh_link_candidates(element) -> List[str]:
    """Inspect the DOM node for any embedded shbrefresh URLs."""
    fragments: List[str] = []
    try:
        attributes = await element.evaluate(
            "(el) => { const attrs = {}; for (const attr of el.attributes) { attrs[attr.name] = attr.value; } return attrs; }"
        )
        if isinstance(attributes, dict):
            fragments.extend([str(value) for value in attributes.values() if value])
    except Exception:
        pass

    for getter in ("inner_html", "text_content"):
        try:
            value = await getattr(element, getter)()
            if value:
                fragments.append(value)
        except Exception:
            continue

    urls: List[str] = []
    for fragment in fragments:
        for url in _extract_shbrefresh_urls_from_blob(fragment):
            if url not in urls:
                urls.append(url)

    return urls


async def _collect_page_shbrefresh_urls(page: Page) -> List[str]:
    """Extract shbrefresh/interpark URLs from the entire page content."""
    try:
        html = await page.content()
    except Exception as content_error:
        logger.debug(f"Failed to read page content for shbrefresh discovery: {content_error}")
        return []

    return _extract_shbrefresh_urls_from_blob(html)


async def _find_active_refresh_sso_href(page: Page) -> Optional[str]:
    """Locate the Refresh SSO link under swiper slides without extra waits."""

    # 페이지가 완전히 로드될 때까지 대기
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except:
        pass

    # 추가 안정화 대기 (동적 콘텐츠 로딩을 위해)
    await page.wait_for_timeout(3000)

    # iframe 확인
    frames = page.frames
    logger.info(f"Total frames on page: {len(frames)}")
    for idx, frame in enumerate(frames):
        try:
            frame_url = frame.url
            logger.info(f"  Frame {idx}: {frame_url}")
        except:
            pass

    # 방법 1: 특정 선택자로 찾기
    selectors = [
        "a[href*='vservice.html'][href*='sh_gmidas']",
        "a[href*='vservice'][href*='sh_gmidas']",
        "li.swiper-slide.swiper-slide-active a[href*='vservice']",
        "li.swiper-slide a[href*='vservice'][href*='sh_gmidas']",
        "a[href*='client_id=sh_gmidas']",
        "a[href*='shbrefresh']",
    ]

    for selector in selectors:
        try:
            anchor = await page.query_selector(selector)
            if anchor:
                href = await anchor.get_attribute("href")
                if href and ("vservice" in href or "sh_gmidas" in href or "shbrefresh" in href):
                    full_href = urljoin(page.url, href)
                    logger.info(f"Found Refresh SSO link via selector {selector}: {full_href}")
                    return full_href
        except Exception as selector_error:
            logger.debug(f"Selector {selector} did not resolve Refresh SSO link: {selector_error}")

    # 방법 2: JavaScript로 페이지와 iframe의 모든 링크 검색
    try:
        logger.info("Searching all links on page and iframes for SSO URL...")

        # 메인 페이지에서 링크 검색
        all_hrefs = []
        try:
            main_hrefs = await page.evaluate(
                """() => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(a => ({
                        href: a.getAttribute('href'),
                        text: a.innerText || '',
                        className: a.className || '',
                        source: 'main'
                    }));
                }"""
            )
            all_hrefs.extend(main_hrefs or [])
            logger.info(f"Links found on main page: {len(main_hrefs or [])}")
        except Exception as e:
            logger.debug(f"Error searching main page: {e}")

        # 각 iframe에서 링크 검색
        for idx, frame in enumerate(frames):
            try:
                frame_hrefs = await frame.evaluate(
                    """() => {
                        const links = Array.from(document.querySelectorAll('a[href]'));
                        return links.map(a => ({
                            href: a.getAttribute('href'),
                            text: a.innerText || '',
                            className: a.className || ''
                        }));
                    }"""
                )
                if frame_hrefs:
                    for link in frame_hrefs:
                        link['source'] = f'iframe_{idx}'
                    all_hrefs.extend(frame_hrefs)
                    logger.info(f"Links found in iframe {idx}: {len(frame_hrefs)}")
            except Exception as e:
                logger.debug(f"Error searching iframe {idx}: {e}")

        logger.info(f"Total links found (all sources): {len(all_hrefs)}")

        # shbrefresh 또는 sh_gmidas 관련 링크만 출력 (디버깅용)
        refresh_related_links = []
        for link_info in all_hrefs:
            href = link_info.get('href', '')
            if any(keyword in href.lower() for keyword in ['shbrefresh', 'sh_gmidas', 'refresh', 'gmidas']):
                refresh_related_links.append(link_info)

        logger.info(f"Refresh-related links found: {len(refresh_related_links)}")
        for idx, link_info in enumerate(refresh_related_links[:10], 1):
            href = link_info.get('href', '')
            text = link_info.get('text', '')[:30]
            source = link_info.get('source', 'unknown')
            logger.info(f"  Refresh Link {idx} [{source}]:")
            logger.info(f"    URL: {href}")
            logger.info(f"    Text: {text}")

        # SSO 링크 패턴 매칭 - sh_gmidas를 포함하는 링크 우선
        best_match = None
        best_score = 0

        for link_info in all_hrefs:
            href = link_info.get('href', '')
            if not href:
                continue

            score = 0
            # sh_gmidas를 포함하면 가장 높은 점수
            if 'sh_gmidas' in href:
                score += 100
            # shbrefresh를 포함하면 추가 점수
            if 'shbrefresh' in href.lower():
                score += 50
            # vservice.html을 포함하면 기본 점수
            if 'vservice.html' in href:
                score += 10

            if score > best_score:
                best_score = score
                best_match = link_info

        if best_match:
            href = best_match.get('href', '')
            full_href = urljoin(page.url, href)
            logger.info(f"✓ Found Refresh SSO link via JavaScript scan (score: {best_score}): {full_href}")
            logger.info(f"  Link text: {best_match.get('text', '')[:50]}")
            logger.info(f"  Link source: {best_match.get('source', 'unknown')}")
            return full_href

    except Exception as eval_error:
        logger.warning(f"JavaScript link scan failed: {eval_error}")

    # 방법 3: 페이지 HTML 전체에서 URL 패턴 추출
    try:
        logger.info("Extracting SSO URLs from page HTML...")
        page_content = await page.content()

        # vservice.html을 포함하는 URL 패턴 찾기
        import re
        url_pattern = re.compile(r'(https?://[^\s"\'<>]+vservice\.html[^\s"\'<>]*)')
        matches = url_pattern.findall(page_content)

        for match in matches:
            if 'sh_gmidas' in match or 'shbrefresh' in match:
                # HTML 엔티티 디코딩
                from html import unescape
                decoded_url = unescape(match)
                logger.info(f"Found Refresh SSO link via HTML pattern: {decoded_url}")
                return decoded_url

    except Exception as html_error:
        logger.debug(f"HTML pattern extraction failed: {html_error}")

    logger.warning("Could not find Refresh SSO link using any method")
    return None


async def _open_refresh_sso_in_new_tab(
    page: Page,
    context: BrowserContext,
    timing_profile: LoginTimingProfile,
) -> tuple[bool, Optional[Page]]:
    """Open the active Refresh SSO link in a fresh tab and drive it to the index page."""
    sso_href = await _find_active_refresh_sso_href(page)
    if not sso_href:
        logger.warning("Could not locate Refresh SSO link on active swiper slide")
        return False, None

    logger.info(f"Opening Refresh SSO link in new tab: {sso_href}")
    sso_page = await context.new_page()

    try:
        await sso_page.goto(sso_href, wait_until="networkidle", timeout=20000)
    except Exception as nav_error:
        logger.error(f"Failed to open Refresh SSO link: {nav_error}")
        try:
            await sso_page.close()
        except Exception:
            pass
        return False, None

    if timing_profile.reservation_pre_click_ms:
        await sso_page.wait_for_timeout(timing_profile.reservation_pre_click_ms)

    intro_loaded = "intro" in sso_page.url.lower()
    success = await _ensure_intro_then_index(
        sso_page,
        timing_profile,
        intro_already_loaded=intro_loaded,
    )

    if success:
        return True, sso_page

    logger.warning("Refresh SSO tab did not complete navigation to index, closing tab")
    try:
        await sso_page.close()
    except Exception:
        pass
    return False, None


async def _ensure_intro_then_index(
    page: Page,
    timing_profile: LoginTimingProfile,
    intro_already_loaded: bool = False,
) -> bool:
    """Guarantee the Intro -> Index navigation sequence to preserve SSO state."""
    try:
        if not intro_already_loaded:
            logger.info("Loading shbrefresh intro page to seed session cookies...")
            await page.goto(SHB_REFRESH_INTRO_URL, wait_until="networkidle")
            if timing_profile.reservation_pre_click_ms:
                await page.wait_for_timeout(timing_profile.reservation_pre_click_ms)

        logger.info("Navigating to shbrefresh reservation index page...")
        await page.goto(SHB_REFRESH_INDEX_URL, wait_until="networkidle")
        if timing_profile.post_reservation_click_ms:
            await page.wait_for_timeout(timing_profile.post_reservation_click_ms)

        logger.info(f"Reached reservation index page: {page.url}")
        return True
    except Exception as transition_error:
        logger.error(f"Failed during intro/index transition: {transition_error}")
        return False


async def _attempt_direct_link_navigation(
    context: BrowserContext,
    candidate_urls: List[str],
    timing_profile: LoginTimingProfile,
) -> Optional[Page]:
    """Try opening extracted shbrefresh URLs in isolation before falling back."""
    for candidate in candidate_urls:
        candidate_page = await context.new_page()
        logger.info(f"Trying direct Refresh link navigation: {candidate}")
        success = False
        try:
            await candidate_page.goto(candidate, wait_until="networkidle")
            intro_loaded = "intro" in candidate_page.url.lower()
            success = await _ensure_intro_then_index(
                candidate_page,
                timing_profile,
                intro_already_loaded=intro_loaded,
            )
            if success:
                return candidate_page
        except Exception as direct_error:
            logger.warning(f"Direct link navigation failed for {candidate}: {direct_error}")
        finally:
            if not success and not candidate_page.is_closed():
                await candidate_page.close()

    return None


def encrypt_rsa(plaintext: str, public_key_pem: str) -> str:
    """
    RSA 공개키로 텍스트 암호화
    """
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        import base64
        
        key = RSA.import_key(public_key_pem)
        cipher = PKCS1_v1_5.new(key)
        encrypted = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        logger.error(f"RSA encryption failed: {str(e)}")
        raise


async def login_to_lulu_lala(
    page: Page,
    username: str,
    password: str,
    rsa_public_key: str,
    timing: LoginTimingProfile | None = None
) -> bool:
    """
    lulu-lala 웹사이트에 로그인
    
    Args:
        page: Playwright Page 객체
        username: 로그인 사용자명
        password: 로그인 비밀번호
        rsa_public_key: RSA 공개키
    
    Returns:
        bool: 로그인 성공 여부
    """
    try:
        timing_profile = timing or STABLE_LOGIN_TIMING

        logger.info(f"Navigating to login page: {LULU_LALA_LOGIN_URL}")
        await page.goto(LULU_LALA_LOGIN_URL, wait_until="networkidle")
        if timing_profile.preload_delay_ms:
            await page.wait_for_timeout(timing_profile.preload_delay_ms)
        
        # 입력 필드 찾기
        username_input = page.locator('input#username')
        password_input = page.locator('input#password')
        
        # RSA 암호화
        encrypted_username = encrypt_rsa(username, rsa_public_key)
        encrypted_password = encrypt_rsa(password, rsa_public_key)
        
        logger.info("Filling login form...")
        await username_input.fill(username)
        await password_input.fill(password)

        # JavaScript의 login 함수를 직접 호출 (test_crawler_standalone.py와 동일한 방식)
        if timing_profile.login_func_wait_ms:
            try:
                await page.wait_for_function(
                    "typeof login === 'function'",
                    timeout=timing_profile.login_func_wait_ms
                )
            except Exception:
                await page.wait_for_timeout(min(500, timing_profile.login_func_wait_ms))

        try:
            login_result = await page.evaluate(f"""
                async () => {{
                    // login 함수가 있는지 확인
                    if (typeof login === 'function') {{
                        try {{
                            // login 함수 호출 (페이지의 JavaScript가 처리)
                            login('{username}', '{password}');
                            return {{ success: true, message: 'Login function called' }};
                        }} catch (e) {{
                            return {{ success: false, message: e.toString() }};
                        }}
                    }} else {{
                        // 로그인 링크 클릭
                        const loginLink = document.querySelector('a[href*="login("]');
                        if (loginLink) {{
                            loginLink.click();
                            return {{ success: true, message: 'Login link clicked' }};
                        }}
                        return {{ success: false, message: 'Login function not found' }};
                    }}
                }}
            """)

            logger.info(f"JavaScript execution result: {login_result}")

            # 로그인 처리 대기
            if timing_profile.post_submit_wait_ms:
                try:
                    await page.wait_for_load_state(
                        "networkidle",
                        timeout=timing_profile.post_submit_wait_ms
                    )
                except Exception:
                    await page.wait_for_timeout(timing_profile.post_submit_wait_ms)

            # 로그인 완료 대기 및 세션 세팅 시간 확보
            if timing_profile.final_settle_wait_ms:
                await page.wait_for_timeout(timing_profile.final_settle_wait_ms)

            # 로그인 성공 확인
            cookies = await page.context.cookies()
            access_token_cookie = next((c for c in cookies if c['name'] == 'access_token'), None)
            current_url = page.url

            logger.info(f"Login result URL: {current_url}")
            logger.info(f"access_token cookie: {'present' if access_token_cookie else 'absent'}")

            if access_token_cookie or 'login' not in current_url.lower():
                logger.info("Login successful!")
                return True
            else:
                logger.warning("Login status unclear, proceeding anyway")
                return True  # 일단 계속 진행

        except Exception as e:
            logger.error(f"JavaScript login attempt failed: {str(e)}")
            # 로그인 링크 직접 클릭 시도
            try:
                login_link = page.locator('a[href*="login("]')
                if await login_link.count() > 0:
                    logger.info("Trying to click login link...")
                    await login_link.click()
                    await page.wait_for_timeout(5000)
                    return True
            except:
                pass

            return False
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return False


async def navigate_to_reservation_page(
    page: Page,
    context: BrowserContext,
    timing: LoginTimingProfile | None = None
) -> tuple[bool, Page]:
    """
    lulu-lala 로그인 후 노출되는 Refresh SSO 링크를 통해 예약 페이지로 이동
    - swiper-slide 내 활성화된 Refresh 링크를 새 탭에서 호출해 자동 로그인
    - 실패 시 기존 direct intro/index 접근 및 아이콘 클릭 방식으로 폴백

    Args:
        page: Playwright Page 객체 (로그인 완료된 상태)
        context: BrowserContext 객체
        timing: 타이밍 프로파일

    Returns:
        tuple[bool, Page]: (성공 여부, 최종 페이지 객체)
    """
    try:
        timing_profile = timing or STABLE_LOGIN_TIMING

        logger.info("=" * 60)
        logger.info("Navigating to shbrefresh via Refresh SSO link")
        logger.info("=" * 60)

        # STEP 0: 로그인 후 노출된 swiper-slide에서 SSO 링크 바로 호출 (새 탭)
        logger.info("Attempting Refresh SSO link from active swiper slide...")
        link_success, tab_page = await _open_refresh_sso_in_new_tab(page, context, timing_profile)
        if link_success and tab_page:
            logger.info("=" * 60)
            logger.info("✓ Successfully navigated via active swiper SSO link")
            logger.info(f"✓ Final URL: {tab_page.url}")
            logger.info("=" * 60)
            return True, tab_page

        logger.warning("Active swiper SSO link navigation failed, falling back to direct intro/index approach")

        # 현재 쿠키 상태 확인 (디버깅용)
        cookies = await context.cookies()
        logger.info(f"Current cookies count: {len(cookies)}")
        cookie_domains = set(c.get('domain', '') for c in cookies)
        logger.info(f"Cookie domains: {cookie_domains}")

        # STEP 1: shbrefresh intro 페이지로 직접 이동 (SSO 쿠키 자동 전달)
        logger.info(f"[Direct SSO] Navigating to: {SHB_REFRESH_INTRO_URL}")

        try:
            # 같은 페이지 객체에서 직접 이동 (새 탭 생성하지 않음)
            response = await page.goto(
                SHB_REFRESH_INTRO_URL,
                wait_until="networkidle",
                timeout=30000
            )

            logger.info(f"Response status: {response.status if response else 'N/A'}")
            logger.info(f"Current URL after intro: {page.url}")

        except Exception as goto_error:
            logger.error(f"Failed to navigate to intro page: {goto_error}")
            await page.screenshot(path="error_sso_intro_failed.png", full_page=True)

            # Fallback: 복잡한 아이콘 클릭 방식 시도
            logger.warning("Falling back to icon click method...")
            return await _fallback_icon_click_navigation(page, context, timing_profile)

        # 안정화 대기
        if timing_profile.reservation_pre_click_ms:
            await page.wait_for_timeout(timing_profile.reservation_pre_click_ms)

        # 로그인 실패 여부 확인
        current_url = page.url.lower()
        if "error" in current_url or ("login" in current_url and "lulu-lala" in current_url):
            logger.error("SSO failed - redirected back to login page")
            await page.screenshot(path="error_sso_login_redirect.png", full_page=True)

            # 쿠키 재확인
            cookies_after = await context.cookies()
            logger.error(f"Cookies after failed navigation: {len(cookies_after)}")

            # Fallback
            logger.warning("Falling back to icon click method...")
            return await _fallback_icon_click_navigation(page, context, timing_profile)

        logger.info(f"✓ Successfully reached intro page: {page.url}")

        # STEP 2: index 페이지로 이동
        logger.info(f"[Direct SSO] Navigating to: {SHB_REFRESH_INDEX_URL}")

        try:
            response = await page.goto(
                SHB_REFRESH_INDEX_URL,
                wait_until="networkidle",
                timeout=30000
            )

            logger.info(f"Response status: {response.status if response else 'N/A'}")
            logger.info(f"Final URL: {page.url}")

        except Exception as index_error:
            logger.error(f"Failed to navigate to index page: {index_error}")
            await page.screenshot(path="error_sso_index_failed.png", full_page=True)
            return False, page

        # 안정화 대기
        if timing_profile.post_reservation_click_ms:
            await page.wait_for_timeout(timing_profile.post_reservation_click_ms)

        # 최종 확인
        final_url = page.url.lower()

        if ("shbrefresh" in final_url or "interparkb2b" in final_url) and \
           "error" not in final_url and "login" not in final_url:
            logger.info("=" * 60)
            logger.info("✓ Successfully navigated to reservation page via direct SSO")
            logger.info(f"✓ Final URL: {page.url}")
            logger.info("=" * 60)
            return True, page

        logger.error("Failed to reach reservation page - unexpected final URL")
        await page.screenshot(path="error_sso_unexpected_url.png", full_page=True)
        return False, page

    except Exception as e:
        logger.error(f"Error in SSO navigation: {str(e)}", exc_info=True)
        await page.screenshot(path="error_sso_exception.png", full_page=True)
        return False, page


async def _fallback_icon_click_navigation(
    page: Page,
    context: BrowserContext,
    timing_profile: LoginTimingProfile
) -> tuple[bool, Page]:
    """
    Fallback 방식: Refresh 아이콘 클릭 후 새 탭 전환
    (SSO 직접 접근이 실패했을 때만 사용)
    """
    try:
        logger.info("=" * 60)
        logger.info("FALLBACK: Trying icon click navigation...")
        logger.info("=" * 60)

        # Refresh 아이콘 찾기
        frames = page.frames
        refresh_element = None
        found_in_frame = None

        for frame in [page] + list(frames):
            try:
                all_links = await frame.query_selector_all("a, button, [role='button'], [onclick], img")

                for element in all_links:
                    try:
                        text = await element.inner_text() if hasattr(element, 'inner_text') else ""
                        href = await element.get_attribute("href") or ""
                        onclick = await element.get_attribute("onclick") or ""
                        title = await element.get_attribute("title") or ""
                        alt = await element.get_attribute("alt") or ""
                        src = await element.get_attribute("src") or ""

                        combined_text = f"{text} {href} {onclick} {title} {alt} {src}".lower()

                        if "sh_gmidas" in combined_text or ("shbrefresh" in combined_text and "vservice" in combined_text):
                            logger.info(f"Found Refresh icon: {href[:100]}")
                            refresh_element = element
                            found_in_frame = frame
                            break
                    except:
                        continue

                if refresh_element:
                    break
            except:
                continue

        if not refresh_element:
            logger.error("Refresh icon not found")
            return False, page

        # Dialog 핸들러 설정
        async def handle_dialog(dialog):
            logger.info(f"Dialog detected: {dialog.type}")
            await dialog.accept()

        page.on("dialog", handle_dialog)
        context.on("page", lambda new_page: new_page.on("dialog", handle_dialog))

        # 아이콘 클릭
        logger.info("Clicking Refresh icon...")

        pages_before = len(context.pages)
        shbrefresh_page = None

        def handle_new_page(new_page):
            nonlocal shbrefresh_page
            url = new_page.url
            if "shbrefresh" in url.lower() or "interparkb2b" in url.lower():
                if "error" not in url.lower() and "login" not in url.lower():
                    logger.info(f"New shbrefresh page detected: {url}")
                    shbrefresh_page = new_page

        context.on("page", handle_new_page)

        # 클릭 실행
        if found_in_frame and found_in_frame != page:
            try:
                await refresh_element.click(timeout=5000)
            except:
                await refresh_element.evaluate("el => el.click()")
        else:
            await refresh_element.scroll_into_view_if_needed()
            await refresh_element.click()

        # 새 페이지 대기
        poll_interval = max(200, timing_profile.nav_poll_interval_ms)
        max_wait_ms = timing_profile.max_nav_wait_seconds * 1000
        waited_ms = 0

        while waited_ms < max_wait_ms:
            await page.wait_for_timeout(poll_interval)
            waited_ms += poll_interval

            if shbrefresh_page:
                await shbrefresh_page.wait_for_load_state("networkidle", timeout=10000)
                page = shbrefresh_page
                logger.info(f"Switched to new shbrefresh page: {page.url}")
                break

            current_url = page.url
            if "shbrefresh" in current_url.lower() or "interparkb2b" in current_url.lower():
                if "error" not in current_url.lower() and "login" not in current_url.lower():
                    logger.info(f"Same page navigated to shbrefresh: {current_url}")
                    break

            if len(context.pages) > pages_before:
                for p in context.pages:
                    try:
                        p_url = p.url
                        if "shbrefresh" in p_url.lower() or "interparkb2b" in p_url.lower():
                            if "error" not in p_url.lower() and "login" not in p_url.lower():
                                await p.wait_for_load_state("networkidle", timeout=10000)
                                page = p
                                logger.info(f"Found shbrefresh in new tab: {page.url}")
                                break
                    except:
                        continue

        # intro -> index 전환
        current_url = page.url.lower()
        if "shbrefresh" not in current_url and "interparkb2b" not in current_url:
            logger.error("Failed to reach shbrefresh via icon click")
            return False, page

        intro_loaded = "intro" in current_url
        success = await _ensure_intro_then_index(page, timing_profile, intro_already_loaded=intro_loaded)

        if success:
            logger.info("✓ Successfully navigated via fallback icon click method")
            return True, page

        logger.error("Fallback method failed")
        return False, page

    except Exception as e:
        logger.error(f"Fallback navigation error: {str(e)}", exc_info=True)
        return False, page


async def crawl_accommodations(page: Page) -> List[Dict]:
    """
    RESERVATION 페이지에서 숙소 정보 및 날짜별 신청 점수/인원 크롤링
    
    전략:
    1. 메인 페이지에서 지역별 연성소 링크 수집
    2. 각 지역별 페이지에서 개별 숙소 링크 수집
    3. 각 개별 숙소 상세 페이지에서 정보 추출
    
    Returns:
        List[Dict]: 크롤링한 숙소 정보 리스트
        각 Dict는 다음 구조:
        {
            "name": str,
            "price": int,
            "region": str,
            "image_url": str,
            "date_booking_info": {
                "YYYY-MM-DD": {"score": int, "applicants": int},
                ...
            }
        }
    """
    try:
        logger.info(f"Crawling accommodations from current page: {page.url}")
        await page.wait_for_timeout(2000)  # 페이지 로딩 대기

        accommodations = []

        # STEP 0: "연성소 더보기" 버튼 찾아서 클릭 (61개 모두 표시)
        logger.info("STEP 0: Looking for '연성소 더보기' button...")
        try:
            # 여러 가능한 선택자로 더보기 버튼 찾기
            more_button_selectors = [
                "button:has-text('더보기')",
                "a:has-text('더보기')",
                "[class*='more']:has-text('더보기')",
                "button:has-text('연성소 더보기')",
                "a:has-text('연성소 더보기')",
                ".btn-more",
                "#btnMore",
                "[onclick*='more']"
            ]

            more_button = None
            for selector in more_button_selectors:
                try:
                    more_button = await page.query_selector(selector)
                    if more_button:
                        # 버튼이 보이는지 확인
                        is_visible = await more_button.is_visible()
                        if is_visible:
                            logger.info(f"Found '더보기' button with selector: {selector}")
                            break
                        else:
                            more_button = None
                except:
                    continue

            if more_button:
                logger.info("Clicking '연성소 더보기' button...")
                await more_button.scroll_into_view_if_needed()
                await more_button.click()
                await page.wait_for_timeout(2000)  # 추가 숙소 로딩 대기
                logger.info("✓ Clicked '더보기' button, all accommodations should now be visible")
            else:
                logger.warning("'연성소 더보기' button not found, proceeding with visible accommodations")
        except Exception as e:
            logger.warning(f"Error clicking '더보기' button: {str(e)}, proceeding anyway")

        # STEP 1: 모든 개별 숙소 링크 수집 (/condo/숫자 패턴)
        logger.info("STEP 1: Collecting all individual accommodation links...")

        # 페이지에서 모든 링크 요소 가져오기
        all_links = await page.query_selector_all("a")
        accommodation_urls = set()  # 중복 제거를 위해 set 사용

        import re
        for link in all_links:
            try:
                href = await link.get_attribute("href")
                if not href:
                    continue

                # /condo/숫자 패턴 매칭 (지역 목록이나 기타 페이지 제외)
                if re.search(r'/condo/\d+', href):
                    # 절대 URL로 변환
                    if href.startswith("http"):
                        full_url = href
                    elif href.startswith("/"):
                        # 도메인 추출 (현재 페이지의 도메인 사용)
                        current_url = page.url
                        base_url = re.match(r'(https?://[^/]+)', current_url)
                        if base_url:
                            full_url = base_url.group(1) + href
                        else:
                            full_url = f"https://shbrefresh.interparkb2b.co.kr{href}"
                    else:
                        full_url = f"https://shbrefresh.interparkb2b.co.kr/{href}"

                    # 쿼리 파라미터 제거 (같은 숙소의 다른 뷰는 제외)
                    clean_url = full_url.split('?')[0]
                    accommodation_urls.add(clean_url)

            except:
                continue

        logger.info(f"  Found {len(accommodation_urls)} unique accommodation URLs")

        if len(accommodation_urls) == 0:
            logger.warning("No accommodation links found!")
            return accommodations

        # STEP 2: 각 숙소 상세 페이지에서 정보 추출
        logger.info(f"STEP 2: Crawling {len(accommodation_urls)} accommodations...")

        for acc_idx, acc_url in enumerate(sorted(accommodation_urls), 1):
            logger.info(f"  [{acc_idx}/{len(accommodation_urls)}] Processing: {acc_url}")
            try:
                await crawl_individual_accommodation(page, acc_url, accommodations)
            except Exception as e:
                logger.warning(f"    Error crawling {acc_url}: {str(e)}")
                continue
        
        logger.info(f"Crawled {len(accommodations)} accommodations")
        return accommodations
        
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}", exc_info=True)
        await page.screenshot(path="crawl_error.png", full_page=True)
        return []


async def extract_meta_text_candidates(page: Page) -> List[str]:
    """
    숙소 제목 주변의 텍스트 블록을 수집하여 지역/타입/정원 등의 메타 정보를 찾는 데 활용
    """
    try:
        raw_blocks = await page.evaluate(
            """
            () => {
                const results = [];
                const seen = new Set();
                const pushText = (node) => {
                    if (!node) { return; }
                    const text = (node.innerText || '').replace(/\\u00a0/g, ' ').trim();
                    if (!text) { return; }
                    const snapshot = text.length > 400 ? text.slice(0, 400) : text;
                    if (seen.has(snapshot)) { return; }
                    seen.add(snapshot);
                    results.push(snapshot);
                };

                const titleSelectors = [
                    '.prdSubject',
                    '.prd_subject',
                    '.prd-title',
                    '.prdTitle',
                    '.prdTit',
                    '.prd_tit',
                    '.condo-title',
                    '.condo_tit',
                    '.title_area h1',
                    '.title_area h2',
                    '.titArea h1',
                    '.titArea h2'
                ];

                let titleEl = null;
                for (const selector of titleSelectors) {
                    const candidate = document.querySelector(selector);
                    if (candidate) {
                        titleEl = candidate;
                        break;
                    }
                }

                if (!titleEl) {
                    titleEl = document.querySelector('h1, h2, .title, .name');
                }

                const collectAround = (element, depthLimit = 4) => {
                    if (!element) { return; }
                    let next = element.nextElementSibling;
                    let depth = 0;
                    while (next && depth < depthLimit) {
                        pushText(next);
                        next = next.nextElementSibling;
                        depth += 1;
                    }
                    let prev = element.previousElementSibling;
                    depth = 0;
                    while (prev && depth < 2) {
                        pushText(prev);
                        prev = prev.previousElementSibling;
                        depth += 1;
                    }
                };

                if (titleEl) {
                    pushText(titleEl);
                    collectAround(titleEl, 5);
                    let parent = titleEl.parentElement;
                    let level = 0;
                    while (parent && level < 3) {
                        pushText(parent);
                        collectAround(parent, 2);
                        parent = parent.parentElement;
                        level += 1;
                    }
                }

                const infoSelectors = [
                    '.prd_info',
                    '.prd-info',
                    '.prdDesc',
                    '.prd_desc',
                    '.prdMeta',
                    '.prd_meta',
                    '.prdSub',
                    '.prd_sub',
                    '.prd-sub',
                    '.prd_info_box',
                    '.prd-info-box',
                    '.info_area',
                    '.info-area',
                    '.info_box',
                    '.infoBox',
                    '.meta_info',
                    '.room_info',
                    '.room-info',
                    '.product_info',
                    '.product-info',
                    '.detail_info',
                    '.detail-info',
                    '.condo_tit',
                    '.condo-tit'
                ];

                for (const selector of infoSelectors) {
                    document.querySelectorAll(selector).forEach((node) => pushText(node));
                }

                return results;
            }
            """
        )

        if isinstance(raw_blocks, list):
            cleaned_blocks: List[str] = []
            seen_texts = set()
            for block in raw_blocks:
                if not isinstance(block, str):
                    continue
                text = block.strip()
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)
                cleaned_blocks.append(text)
            return cleaned_blocks

    except Exception as e:
        logger.debug(f"  Failed to collect meta candidates: {str(e)}")

    return []


async def crawl_individual_accommodation(
    page: Page,
    acc_url: str,
    accommodations: List[Dict],
    region: str = "Unknown"
) -> None:
    """
    개별 숙소 상세 페이지에서 정보 추출

    Args:
        page: Playwright Page 객체
        acc_url: 숙소 상세 페이지 URL
        accommodations: 결과를 추가할 리스트
        region: 지역명
    """
    try:
        logger.info(f"  Crawling individual accommodation: {acc_url}")

        # URL에서 숙소 ID 추출 (/condo/189 -> 189)
        import re
        acc_id_match = re.search(r'/condo/(\d+)', acc_url)
        if not acc_id_match:
            logger.warning(f"  Cannot extract accommodation ID from URL: {acc_url}")
            return

        acc_id = acc_id_match.group(1)
        logger.info(f"  Accommodation ID: {acc_id}")

        # 숙소 상세 페이지로 이동
        await page.goto(acc_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # 페이지 전체 텍스트 가져오기 (디버깅 및 정보 추출용)
        page_text = await page.inner_text("body")

        # 숙소 이름 추출 (여러 방법 시도)
        name = "Unknown"

        # 방법 1: 큰 제목 태그에서 추출 (가장 눈에 띄는 제목)
        name_selectors = [
            ".prdSubject",  # 숙소 이름이 있는 실제 클래스 (최우선)
            "h1", "h2", ".title", ".name", "[class*='title']", "[class*='name']",
            ".condo-title", ".hotel-title", "#condoName"
        ]

        found_names = []
        for selector in name_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    temp_name = await elem.inner_text()
                    temp_name = temp_name.strip()

                    # 완전히 무효한 키워드 (이것만 있으면 제외)
                    completely_invalid = [
                        "객실 상태", "표시 안내", "이용시간", "운영시간", "신한은행",
                        "Refresh", "SHB", "체크인", "체크아웃", "연성소",
                        "객실유형", "이용박수", "객실없음", "오픈전"
                    ]

                    # 유효한 이름인지 확인
                    if temp_name and len(temp_name) > 2 and len(temp_name) < 100:
                        is_valid = True

                        # 완전 무효 키워드 체크 (전체가 이것이면 제외)
                        temp_name_clean = temp_name.strip()
                        for keyword in completely_invalid:
                            if temp_name_clean == keyword or (keyword in temp_name_clean and len(temp_name_clean) < 10):
                                is_valid = False
                                break

                        # 특수문자나 숫자만 있는지 체크
                        if is_valid and not re.search(r'[가-힣a-zA-Z]', temp_name):
                            is_valid = False

                        if is_valid:
                            found_names.append(temp_name)
                            logger.debug(f"    Found potential name from {selector}: {temp_name}")
            except:
                continue

        # 가장 적절한 이름 선택 (길이와 위치 고려)
        if found_names:
            # 중복 제거
            unique_names = list(dict.fromkeys(found_names))
            # 가장 앞에 나온 이름 사용 (보통 페이지 상단의 큰 제목)
            name = unique_names[0]
            logger.info(f"    Selected name: {name}")

        # 방법 2: 페이지 제목에서 추출 (이름을 찾지 못한 경우)
        if not name or name == "Unknown":
            page_title = await page.title()
            if page_title and page_title != "Unknown":
                # "신한은행 Refresh" 같은 공통 부분 제거
                name = page_title.split('-')[0].strip()
                name = name.replace("신한은행 Refresh", "").strip()
                name = name.replace("신한은행", "").strip()
                name = name.replace("Refresh", "").strip()
                if name:
                    logger.debug(f"    Extracted name from title: {name}")

        # 지역/숙소 타입/정원 추출 (숙소 제목 근처 메타 영역 우선)
        region_value = region if region != "Unknown" else None
        accommodation_type = None
        capacity_value = None

        meta_texts = await extract_meta_text_candidates(page)
        meta_selectors = [
            ".prdSubject + *",
            ".prdSubject ~ *",
            ".prd_info",
            ".prd-info",
            ".info_area",
            ".titArea",
            ".title_area",
            ".condo_tit",
            ".room_info",
            ".room-info",
            ".product_info",
            ".product-info",
        ]
        seen_meta_texts = set(meta_texts)
        for selector in meta_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.inner_text()
                    if text:
                        cleaned_text = text.strip()
                        if cleaned_text and cleaned_text not in seen_meta_texts:
                            meta_texts.append(cleaned_text)
                            seen_meta_texts.add(cleaned_text)
            except:
                continue

        # 제목 주변에서 정보를 찾지 못한 경우 페이지 상단부 텍스트 사용
        if not meta_texts:
            meta_texts.append("\n".join(page_text.splitlines()[:15]))

        def normalize_lines(texts: List[str]) -> List[str]:
            lines: List[str] = []
            for text in texts:
                for line in text.splitlines():
                    cleaned = " ".join(line.split())
                    if cleaned:
                        lines.append(cleaned)
            return lines

        meta_lines = normalize_lines(meta_texts)

        # 지역 추출 (시/도 키워드 우선)
        region_pattern = re.compile(
            r"(서울|경기|인천|부산|대구|광주|대전|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주)\s*(특별자치도|특별자치시|광역시|특별시|도|시)?"
        )
        for line in meta_lines:
            match = region_pattern.search(line)
            if match:
                region_value = f"{match.group(1)}{match.group(2) or ''}"
                break
        if not region_value:
            match = region_pattern.search(page_text)
            if match:
                region_value = f"{match.group(1)}{match.group(2) or ''}"

        # 숙소 타입 추출 (타입 키워드가 포함된 짧은 텍스트 선호)
        type_keywords = [
            "스위트",
            "스탠더드",
            "스탠다드",
            "디럭스",
            "더블",
            "트윈",
            "온돌",
            "패밀리",
            "펜션",
            "리조트",
            "독채",
            "풀빌라",
            "카라반",
            "킹",
            "퀸",
            "룸",
            "room",
            "suite",
            "double",
            "twin",
            "family",
        ]
        type_candidates = []
        for line in meta_lines:
            lower_line = line.lower()
            if any(kw.lower() in lower_line for kw in type_keywords):
                cleaned_line = re.sub(r"\d+\s*[명인]\b", "", line)
                if region_value:
                    cleaned_line = cleaned_line.replace(region_value, "")
                parts = re.split(r"[|/·>-]", cleaned_line)
                for part in parts:
                    part_clean = part.strip(" |-./·")
                    if not part_clean:
                        continue
                    if any(kw.lower() in part_clean.lower() for kw in type_keywords):
                        type_candidates.append(part_clean)
                        break
        if type_candidates:
            accommodation_type = type_candidates[0]

        if not accommodation_type:
            type_label_patterns = [
                r"(?:객실유형|객실 유형|객실타입|객실 타입|객실형|룸형|룸 타입|룸타입|객실구분|객실종류|Room\s*Type)\s*[:\-]?\s*([^\n]+)",
            ]
            for pattern in type_label_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    candidate = match.group(1).splitlines()[0].strip(" :-/|·")
                    if candidate:
                        accommodation_type = candidate
                        break

        # 정원 추출 (상단 짧은 문구에서 '명/인' 패턴 우선)
        capacity_patterns = [
            r"(?:기준|정원|최대|수용)\s*(\d+)\s*(?:명|인)",
            r"(\d+)\s*(?:명|인)\s*기준",
            r"^\s*(\d+)\s*(?:명|인)\s*$",
            r"정원[:\s]*(\d+)",
            r"(\d+)\s*(?:명|인)\s*이용",
            r"(\d+)\s*인\s*실",
        ]
        for line in meta_lines:
            if len(line) > 120:
                continue
            for pattern in capacity_patterns:
                cap_match = re.search(pattern, line)
                if cap_match:
                    try:
                        cap_val = int(cap_match.group(1))
                        if cap_val > 0:
                            capacity_value = cap_val
                            break
                    except:
                        continue
            if capacity_value:
                break
        if not capacity_value:
            extended_capacity_patterns = [
                r"(?:기준|정원|최대|수용)\s*(\d+)\s*(?:명|인)",
                r"(?:기준인원|기준 인원|정원|최대인원|최대 인원|수용인원|수용 인원|이용인원|이용 인원)\s*[:\-]?\s*(\d+)\s*(?:명|인)?",
                r"(\d+)\s*(?:명|인)\s*(?:수용|이용)",
            ]
            for pattern in extended_capacity_patterns:
                cap_match = re.search(pattern, page_text)
                if cap_match:
                    try:
                        capacity_value = int(cap_match.group(1))
                        break
                    except:
                        continue

        # 주소 추출
        address = None
        address_patterns = [
            r'주소[:\s]*([^\n]+)',
            r'소재지[:\s]*([^\n]+)',
            r'위치[:\s]*([^\n]+)',
            r'Address[:\s]*([^\n]+)'
        ]
        for pattern in address_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                logger.debug(f"    Extracted address: {address}")
                break

        # 연락처 추출
        contact = None
        contact_patterns = [
            r'연락처[:\s]*([0-9-]+)',
            r'전화[:\s]*([0-9-]+)',
            r'Tel[:\s]*([0-9-]+)',
            r'문의[:\s]*([0-9-]+)',
            r'(\d{2,3}-\d{3,4}-\d{4})'
        ]
        for pattern in contact_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                contact = match.group(1).strip()
                logger.debug(f"    Extracted contact: {contact}")
                break

        # 홈페이지 URL 추출
        homepage = None
        homepage_patterns = [
            r'홈페이지[:\s]*(https?://[^\s\n]+)',
            r'Homepage[:\s]*(https?://[^\s\n]+)',
            r'Website[:\s]*(https?://[^\s\n]+)'
        ]
        for pattern in homepage_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                homepage = match.group(1).strip()
                logger.debug(f"    Extracted homepage: {homepage}")
                break

        # 메타 정보 보완 - 주소/라벨 기반 지역 추출 및 텍스트 정리
        if (not region_value or region_value == "Unknown") and address:
            match = region_pattern.search(address)
            if match:
                region_value = f"{match.group(1)}{match.group(2) or ''}"

        if not region_value or region_value == "Unknown":
            region_label_pattern = re.compile(
                r"(?:지역|지역구분|소재지|위치)\s*[:\-]?\s*([가-힣\s]{2,25}?(?:특별자치도|특별자치시|광역시|특별시|자치시|자치도|도|시|군|구))"
            )
            label_match = region_label_pattern.search(page_text)
            if label_match:
                region_value = label_match.group(1).strip()

        region_value = region_value or region or "Unknown"

        if accommodation_type:
            cleaned_type = accommodation_type
            if region_value:
                cleaned_type = cleaned_type.replace(region_value, "")
            cleaned_type = re.sub(r"(기준|정원|최대)\s*\d+\s*(?:명|인)", "", cleaned_type)
            cleaned_type = re.sub(r"\s{2,}", " ", cleaned_type).strip(" |-·/.,")
            if cleaned_type:
                accommodation_type = cleaned_type

        logger.info(
            f"    Meta info - region: {region_value}, type: {accommodation_type}, capacity: {capacity_value or 'Unknown'}"
        )

        # 가격은 존재하지 않음 (점수 순으로 선정되는 방식)
        price = 0

        # 이미지 추출 - 모든 숙소 이미지 수집
        image_urls = []
        all_images = await page.query_selector_all("img")

        for img in all_images:
            try:
                src = await img.get_attribute("src")

                if not src:
                    continue

                # 상대 URL을 절대 URL로 변환
                if not src.startswith("http"):
                    if src.startswith("/"):
                        # 현재 페이지의 도메인 사용
                        current_url = page.url
                        base_url_match = re.match(r'(https?://[^/]+)', current_url)
                        if base_url_match:
                            src = base_url_match.group(1) + src
                        else:
                            src = f"https://shbrefresh.interparkb2b.co.kr{src}"
                    else:
                        src = f"https://shbrefresh.interparkb2b.co.kr/{src}"

                # 명확히 제외해야 할 이미지만 필터링
                exclude_keywords = ["btn", "button", "icon", "logo", "banner", "symbol", "arrow", "close", "menu"]

                should_exclude = False
                for keyword in exclude_keywords:
                    if keyword in src.lower():
                        should_exclude = True
                        break

                # data:image나 base64 이미지는 제외
                if src.startswith("data:"):
                    should_exclude = True

                if not should_exclude:
                    # 중복 제거
                    if src not in image_urls:
                        image_urls.append(src)
                        logger.debug(f"    Found image: {src}")

                # 최대 20개 이미지까지만 수집 (너무 많으면 제한)
                if len(image_urls) >= 20:
                    break
            except:
                continue

        logger.info(f"    Found {len(image_urls)} images")

        # 날짜별 신청 점수 및 인원 정보 추출
        # calendar 클래스에서 data-role="roomInfo" 요소 찾기
        date_booking_info = {}

        import re
        from datetime import datetime

        logger.info(f"  Extracting date booking information from calendar...")

        # 현재 월 + 이전 2개월 데이터 크롤링 (총 3개월)
        for month_offset in range(3):
            if month_offset > 0:
                # month_prev 버튼 클릭하여 이전 달로 이동
                logger.info(f"  Navigating to {month_offset} month(s) ago...")
                try:
                    # month_prev 버튼 찾기 (여러 가능한 선택자)
                    prev_button_selectors = [
                        ".month_prev",
                        "[class*='month_prev']",
                        "[class*='prev']",
                        "button:has-text('이전')",
                        "a:has-text('이전')",
                    ]

                    prev_button = None
                    for selector in prev_button_selectors:
                        try:
                            prev_button = await page.query_selector(selector)
                            if prev_button:
                                is_visible = await prev_button.is_visible()
                                if is_visible:
                                    logger.debug(f"    Found prev button with selector: {selector}")
                                    break
                                else:
                                    prev_button = None
                        except:
                            continue

                    if prev_button:
                        await prev_button.click()
                        await page.wait_for_timeout(1500)  # 달력 로딩 대기
                        logger.info(f"    ✓ Navigated to previous month ({month_offset} month(s) ago)")
                    else:
                        logger.warning(f"    ⚠️  Previous month button not found, skipping month offset {month_offset}")
                        break

                except Exception as e:
                    logger.warning(f"    Error navigating to previous month: {str(e)}")
                    break

            # calendar 클래스 또는 data-role="roomInfo" 요소 찾기
            room_info_elements = await page.query_selector_all('[data-role="roomInfo"]')

            if not room_info_elements:
                # 대안: calendar 클래스 내부에서 찾기
                calendars = await page.query_selector_all('.calendar, [class*="calendar"]')
                for calendar in calendars:
                    room_info_elements.extend(await calendar.query_selector_all('[data-role="roomInfo"]'))

            logger.info(f"  Found {len(room_info_elements)} room info elements for month offset {month_offset}")

            for room_info in room_info_elements:
                try:
                    # data-rblockdate 속성에서 날짜 추출
                    date_str = await room_info.get_attribute("data-rblockdate")
                    if not date_str:
                        continue

                    logger.debug(f"    Processing date: {date_str}")

                    # room_status 요소 찾기
                    room_status_element = await room_info.query_selector(".room_status, [class*='room_status']")
                    if not room_status_element:
                        # room_status가 없으면 전체 텍스트에서 추출
                        room_status_element = room_info

                    room_status_html = await room_status_element.inner_html()
                    room_status_text = await room_status_element.inner_text()

                    # 상태 추출
                    status = "Unknown"
                    if "신청중" in room_status_text or "신청 중" in room_status_text:
                        status = "신청중"
                    elif "마감" in room_status_text or "신청종료" in room_status_text:
                        status = "마감(신청종료)"
                    elif "신청불가" in room_status_text:
                        status = "신청불가(오픈전)"
                    elif "객실없음" in room_status_text:
                        status = "객실없음"

                    # '마감(신청종료)' 상태만 처리
                    if status != "마감(신청종료)":
                        logger.debug(f"      Skipping {date_str}: status is '{status}' (only '마감(신청종료)' is saved)")
                        continue

                    # 최초 점수와 상시 점수를 data 속성에서 직접 추출 (가장 정확)
                    choi_score = 0.0  # 최초 점수
                    sangsi_score = 0.0  # 상시 점수

                    # data-first-room-score 속성에서 최초 점수 추출
                    first_score_attr = await room_info.get_attribute("data-first-room-score")
                    if first_score_attr and first_score_attr.strip():
                        try:
                            choi_score = float(first_score_attr)
                            logger.debug(f"      최초 점수: {choi_score}점 (from data-first-room-score)")
                        except:
                            pass

                    # data-permanent-room-score 속성에서 상시 점수 추출
                    permanent_score_attr = await room_info.get_attribute("data-permanent-room-score")
                    if permanent_score_attr and permanent_score_attr.strip():
                        try:
                            sangsi_score = float(permanent_score_attr)
                            logger.debug(f"      상시 점수: {sangsi_score}점 (from data-permanent-room-score)")
                        except:
                            pass

                    # data 속성에서 추출 실패 시, HTML에서 파싱 시도 (fallback)
                    if choi_score == 0.0 and sangsi_score == 0.0:
                        # <span>최초</span> 다음의 점수 추출
                        choi_match = re.search(r'<span[^>]*>최초</span>\s*\d+\s*실\s*-\s*(\d+\.?\d*)\s*점', room_status_html)
                        if choi_match:
                            choi_score = float(choi_match.group(1))
                            logger.debug(f"      최초 점수: {choi_score}점 (from HTML)")

                        # <span>상시</span> 다음의 점수 추출
                        sangsi_match = re.search(r'<span[^>]*>상시</span>\s*\d+\s*실\s*-\s*(\d+\.?\d*)\s*점', room_status_html)
                        if sangsi_match:
                            sangsi_score = float(sangsi_match.group(1))
                            logger.debug(f"      상시 점수: {sangsi_score}점 (from HTML)")

                        # <span>예상점수</span> 추출 (최초/상시가 없는 경우)
                        if choi_score == 0.0 and sangsi_score == 0.0:
                            expected_match = re.search(r'<span[^>]*>예상점수</span>\s*(\d+\.?\d*)', room_status_html)
                            if expected_match:
                                sangsi_score = float(expected_match.group(1))
                                logger.debug(f"      예상점수: {sangsi_score}점 (from HTML)")

                    # 두 점수 중 더 높은 점수 선택
                    score = max(choi_score, sangsi_score)

                    if score > 0:
                        logger.debug(f"      Selected score: {score}점 (최초: {choi_score}, 상시: {sangsi_score})")

                    # 인원 추출 (data 속성 우선, 없으면 HTML 파싱)
                    applicants = 0
                    apply_count_attr = await room_info.get_attribute("data-apply-count")
                    if apply_count_attr and apply_count_attr.strip():
                        try:
                            applicants = int(apply_count_attr)
                            logger.debug(f"      신청인원: {applicants}명 (from data-apply-count)")
                        except:
                            pass

                    # data 속성에서 추출 실패 시 HTML 파싱
                    if applicants == 0:
                        applicants_patterns = [
                            r'<span[^>]*>신청인원</span>\s*(\d+)',
                            r'신청인원[:\s]*(\d+)',
                            r'(\d+)\s*명',
                        ]

                        for pattern in applicants_patterns:
                            match = re.search(pattern, room_status_text)
                            if match:
                                applicants = int(match.group(1))
                                logger.debug(f"      신청인원: {applicants}명 (from HTML)")
                                break

                    # 객실 수 추출 (data 속성 우선)
                    rooms = 0
                    room_count_attr = await room_info.get_attribute("data-room-count")
                    if room_count_attr and room_count_attr.strip():
                        try:
                            rooms = int(room_count_attr)
                            logger.debug(f"      객실수: {rooms}실 (from data-room-count)")
                        except:
                            pass

                    # data 속성에서 추출 실패 시 HTML 파싱
                    if rooms == 0:
                        rooms_match = re.search(r'<span[^>]*>객실수</span>\s*(\d+)', room_status_html)
                        if not rooms_match:
                            rooms_match = re.search(r'객실수?[:\s]*(\d+)', room_status_text)
                        if not rooms_match:
                            rooms_match = re.search(r'(\d+)\s*실', room_status_text)
                        if rooms_match:
                            rooms = int(rooms_match.group(1))
                            logger.debug(f"      객실수: {rooms}실 (from HTML)")

                    # 날짜 정보 저장 ('마감(신청종료)' 상태이고 점수가 있는 경우만)
                    if date_str and score > 0:
                        # 이미 해당 날짜 데이터가 있으면 건너뛰기 (중복 방지)
                        if date_str in date_booking_info:
                            logger.debug(f"      Skipping duplicate date: {date_str}")
                            continue

                        date_booking_info[date_str] = {
                            "status": status,
                            "score": score,
                            "applicants": applicants,
                            "rooms": rooms
                        }
                        logger.info(f"    ✓ {date_str}: {status}, {score}점, {applicants}명, {rooms}실")

                except Exception as e:
                    logger.debug(f"    Error processing room info: {str(e)}")
                    continue
        
        # 유효한 숙소 정보인지 확인
        if name and name != "Unknown":
            accommodation_data = {
                "id": acc_id,  # URL에서 추출한 실제 ID
                "name": name,
                "accommodation_type": accommodation_type,
                "address": address,  # 주소
                "contact": contact,  # 연락처
                "homepage": homepage,  # 홈페이지
                "price": price,
                "region": region_value,
                "capacity": capacity_value,
                "image_urls": image_urls,  # 이미지 URL 리스트
                "date_booking_info": date_booking_info
            }

            accommodations.append(accommodation_data)
            logger.info(f"    ✓ Extracted: {name} (ID: {acc_id})")
            if address:
                logger.info(f"      Address: {address}")
            if contact:
                logger.info(f"      Contact: {contact}")
            if homepage:
                logger.info(f"      Homepage: {homepage}")
            if image_urls:
                logger.info(f"      Images: {len(image_urls)} images")
            if date_booking_info:
                logger.info(f"      Date booking info: {len(date_booking_info)} dates")
                # 처음 3개 날짜 정보 로그
                for date, info in list(date_booking_info.items())[:3]:
                    logger.info(f"        - {date}: {info.get('status', 'Unknown')}, 점수 {info.get('score', 0)}점, 인원 {info.get('applicants', 0)}명")
        else:
            logger.warning(f"    ⚠️  Skipped: insufficient information")
            
    except Exception as e:
        logger.warning(f"  Error crawling individual accommodation {acc_url}: {str(e)}")


async def extract_date_booking_info(element, page: Page) -> Dict[str, Dict[str, int]]:
    """
    숙소 요소에서 날짜별 신청 점수 및 인원 정보 추출
    
    Returns:
        Dict[str, Dict[str, int]]: 날짜별 정보
        예: {"2024-01-15": {"score": 85, "applicants": 12}}
    """
    date_info = {}
    
    try:
        import re
        from datetime import datetime
        
        # 요소의 전체 텍스트 가져오기
        element_text = await element.inner_text() if hasattr(element, 'inner_text') else ""
        element_html = await element.inner_html() if hasattr(element, 'inner_html') else ""
        
        # 방법 1: 테이블 구조에서 날짜별 정보 추출
        # 테이블 행이나 셀에서 날짜 정보 찾기
        all_cells = await element.query_selector_all("td, th, .cell, [class*='cell'], [class*='date']")
        
        for cell in all_cells:
            try:
                cell_text = await cell.inner_text()
                
                # 날짜 추출 (다양한 형식 지원)
                # YYYY-MM-DD, YYYY/MM/DD, MM-DD, MM/DD 등
                date_patterns = [
                    r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD
                    r'(\d{1,2}[-/]\d{1,2})',  # MM-DD
                    r'(\d{1,2}월\s*\d{1,2}일)',  # 1월 15일
                    r'(\d{4}\.\d{1,2}\.\d{1,2})',  # YYYY.MM.DD
                ]
                
                date_str = None
                for pattern in date_patterns:
                    date_match = re.search(pattern, cell_text)
                    if date_match:
                        date_str = date_match.group(1)
                        break
                
                if not date_str:
                    continue
                
                # 날짜 형식 정규화 (YYYY-MM-DD)
                date_str = date_str.replace('/', '-').replace('.', '-')
                date_str = date_str.replace('월', '-').replace('일', '').strip()
                
                # MM-DD 형식을 YYYY-MM-DD로 변환
                if len(date_str.split('-')) == 2:
                    current_year = datetime.now().year
                    date_str = f"{current_year}-{date_str}"
                
                # 점수 추출 (다양한 패턴)
                score_patterns = [
                    r'(\d+)\s*점',
                    r'점수[:\s]*(\d+)',
                    r'score[:\s]*(\d+)',
                    r'신청점수[:\s]*(\d+)',
                    r'필요점수[:\s]*(\d+)',
                    r'(\d+)\s*pt',
                ]
                
                score = 0
                for pattern in score_patterns:
                    score_match = re.search(pattern, cell_text, re.IGNORECASE)
                    if score_match:
                        score = int(score_match.group(1))
                        break
                
                # 인원 추출 (다양한 패턴)
                applicants_patterns = [
                    r'(\d+)\s*명',
                    r'인원[:\s]*(\d+)',
                    r'applicants?[:\s]*(\d+)',
                    r'신청인원[:\s]*(\d+)',
                    r'신청자[:\s]*(\d+)',
                    r'(\d+)\s*people',
                ]
                
                applicants = 0
                for pattern in applicants_patterns:
                    applicants_match = re.search(pattern, cell_text, re.IGNORECASE)
                    if applicants_match:
                        applicants = int(applicants_match.group(1))
                        break
                
                # 인접 셀에서도 정보 찾기
                if score == 0 or applicants == 0:
                    # 다음 셀 확인
                    try:
                        next_cell = await cell.evaluate_handle("el => el.nextElementSibling")
                        if next_cell:
                            next_cell_text = await next_cell.inner_text() if hasattr(next_cell, 'inner_text') else ""
                            if score == 0:
                                for pattern in score_patterns:
                                    score_match = re.search(pattern, next_cell_text, re.IGNORECASE)
                                    if score_match:
                                        score = int(score_match.group(1))
                                        break
                            if applicants == 0:
                                for pattern in applicants_patterns:
                                    applicants_match = re.search(pattern, next_cell_text, re.IGNORECASE)
                                    if applicants_match:
                                        applicants = int(applicants_match.group(1))
                                        break
                    except:
                        pass
                
                if date_str and (score > 0 or applicants > 0):
                    date_info[date_str] = {
                        "score": score,
                        "applicants": applicants
                    }
                    logger.debug(f"Extracted date info: {date_str} - score: {score}, applicants: {applicants}")
                    
            except Exception as e:
                logger.debug(f"Error extracting date info from cell: {str(e)}")
                continue
        
        # 방법 2: 요소의 텍스트에서 직접 추출
        if not date_info:
            # 날짜 패턴 찾기
            date_matches = re.finditer(
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})|(\d{1,2}[-/]\d{1,2})|(\d{1,2}월\s*\d{1,2}일)',
                element_text
            )
            
            for match in date_matches:
                date_str = match.group(0)
                # 날짜 주변 텍스트에서 점수/인원 찾기
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(element_text), match.end() + 50)
                context_text = element_text[start_pos:end_pos]
                
                # 점수와 인원 추출
                score_match = re.search(r'(\d+)\s*점', context_text)
                applicants_match = re.search(r'(\d+)\s*명', context_text)
                
                score = int(score_match.group(1)) if score_match else 0
                applicants = int(applicants_match.group(1)) if applicants_match else 0
                
                if score > 0 or applicants > 0:
                    # 날짜 형식 정규화
                    date_str = date_str.replace('/', '-').replace('.', '-')
                    date_str = date_str.replace('월', '-').replace('일', '').strip()
                    if len(date_str.split('-')) == 2:
                        current_year = datetime.now().year
                        date_str = f"{current_year}-{date_str}"
                    
                    date_info[date_str] = {
                        "score": score,
                        "applicants": applicants
                    }
        
        # 방법 3: JavaScript 데이터에서 추출 시도
        try:
            js_data = await page.evaluate("""
                () => {
                    // window 객체에서 숙소 데이터 찾기
                    if (window.accommodationData) return window.accommodationData;
                    if (window.bookingData) return window.bookingData;
                    if (window.dateInfo) return window.dateInfo;
                    return null;
                }
            """)
            
            if js_data and isinstance(js_data, dict):
                logger.info("Found JavaScript data for accommodations")
                # js_data 처리 로직 추가 가능
                
        except Exception as e:
            logger.debug(f"Error extracting from JavaScript: {str(e)}")
        
    except Exception as e:
        logger.warning(f"Error extracting date booking info: {str(e)}")
    
    return date_info


async def save_accommodations_to_db(accommodations: List[Dict]):
    """
    크롤링한 숙소 정보를 DB에 저장
    - Accommodation: 숙소 기본 정보
    - AccommodationDate: 날짜별 숙소 내역
    - TodayAccommodation: 오늘자 숙소 내역

    Args:
        accommodations: 크롤링한 숙소 정보 리스트
    """
    async with AsyncSessionLocal() as db:
        try:
            from datetime import date as date_obj

            saved_accommodations = 0
            updated_accommodations = 0
            saved_dates = 0
            updated_dates = 0
            saved_today = 0
            updated_today = 0

            today_str = date_obj.today().isoformat()  # YYYY-MM-DD

            for acc_data in accommodations:
                # 1. Accommodation 저장/업데이트 (숙소 기본 정보)
                # URL에서 추출한 실제 숙소 ID 사용
                acc_id = acc_data.get("id")
                if not acc_id:
                    logger.warning(f"Skipping accommodation without ID: {acc_data.get('name')}")
                    continue

                # 기존 숙소 확인
                existing = await db.execute(
                    select(Accommodation).where(Accommodation.id == acc_id)
                )
                existing_acc = existing.scalar_one_or_none()

                if existing_acc:
                    # 업데이트
                    existing_acc.name = acc_data["name"]
                    existing_acc.region = acc_data.get("region", "Unknown")
                    existing_acc.address = acc_data.get("address")
                    existing_acc.contact = acc_data.get("contact")
                    existing_acc.website = acc_data.get("homepage")
                    if acc_data.get("accommodation_type"):
                        existing_acc.accommodation_type = acc_data.get("accommodation_type")
                    capacity_value = acc_data.get("capacity")
                    if capacity_value is not None:
                        existing_acc.capacity = capacity_value
                    if acc_data.get("summary") is not None:
                        existing_acc.summary = acc_data.get("summary")

                    # 이미지 URL 업데이트 (여러 개)
                    new_image_urls = acc_data.get("image_urls", [])
                    if new_image_urls:
                        existing_images = existing_acc.images or []
                        # 새로운 이미지 추가 (중복 제거)
                        for img_url in new_image_urls:
                            if img_url not in existing_images:
                                existing_images.append(img_url)
                        existing_acc.images = existing_images

                    existing_acc.updated_at = datetime.utcnow()
                    db.add(existing_acc)
                    updated_accommodations += 1
                else:
                    # 새로 생성
                    new_acc = Accommodation(
                        id=acc_id,
                        name=acc_data["name"],
                        region=acc_data.get("region", "Unknown"),
                        address=acc_data.get("address"),
                        contact=acc_data.get("contact"),
                        website=acc_data.get("homepage"),
                        images=acc_data.get("image_urls", []),  # 이미지 URL 리스트
                        accommodation_type=acc_data.get("accommodation_type"),
                        capacity=acc_data.get("capacity") or 2,  # 기본값
                        summary=acc_data.get("summary", []),
                    )
                    db.add(new_acc)
                    saved_accommodations += 1

                # 2. AccommodationDate 저장/업데이트 (날짜별 정보)
                date_booking_info = acc_data.get("date_booking_info", {})
                for date_str, booking_data in date_booking_info.items():
                    try:
                        # 날짜 파싱
                        date_parts = date_str.split("-")
                        if len(date_parts) != 3:
                            logger.warning(f"Invalid date format: {date_str}")
                            continue

                        year = int(date_parts[0])
                        month = int(date_parts[1])
                        day = int(date_parts[2])

                        # 날짜 객체 생성 (요일, 주차 계산용)
                        try:
                            date_value = date_obj(year, month, day)
                            weekday = date_value.weekday()  # 0=월요일, 6=일요일
                            week_number = date_value.isocalendar()[1]  # ISO week number
                        except ValueError:
                            logger.warning(f"Invalid date: {date_str}")
                            continue

                        # AccommodationDate ID 생성
                        date_id = f"{acc_id}_{date_str}"

                        # 기존 날짜 정보 확인
                        existing_date = await db.execute(
                            select(AccommodationDate).where(AccommodationDate.id == date_id)
                        )
                        existing_date_obj = existing_date.scalar_one_or_none()

                        if existing_date_obj:
                            # 업데이트
                            existing_date_obj.applicants = booking_data.get("applicants", 0)
                            existing_date_obj.score = booking_data.get("score", 0.0)
                            existing_date_obj.status = booking_data.get("status", "Unknown")
                            existing_date_obj.updated_at = datetime.utcnow()
                            db.add(existing_date_obj)
                            updated_dates += 1
                        else:
                            # 새로 생성
                            new_date = AccommodationDate(
                                id=date_id,
                                year=year,
                                month=month,
                                day=day,
                                weekday=weekday,
                                week_number=week_number,
                                date=date_str,
                                accommodation_id=acc_id,
                                applicants=booking_data.get("applicants", 0),
                                score=booking_data.get("score", 0.0),
                                status=booking_data.get("status", "Unknown")
                            )
                            db.add(new_date)
                            saved_dates += 1

                        # 3. TodayAccommodation 저장/업데이트 (오늘 날짜만)
                        if date_str == today_str:
                            today_id = f"today_{date_id}"

                            # 기존 오늘 정보 확인
                            existing_today = await db.execute(
                                select(TodayAccommodation).where(TodayAccommodation.id == today_id)
                            )
                            existing_today_obj = existing_today.scalar_one_or_none()

                            if existing_today_obj:
                                # 업데이트
                                existing_today_obj.applicants = booking_data.get("applicants", 0)
                                existing_today_obj.score = booking_data.get("score", 0.0)
                                existing_today_obj.status = booking_data.get("status", "Unknown")
                                existing_today_obj.updated_at = datetime.utcnow()
                                db.add(existing_today_obj)
                                updated_today += 1
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
                                    accommodation_id=acc_id,
                                    applicants=booking_data.get("applicants", 0),
                                    score=booking_data.get("score", 0.0),
                                    status=booking_data.get("status", "Unknown")
                                )
                                db.add(new_today)
                                saved_today += 1

                    except Exception as e:
                        logger.warning(f"Error saving date {date_str}: {str(e)}")
                        continue

            await db.commit()
            logger.info(f"Accommodations - Saved: {saved_accommodations}, Updated: {updated_accommodations}")
            logger.info(f"Accommodation Dates - Saved: {saved_dates}, Updated: {updated_dates}")
            logger.info(f"Today Accommodations - Saved: {saved_today}, Updated: {updated_today}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Database save error: {str(e)}", exc_info=True)
            raise


async def process_accommodation_crawling(
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Dict:
    """
    숙소 크롤링 배치 작업 메인 함수
    
    Args:
        username: lulu-lala 로그인 사용자명 (None이면 설정에서 로드)
        password: lulu-lala 로그인 비밀번호 (None이면 설정에서 로드)
    
    Returns:
        Dict: 작업 결과
    """
    # 설정에서 로드 (인자가 없을 경우)
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
    
    # RSA 공개키 확인
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
    async with async_playwright() as p:
        browser: Browser = None
        context: BrowserContext = None
        page: Page = None
        
        try:
            logger.info("Starting accommodation crawling batch job...")
            
            # 브라우저 시작
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # 단계 1: 로그인
            logger.info("=" * 50)
            logger.info("STEP 1: Logging in to lulu-lala...")
            logger.info("=" * 50)
            login_success = await login_to_lulu_lala(page, username, password, rsa_public_key)
            if not login_success:
                await page.screenshot(path="step1_login_failed.png", full_page=True)
                return {
                    "status": "error",
                    "message": "Login failed",
                    "step": "login",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 로그인 후 스크린샷 저장
            await page.screenshot(path="step1_login_success.png", full_page=True)
            logger.info("✓ Login successful. Screenshot saved: step1_login_success.png")
            logger.info(f"Current URL: {page.url}")
            
            # 단계 2: Refresh 아이콘 클릭 후 shbrefresh로 이동 및 RESERVATION 클릭
            logger.info("=" * 50)
            logger.info("STEP 2: Navigating to shbrefresh via Refresh icon...")
            logger.info("=" * 50)
            
            nav_success, page = await navigate_to_reservation_page(page, context)
            if not nav_success:
                logger.error("Failed to navigate to reservation page")
                return {
                    "status": "error",
                    "message": "Failed to navigate to reservation page",
                    "step": "navigation",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info(f"✓ Successfully navigated to reservation page: {page.url}")
            
            # 단계 3: 숙소 정보 크롤링
            logger.info("=" * 50)
            logger.info("STEP 3: Crawling accommodation information...")
            logger.info("=" * 50)
            accommodations = await crawl_accommodations(page)
            
            if not accommodations:
                logger.warning("No accommodations found")
                return {
                    "status": "warning",
                    "message": "No accommodations found",
                    "accommodations_count": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # DB에 저장
            await save_accommodations_to_db(accommodations)
            
            logger.info(f"Accommodation crawling completed: {len(accommodations)} accommodations")
            
            return {
                "status": "success",
                "accommodations_count": len(accommodations),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Accommodation crawling failed: {str(e)}", exc_info=True)
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
        # 설정에서 자동으로 로드됨 (환경 변수 또는 .env 파일)
        result = asyncio.run(process_accommodation_crawling())
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
