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
        # 이미지 및 불필요한 리소스 차단으로 속도 향상
        async def block_resources(route):
            if route.request.resource_type in ['image', 'stylesheet', 'font', 'media']:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_resources)
        logger.info("Resource blocking enabled (image, stylesheet, font, media)")

        logger.info("Navigating to login page: %s", LULU_LALA_LOGIN_URL)
        await page.goto(LULU_LALA_LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_selector("input#username", timeout=500)
        await page.wait_for_selector("input#password", timeout=500)

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
                await page.locator("button[type='submit']").click(timeout=1000)
                login_triggered = True
            except Exception:
                pass

        if await _wait_for_login_state(page):
            # 로그인 성공 후 페이지가 완전히 로드될 때까지 대기
            try:
                await page.wait_for_load_state("networkidle", timeout=1500)
                # 추가로 JavaScript 실행 완료 대기
                await page.wait_for_timeout(800)
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
    룰루랄라에서 shbrefresh 예약 페이지로 이동
    'Refresh' 텍스트가 포함된 링크를 찾아 클릭
    """
    try:
        async def handle_dialog(dialog):
            logger.info("Dialog detected: %s - %s", dialog.type, dialog.message[:100])
            await dialog.accept()

        page.on("dialog", handle_dialog)
        context.on("page", lambda new_page: new_page.on("dialog", handle_dialog))

        logger.info("Looking for 'Refresh' link on main page")

        # 새 페이지 감지를 위한 핸들러 설정
        shbrefresh_page = None

        def handle_new_page(new_page):
            nonlocal shbrefresh_page
            url = new_page.url
            if "shbrefresh" in url.lower() or "interparkb2b" in url.lower():
                if "error" not in url.lower() and "login" not in url.lower():
                    shbrefresh_page = new_page
                    logger.info(f"New shbrefresh page detected: {url}")

        context.on("page", handle_new_page)

        # 'Refresh' 텍스트가 포함된 링크 찾기 (대소문자 무시, 최대 30초 대기)
        try:
            # 메인 페이지와 모든 프레임에서 검색
            refresh_link = None

            # 먼저 메인 페이지에서 검색
            try:
                refresh_link = page.locator("a:has-text('Refresh'), a:has-text('refresh'), a:has-text('연성소')").first
                await refresh_link.wait_for(state="visible", timeout=5000)
                logger.info("Found 'Refresh' link in main page")
            except Exception:
                logger.info("'Refresh' link not found in main page, checking frames...")

                # 프레임에서 검색
                for idx, frame in enumerate(page.frames):
                    try:
                        refresh_link = frame.locator("a:has-text('Refresh'), a:has-text('refresh'), a:has-text('연성소')").first
                        await refresh_link.wait_for(state="visible", timeout=3000)
                        logger.info(f"Found 'Refresh' link in frame {idx}")
                        break
                    except Exception:
                        continue

            if not refresh_link:
                logger.error("'Refresh' link not found in any frame")
                return False, page

            # 링크 클릭
            logger.info("Clicking 'Refresh' link...")
            await refresh_link.click()

        except Exception as e:
            logger.error(f"Error finding or clicking 'Refresh' link: {e}")
            return False, page

        # shbrefresh 페이지로 이동했는지 확인 (최대 15초 대기)
        for _ in range(30):
            await page.wait_for_timeout(500)

            # 새 페이지가 열렸는지 확인
            if shbrefresh_page:
                try:
                    await shbrefresh_page.wait_for_load_state("networkidle", timeout=2000)
                    logger.info(f"Successfully navigated to shbrefresh page: {shbrefresh_page.url}")
                    return True, shbrefresh_page
                except Exception as e:
                    logger.warning(f"Page load timeout: {e}")
                    return True, shbrefresh_page

            # 현재 페이지 URL 확인
            current_url = page.url
            if "shbrefresh" in current_url.lower() or "interparkb2b" in current_url.lower():
                if "error" not in current_url.lower() and "login" not in current_url.lower():
                    logger.info(f"Successfully navigated to shbrefresh page: {current_url}")
                    return True, page

            # 새로 열린 페이지들 확인
            for p in context.pages:
                try:
                    p_url = p.url
                    if "shbrefresh" in p_url.lower() or "interparkb2b" in p_url.lower():
                        if "error" not in p_url.lower() and "login" not in p_url.lower():
                            await p.wait_for_load_state("networkidle", timeout=2000)
                            logger.info(f"Successfully navigated to shbrefresh page: {p_url}")
                            return True, p
                except Exception:
                    continue

        logger.error("Failed to detect shbrefresh page after clicking 'Refresh' link")
        logger.error(f"Current URL: {page.url}")
        return False, page

    except Exception as e:
        logger.error("Navigation error: %s", e, exc_info=True)
        return False, page
