"""
공통 룰루랄라 인증 유틸리티

- 브라우저 크롤러와 사용자 로그인 플로우가 공유하는 인증 로직을 모듈화
- RSA 암호화 헬퍼, Playwright 기반 로그인 제공
"""

from __future__ import annotations

import base64
import logging
from typing import Optional
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from playwright.async_api import BrowserContext, Page

logger = logging.getLogger(__name__)

LULU_LALA_LOGIN_URL = "https://lulu-lala.zzzmobile.co.kr/login.html"


def encrypt_rsa(plaintext: str, public_key_pem: str) -> str:
    """RSA 공개키로 텍스트 암호화"""
    key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(plaintext.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


async def _wait_for_login_state(page: Page, timeout: int = 12000) -> bool:
    """
    access_token 쿠키 또는 로그인 페이지 이탈을 명시적으로 대기
    """
    try:
        await page.wait_for_function(
            "() => document.cookie.includes('access_token') || "
            "!(window.location && window.location.href && window.location.href.toLowerCase().includes('login'))",
            timeout=timeout,
        )
        return True
    except Exception:
        try:
            cookies = await page.context.cookies()
            return any(c.get("name") == "access_token" for c in cookies)
        except Exception:
            return False


async def login_to_lulu_lala(
    page: Page,
    username: str,
    password: str,
    rsa_public_key: Optional[str] = None,
) -> bool:
    """
    룰루랄라 웹사이트 로그인
    Playwright UI 기반 로그인 (명시적 대기)
    """
    try:
        logger.info("Navigating to login page: %s", LULU_LALA_LOGIN_URL)
        await page.goto(LULU_LALA_LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_selector("input#username", timeout=8000)
        await page.wait_for_selector("input#password", timeout=8000)

        username_input = page.locator("input#username")
        password_input = page.locator("input#password")
        await username_input.fill(username)
        await password_input.fill(password)

        login_triggered = False
        try:
            login_result = await page.evaluate(
                """async ({u, p}) => {
                    if (typeof login === 'function') {
                        try {
                            await login(u, p);
                            return { success: true, message: 'login() invoked' };
                        } catch (e) {
                            return { success: false, message: e.toString() };
                        }
                    }
                    const loginLink = document.querySelector('a[href*="login("], a.login, button.login, button[type="submit"]');
                    if (loginLink) {
                        loginLink.click();
                        return { success: true, message: 'login element clicked' };
                    }
                    const form = document.querySelector('form');
                    if (form) {
                        form.requestSubmit ? form.requestSubmit() : form.submit();
                        return { success: true, message: 'form submitted' };
                    }
                    return { success: false, message: 'no login hook found' };
                }""",
                {"u": username, "p": password},
            )
            login_triggered = login_result.get("success", False)
            if not login_triggered:
                logger.warning("Login JS hook not found: %s", login_result)
        except Exception as e:
            logger.warning("JavaScript login invocation failed: %s", e)

        if not login_triggered:
            try:
                await page.locator("button[type='submit']").click(timeout=5000)
                login_triggered = True
            except Exception:
                pass

        if await _wait_for_login_state(page):
            # 로그인 성공 후 페이지가 완전히 로드될 때까지 대기
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
                # 추가로 JavaScript 실행 완료 대기
                await page.wait_for_timeout(2000)
                logger.info("Login successful, page fully loaded")
            except Exception as e:
                logger.warning(f"Page load timeout after login: {e}")
            return True

        await page.wait_for_load_state("networkidle")
        cookies = await page.context.cookies()
        return any(c.get("name") == "access_token" for c in cookies)

    except Exception as e:
        logger.error("Login error: %s", e, exc_info=True)
        return False


async def navigate_to_reservation_page(page: Page, context: BrowserContext) -> tuple[bool, Page]:
    """
    룰루랄라에서 shbrefresh 예약 페이지로 이동 (명시적 대기 기반)
    """
    try:
        async def handle_dialog(dialog):
            logger.info("Dialog detected: %s - %s", dialog.type, dialog.message[:100])
            await dialog.accept()

        page.on("dialog", handle_dialog)
        context.on("page", lambda new_page: new_page.on("dialog", handle_dialog))

        logger.info("Looking for Refresh (연성소) entry point on main page")

        # 디버깅: 현재 페이지 스크린샷
        try:
            await page.screenshot(path="debug_login_page.png", full_page=True)
            logger.info("Screenshot saved: debug_login_page.png")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")

        frames = [page] + list(page.frames)
        refresh_element = None
        found_in_frame: Optional[Page] = None

        logger.info(f"Searching in {len(frames)} frames (main page + {len(frames)-1} iframes)")

        for idx, frame in enumerate(frames):
            try:
                await frame.wait_for_load_state("domcontentloaded")
                all_links = await frame.query_selector_all(
                    "a, button, [role='button'], [onclick], img"
                )
                logger.info(f"Frame {idx}: Found {len(all_links)} clickable elements")

                for element in all_links:
                    try:
                        text = await element.inner_text() if hasattr(element, "inner_text") else ""
                        href = await element.get_attribute("href") or ""
                        title = await element.get_attribute("title") or ""
                        alt = await element.get_attribute("alt") or ""
                        src = await element.get_attribute("src") or ""
                        combined_text = f"{text} {href} {title} {alt} {src}".lower()

                        # 디버깅: "refresh", "연성소", "shb" 등이 포함된 요소 로깅
                        if any(keyword in combined_text for keyword in ["refresh", "연성소", "shb", "gmidas"]):
                            logger.debug(f"Potential match: text='{text[:30]}', href='{href[:50]}', title='{title[:30]}', alt='{alt[:30]}', src='{src[:50]}'")

                        # 검색 조건
                        if "sh_gmidas" in combined_text or \
                           ("shbrefresh" in combined_text and "vservice" in combined_text) or \
                           ("연성소" in combined_text) or \
                           ("refresh" in combined_text and "shb" in combined_text):
                            refresh_element = element
                            found_in_frame = frame
                            logger.info(f"Found Refresh element in frame {idx}: text='{text[:50]}', href='{href[:80]}'")
                            break
                    except Exception as e:
                        logger.debug(f"Error processing element: {e}")
                        continue
                if refresh_element:
                    break
            except Exception as e:
                logger.warning(f"Error processing frame {idx}: {e}")
                continue

        if not refresh_element:
            logger.error("Refresh (연성소) icon not found after searching all frames")
            logger.error(f"Current URL: {page.url}")
            return False, page

        pages_before = len(context.pages)
        shbrefresh_page = None
        shbrefresh_detected = False

        def handle_new_page(new_page):
            nonlocal shbrefresh_page
            url = new_page.url
            if "shbrefresh" in url.lower() or "interparkb2b" in url.lower():
                if "error" not in url.lower() and "login" not in url.lower():
                    shbrefresh_page = new_page

        context.on("page", handle_new_page)

        if found_in_frame and found_in_frame != page:
            try:
                await refresh_element.click(timeout=5000)
            except Exception:
                await refresh_element.evaluate("el => el.click()")
        else:
            await refresh_element.scroll_into_view_if_needed()
            await refresh_element.click()

        for _ in range(30):
            await page.wait_for_timeout(500)
            if shbrefresh_page:
                await shbrefresh_page.wait_for_load_state("networkidle", timeout=10000)
                return True, shbrefresh_page

            current_url = page.url
            if "shbrefresh" in current_url.lower() or "interparkb2b" in current_url.lower():
                if "error" not in current_url.lower() and "login" not in current_url.lower():
                    return True, page

            if len(context.pages) > pages_before:
                for p in context.pages:
                    try:
                        p_url = p.url
                        if "shbrefresh" in p_url.lower() or "interparkb2b" in p_url.lower():
                            if "error" not in p_url.lower() and "login" not in p_url.lower():
                                await p.wait_for_load_state("networkidle", timeout=10000)
                                return True, p
                    except Exception:
                        continue

        logger.error("Failed to detect shbrefresh page; cannot proceed to reservation index")
        return False, page

    except Exception as e:
        logger.error("Navigation error: %s", e, exc_info=True)
        return False, page
