"""
룰루랄라 세션 매니저

세션 쿠키를 캐싱하여 예약 신청/취소 시 빠른 응답을 제공합니다.
- 첫 예약: 8-10초 (세션 생성)
- 이후 예약: <1초 (캐시 사용)
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from playwright.async_api import BrowserContext, async_playwright, Browser, Playwright
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.user import User
from app.utils.encryption import decrypt_password
from auth.lulu_lala_auth import login_to_lulu_lala, navigate_to_reservation_page
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """룰루랄라 세션 데이터"""
    cookies: list
    expires_at: datetime
    context: Optional[BrowserContext] = None


class LuluLalaSessionManager:
    """룰루랄라 세션 관리자"""

    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def initialize(self):
        """
        앱 시작 시 브라우저 초기화

        브라우저를 미리 실행해두면 세션 생성이 더 빠릅니다.
        """
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',  # Docker/메모리 제한 환경 최적화
                    '--no-sandbox',  # Docker 환경 호환성
                ]
            )
            logger.info("Playwright browser initialized for session management")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}", exc_info=True)

    async def shutdown(self):
        """앱 종료 시 브라우저 정리"""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("Playwright browser shut down")
        except Exception as e:
            logger.error(f"Error shutting down browser: {str(e)}", exc_info=True)

    async def get_session(
        self,
        user_id: str,
        db: AsyncSession
    ) -> SessionData:
        """
        사용자의 룰루랄라 세션 가져오기

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션

        Returns:
            SessionData: 유효한 세션 데이터

        Raises:
            ValueError: 사용자를 찾을 수 없거나 비밀번호가 없음
            RuntimeError: 세션 생성 실패
        """

        # 1. 캐시된 세션 확인
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if self._is_valid(session):
                logger.info(f"Using cached session for user {user_id}")
                return session
            else:
                logger.info(f"Cached session expired for user {user_id}, refreshing...")
                # 만료된 세션 제거
                del self.sessions[user_id]

        # 2. DB에서 세션 확인
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User not found: {user_id}")

        # DB에 저장된 세션이 유효한지 확인
        if user.session_cookies and user.session_expires_at:
            if datetime.utcnow() < user.session_expires_at:
                logger.info(f"Using session from DB for user {user_id}")
                session = SessionData(
                    cookies=user.session_cookies,
                    expires_at=user.session_expires_at
                )
                self.sessions[user_id] = session
                return session

        # 3. 새 세션 생성 필요
        logger.info(f"Creating new session for user {user_id} (8-10s)...")
        session = await self._create_session(user_id, db)
        self.sessions[user_id] = session
        return session

    def _is_valid(self, session: SessionData) -> bool:
        """세션이 유효한지 확인"""
        return datetime.utcnow() < session.expires_at

    async def _create_session(
        self,
        user_id: str,
        db: AsyncSession
    ) -> SessionData:
        """
        새 룰루랄라 세션 생성 (Playwright 사용, 8-10초 소요)

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션

        Returns:
            SessionData: 새로 생성된 세션

        Raises:
            ValueError: 비밀번호가 없거나 로그인 실패
        """

        # 사용자 정보 조회
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User not found: {user_id}")

        if not user.encrypted_password:
            raise ValueError(f"User has no stored password: {user_id}")

        # 비밀번호 복호화
        try:
            password = decrypt_password(user.encrypted_password)
        except Exception as e:
            logger.error(f"Failed to decrypt password for user {user_id}: {str(e)}")
            raise ValueError("Failed to decrypt password")

        # 브라우저 컨텍스트 생성
        try:
            if not self._browser:
                # 브라우저가 초기화되지 않은 경우 임시로 생성
                logger.warning("Browser not initialized, creating temporary browser")
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',  # Docker/메모리 제한 환경 최적화
                            '--no-sandbox',  # Docker 환경 호환성
                        ]
                    )
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080}
                    )
                    page = await context.new_page()

                    # 로그인 시도
                    success = await self._do_login(page, user, password)

                    if not success:
                        await browser.close()
                        raise RuntimeError(f"Login failed for user {user_id}")

                    # shbrefresh 세션 확보 (SSO)
                    logger.info("Establishing shbrefresh session via Refresh portal...")
                    try:
                        nav_success, nav_page = await navigate_to_reservation_page(page, context)
                        if nav_success and nav_page:
                            logger.info("shbrefresh session established successfully")
                        else:
                            logger.warning("Unable to confirm shbrefresh navigation – proceeding with existing cookies")
                    except Exception as nav_error:
                        logger.error(
                            f"Failed to navigate to shbrefresh reservation page: {str(nav_error)}",
                            exc_info=True
                        )

                    # 세션 쿠키 추출 (shbrefresh 쿠키 포함)
                    cookies = await context.cookies()
                    session_data = await self._save_session(user, cookies, db)

                    # 명시적으로 page, context, browser 닫기
                    await page.close()
                    await context.close()
                    await browser.close()
                    logger.info("Temporary browser resources closed")
                    return session_data
            else:
                # 기존 브라우저 사용 (더 빠름)
                context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()

                # 로그인 시도
                success = await self._do_login(page, user, password)

                if not success:
                    await context.close()
                    raise RuntimeError(f"Login failed for user {user_id}")

                # shbrefresh 세션 확보 (SSO)
                logger.info("Establishing shbrefresh session via Refresh portal...")
                try:
                    nav_success, nav_page = await navigate_to_reservation_page(page, context)
                    if nav_success and nav_page:
                        logger.info("shbrefresh session established successfully")
                    else:
                        logger.warning("Unable to confirm shbrefresh navigation – proceeding with existing cookies")
                except Exception as nav_error:
                    logger.error(
                        f"Failed to navigate to shbrefresh reservation page: {str(nav_error)}",
                        exc_info=True
                    )

                # 세션 쿠키 추출 (shbrefresh 쿠키 포함)
                cookies = await context.cookies()
                session_data = await self._save_session(user, cookies, db)

                # 페이지는 닫고, 컨텍스트는 유지 (세션 재사용 가능)
                await page.close()
                logger.info("Page closed, context kept for session reuse")
                session_data.context = context

                return session_data

        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def _do_login(self, page, user: User, password: str) -> bool:
        """Playwright로 룰루랄라 로그인"""
        try:
            return await login_to_lulu_lala(
                page,
                user.lulu_lala_user_id,
                password,
                settings.LULU_LALA_RSA_PUBLIC_KEY
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return False

    async def _save_session(
        self,
        user: User,
        cookies: list,
        db: AsyncSession
    ) -> SessionData:
        """세션 쿠키를 DB와 메모리에 저장"""

        session_data = SessionData(
            cookies=[
                {"name": c["name"], "value": c["value"], "domain": c["domain"]}
                for c in cookies
            ],
            expires_at=datetime.utcnow() + timedelta(hours=6)
        )

        # DB에 저장
        user.session_cookies = session_data.cookies
        user.session_expires_at = session_data.expires_at
        await db.commit()

        logger.info(f"Session created and saved for user {user.id}")

        return session_data

    async def invalidate_session(self, user_id: str, db: AsyncSession):
        """
        세션 무효화

        로그아웃 또는 비밀번호 변경 시 호출
        """
        # 메모리에서 제거
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if session.context:
                await session.context.close()
            del self.sessions[user_id]

        # DB에서 제거
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.session_cookies = None
            user.session_expires_at = None
            await db.commit()

        logger.info(f"Session invalidated for user {user_id}")

    async def background_session_warming(self, db: AsyncSession):
        """
        백그라운드 작업: 만료 임박 세션 갱신

        매 1시간마다 실행하여 세션을 미리 갱신합니다.
        """
        try:
            # 2시간 내 만료 예정인 세션 조회
            result = await db.execute(
                select(User).where(
                    User.session_expires_at < datetime.utcnow() + timedelta(hours=2),
                    User.session_expires_at > datetime.utcnow(),
                    User.is_verified == True,
                    User.encrypted_password.isnot(None)
                )
            )
            users = result.scalars().all()

            logger.info(f"Warming {len(users)} sessions...")

            for user in users:
                try:
                    await self.get_session(user.id, db)
                    logger.info(f"Warmed session for user {user.id}")
                except Exception as e:
                    logger.error(f"Failed to warm session for user {user.id}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in background session warming: {str(e)}", exc_info=True)


# 전역 싱글톤 인스턴스
session_manager = LuluLalaSessionManager()
