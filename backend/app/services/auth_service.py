"""
인증 서비스

사용자 로그인, 토큰 생성/검증, 룰루랄라 인증을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.utils.encryption import encrypt_password, decrypt_password
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    JWTError
)
from app.batch.accommodation_crawler import (
    login_to_lulu_lala,
    navigate_to_reservation_page
)
from app.config import settings

from playwright.async_api import async_playwright
from dateutil import parser as date_parser
import uuid
import re

logger = logging.getLogger(__name__)


async def _fetch_user_info_from_lulu_lala(page) -> Dict[str, any]:
    """
    룰루랄라 마이페이지에서 사용자 정보 크롤링

    Args:
        page: Playwright Page 객체 (로그인 완료된 상태)

    Returns:
        Dict: {"name": str, "points": int}
    """
    try:
        # 포인트 조회 페이지로 이동
        logger.info("Navigating to mypage/point/view...")
        await page.goto("https://shbrefresh.interparkb2b.co.kr/mypage/point/view")
        await page.wait_for_load_state("networkidle")
        current_url = page.url.lower()
        if "login" in current_url:
            logger.warning("shbrefresh redirected to login page while fetching user info")

        # 사용자 이름 추출 (mem_profile 클래스)
        name_element = await page.query_selector(".mem_profile")
        user_name = "Unknown"
        if name_element:
            name_text = await name_element.text_content()
            # "OOO님 환영합니다." 형식에서 이름 추출
            if name_text:
                if "님" in name_text:
                    extracted = name_text.split("님")[0].strip()
                else:
                    extracted = name_text.strip().splitlines()[0]
                if extracted:
                    user_name = extracted
                    logger.info(f"Extracted user name: {user_name}")

        # 사용자 점수 추출 (href="/mypage/point/view"의 orange 색상 텍스트)
        points = 0.0
        # orange 클래스를 가진 요소 찾기
        orange_elements = await page.query_selector_all(".orange")
        for element in orange_elements:
            text = await element.text_content()
            if text:
                # 쉼표는 제거하고 소수점은 유지해 정확한 점수를 저장한다
                cleaned_text = text.strip().replace(",", "")
                cleaned_text = re.sub(r"[^0-9.]", "", cleaned_text)

                if cleaned_text.count(".") > 1:
                    # 1개 초과의 소수점이 있다면 첫 번째만 남기고 나머지는 제거
                    integer_part, decimal_part = cleaned_text.split(".", 1)
                    decimal_part = decimal_part.replace(".", "")
                    cleaned_text = f"{integer_part}.{decimal_part}"

                if cleaned_text:
                    try:
                        points = round(float(cleaned_text), 2)
                        logger.info(f"Extracted user points: {points}")
                        break
                    except ValueError:
                        logger.warning(f"Failed to parse points text: {text}")
                        continue

        return {
            "name": user_name,
            "points": points
        }

    except Exception as e:
        logger.error(f"Failed to fetch user info: {str(e)}", exc_info=True)
        # 실패해도 기본값 반환
        return {
            "name": "Unknown",
            "points": 0
        }


async def _fetch_reservations_from_lulu_lala(page) -> list[Dict[str, any]]:
    """
    룰루랄라 마이페이지에서 예약 내역 크롤링

    Args:
        page: Playwright Page 객체 (로그인 완료된 상태)

    Returns:
        List[Dict]: [{"reservation_number": str, "hotel_name": str, "check_in": str, "check_out": str, "status": str, "created_at": str}, ...]
    """
    try:
        # 예약 내역 페이지로 이동
        logger.info("Navigating to mypage/reservation/list...")
        await page.goto("https://shbrefresh.interparkb2b.co.kr/mypage/reservation/list")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)  # 추가 대기
        current_url = page.url.lower()
        if "login" in current_url:
            logger.warning("shbrefresh redirected to login page while fetching reservations")

        reservations = []

        name_label_keywords = ["숙소", "숙박시설", "상품", "호텔", "리조트", "펜션", "객실", "콘도", "풀빌라"]
        fallback_name_keywords = name_label_keywords + ["스테이", "하우스", "하우징"]
        checkin_keywords = ["체크인", "입실", "투숙시작", "이용시작", "사용시작"]
        checkout_keywords = ["체크아웃", "퇴실", "투숙종료", "이용종료", "사용종료"]
        range_keywords = ["숙박기간", "이용기간", "투숙기간", "사용기간"]
        created_keywords = ["신청일", "접수일", "예약일", "신청시간", "등록일"]
        status_keywords = ["상태", "진행", "완료", "취소", "당첨", "낙첨", "대기"]
        date_pattern = re.compile(r"\d{2,4}[./-]\d{1,2}[./-]\d{1,2}")

        def _normalize_text(value: str) -> str:
            return re.sub(r"\s+", "", value or "")

        def _clean_value(value: str) -> str:
            return re.sub(r"\s+", " ", value or "").strip()

        def _extract_value_by_keywords(line: str, keywords: list[str]) -> str:
            for keyword in keywords:
                if keyword in line:
                    return line.split(keyword, 1)[1].strip(" :：-~\t")
            return ""

        def _format_date_value(value: str) -> str:
            cleaned = _clean_value(value)
            if not cleaned:
                return ""

            cleaned_no_paren = re.sub(r"\([^)]*\)", "", cleaned)
            sanitized = re.sub(r"[^0-9./-]", " ", cleaned_no_paren)
            sanitized = re.sub(r"\s+", " ", sanitized).strip()

            candidates = []
            if sanitized:
                candidates.append(sanitized)
            candidates.extend(date_pattern.findall(cleaned_no_paren))

            for candidate in candidates:
                try:
                    parsed = date_parser.parse(candidate, yearfirst=True, dayfirst=False)
                    return parsed.strftime("%Y-%m-%d")
                except Exception:
                    continue

            return cleaned.strip()

        # order_state_box 클래스 요소들 찾기
        order_boxes = await page.query_selector_all(".order_state_box")
        logger.info(f"Found {len(order_boxes)} reservation boxes")

        for box in order_boxes:
            try:
                # 접수번호 추출 (href="/mypage/reservation/view?revNo=XXXXXX")
                link = await box.query_selector('a[href*="/mypage/reservation/view?revNo="]')
                reservation_number = ""
                if link:
                    href = await link.get_attribute("href")
                    if href and "revNo=" in href:
                        reservation_number = href.split("revNo=")[1].split("&")[0]
                        logger.info(f"Found reservation: {reservation_number}")

                if not reservation_number:
                    logger.warning("Reservation box without revNo detected, skipping")
                    continue

                # 전체 텍스트 가져오기
                full_text = await box.text_content()
                lines = [line.strip() for line in (full_text or "").split("\n") if line.strip()]

                hotel_name = ""
                check_in = ""
                check_out = ""
                status = ""
                created_at = ""

                # definition list 기반 정보 추출
                detail_rows = await box.query_selector_all("dl")
                for row in detail_rows:
                    try:
                        label_element = await row.query_selector("dt")
                        value_element = await row.query_selector("dd")
                        if not label_element or not value_element:
                            continue

                        label_text = await label_element.text_content()
                        value_text = await value_element.text_content()
                        label = _normalize_text(label_text or "")
                        value = _clean_value(value_text or "")
                        if not label or not value:
                            continue

                        if any(label.startswith(keyword) for keyword in name_label_keywords):
                            if not hotel_name:
                                hotel_name = value
                            continue

                        if any(label.startswith(keyword) for keyword in checkin_keywords):
                            formatted = _format_date_value(value)
                            if formatted:
                                check_in = check_in or formatted
                            continue

                        if any(label.startswith(keyword) for keyword in checkout_keywords):
                            formatted = _format_date_value(value)
                            if formatted:
                                check_out = check_out or formatted
                            continue

                        if any(label.startswith(keyword) for keyword in range_keywords):
                            if "~" in value:
                                start_text, end_text = value.split("~", 1)
                                start = _format_date_value(start_text)
                                end = _format_date_value(end_text)
                                if start:
                                    check_in = check_in or start
                                if end:
                                    check_out = check_out or end
                                continue

                        if any(label.startswith(keyword) for keyword in created_keywords):
                            formatted = _format_date_value(value)
                            if formatted:
                                created_at = created_at or formatted
                            continue

                    except Exception as parse_error:
                        logger.debug(f"Failed to parse detail row: {parse_error}")
                        continue

                # 텍스트 기반 보정 로직
                for i, line in enumerate(lines):
                    normalized_line = _normalize_text(line)
                    if not normalized_line:
                        continue

                    if not hotel_name and any(keyword in normalized_line for keyword in fallback_name_keywords):
                        candidate = _clean_value(_extract_value_by_keywords(line, fallback_name_keywords) or line)
                        if candidate:
                            hotel_name = candidate
                            continue

                    if not check_in and any(keyword in normalized_line for keyword in checkin_keywords):
                        candidate = _extract_value_by_keywords(line, checkin_keywords)
                        if not candidate and i + 1 < len(lines):
                            candidate = lines[i + 1]
                        formatted = _format_date_value(candidate)
                        if formatted:
                            check_in = formatted
                            continue

                    if not check_out and any(keyword in normalized_line for keyword in checkout_keywords):
                        candidate = _extract_value_by_keywords(line, checkout_keywords)
                        if not candidate and i + 1 < len(lines):
                            candidate = lines[i + 1]
                        formatted = _format_date_value(candidate)
                        if formatted:
                            check_out = formatted
                            continue

                    if not created_at and any(keyword in normalized_line for keyword in created_keywords):
                        candidate = _extract_value_by_keywords(line, created_keywords)
                        if not candidate and i + 1 < len(lines):
                            candidate = lines[i + 1]
                        formatted = _format_date_value(candidate)
                        if formatted:
                            created_at = formatted
                            continue

                    if not status and any(keyword in normalized_line for keyword in status_keywords):
                        status = line

                # 숙박기간 형태(YYYY.MM.DD ~ YYYY.MM.DD) 처리
                if (not check_in or not check_out):
                    for line in lines:
                        if "~" in line:
                            start_text, end_text = line.split("~", 1)
                            start = _format_date_value(start_text)
                            end = _format_date_value(end_text)
                            if start and not check_in:
                                check_in = start
                            if end and not check_out:
                                check_out = end
                            if check_in and check_out:
                                break

                if not hotel_name:
                    name_element = await box.query_selector(".order_state_tit, .order_subject, .order_info strong")
                    if name_element:
                        text = await name_element.text_content()
                        if text:
                            hotel_name = _clean_value(text)

                if not hotel_name and link:
                    link_text = await link.text_content()
                    if link_text:
                        hotel_name = _clean_value(link_text)

                reservations.append({
                    "reservation_number": reservation_number,
                    "hotel_name": hotel_name,
                    "check_in": check_in,
                    "check_out": check_out,
                    "status": status,
                    "created_at": created_at
                })

            except Exception as e:
                logger.error(f"Failed to parse reservation box: {str(e)}")
                continue

        logger.info(f"Extracted {len(reservations)} reservations")
        return reservations

    except Exception as e:
        logger.error(f"Failed to fetch reservations: {str(e)}", exc_info=True)
        return []


async def _save_reservations_to_db(
    reservations: list[Dict[str, any]],
    user_id: str,
    db: AsyncSession
):
    """
    크롤링한 예약 내역을 DB에 저장

    Args:
        reservations: 크롤링한 예약 내역 리스트
        user_id: 사용자 ID
        db: 데이터베이스 세션
    """
    try:
        saved_count = 0
        updated_count = 0

        for res in reservations:
            try:
                # 접수번호로 기존 예약 확인
                result = await db.execute(
                    select(Booking).where(
                        Booking.confirmation_number == res["reservation_number"]
                    )
                )
                existing_booking = result.scalar_one_or_none()

                # 날짜 파싱
                check_in_dt = None
                check_out_dt = None
                created_at_dt = datetime.utcnow()

                try:
                    if res["check_in"]:
                        check_in_dt = date_parser.parse(res["check_in"])
                    if res["check_out"]:
                        check_out_dt = date_parser.parse(res["check_out"])
                    if res["created_at"]:
                        created_at_dt = date_parser.parse(res["created_at"])
                except Exception as e:
                    logger.warning(f"Date parsing failed for reservation {res['reservation_number']}: {str(e)}")

                # 상태 매핑
                status = BookingStatus.PENDING
                status_text = res["status"].lower()
                if "완료" in status_text or "complete" in status_text:
                    status = BookingStatus.COMPLETED
                elif "취소" in status_text or "cancel" in status_text:
                    status = BookingStatus.CANCELLED
                elif "당첨" in status_text or "won" in status_text:
                    status = BookingStatus.WON
                elif "낙첨" in status_text or "lost" in status_text:
                    status = BookingStatus.LOST

                if existing_booking:
                    # 기존 예약 업데이트
                    existing_booking.accommodation_name = res["hotel_name"]
                    existing_booking.check_in = check_in_dt
                    existing_booking.check_out = check_out_dt
                    existing_booking.status = status
                    updated_count += 1
                    logger.info(f"Updated booking: {res['reservation_number']}")
                else:
                    # 새 예약 생성
                    new_booking = Booking(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        accommodation_name=res["hotel_name"],
                        check_in=check_in_dt,
                        check_out=check_out_dt,
                        status=status,
                        confirmation_number=res["reservation_number"],
                        is_from_crawler=True,
                        created_at=created_at_dt
                    )
                    db.add(new_booking)
                    saved_count += 1
                    logger.info(f"Created new booking: {res['reservation_number']}")

            except Exception as e:
                logger.error(f"Failed to save reservation {res.get('reservation_number')}: {str(e)}")
                continue

        await db.commit()
        logger.info(f"Saved {saved_count} new reservations, updated {updated_count} existing reservations")

    except Exception as e:
        logger.error(f"Failed to save reservations to DB: {str(e)}", exc_info=True)
        await db.rollback()


class AuthService:
    """인증 관련 비즈니스 로직"""

    async def login(
        self,
        username: str,
        password: str,
        db: AsyncSession,
        ip_address: Optional[str] = None
    ) -> Dict:
        """
        사용자 로그인

        1. 룰루랄라 사이트에 로그인 (8-10초)
        2. 성공 시 사용자 생성/업데이트
        3. JWT 토큰 발급
        4. 세션 쿠키 저장

        Args:
            username: 룰루랄라 사용자 ID
            password: 룰루랄라 비밀번호
            db: 데이터베이스 세션
            ip_address: 클라이언트 IP (로깅용)

        Returns:
            Dict: {access_token, refresh_token, token_type, user}

        Raises:
            ValueError: 로그인 실패 (잘못된 인증 정보)
            PermissionError: 계정 잠금
        """

        logger.info(f"Login attempt for user: {username} from IP: {ip_address}")

        # 1. 기존 사용자 조회
        result = await db.execute(
            select(User).where(User.lulu_lala_user_id == username)
        )
        user = result.scalar_one_or_none()

        # 2. 계정 잠금 확인
        if user and user.locked_until:
            if datetime.utcnow() < user.locked_until:
                remaining = (user.locked_until - datetime.utcnow()).seconds // 60
                raise PermissionError(
                    f"계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요."
                )
            else:
                # 잠금 해제
                user.locked_until = None
                user.failed_login_attempts = 0
                await db.commit()

        # 3. 룰루랄라 로그인 시도 (8-10초 소요)
        logger.info(f"Attempting Lulu-Lala login for {username}...")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()

                # 로그인 시도
                success = await login_to_lulu_lala(
                    page,
                    username,
                    password,
                    settings.LULU_LALA_RSA_PUBLIC_KEY
                )

                if not success:
                    # 로그인 실패
                    await browser.close()

                    # 실패 횟수 증가
                    if user:
                        user.failed_login_attempts += 1

                        # 5회 실패 시 30분 잠금
                        if user.failed_login_attempts >= 5:
                            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                            await db.commit()
                            logger.warning(f"Account locked for {username} due to failed attempts")
                            raise PermissionError(
                                "5회 로그인 실패로 계정이 30분간 잠겼습니다."
                            )

                        await db.commit()

                    logger.error(f"Lulu-Lala login failed for {username}")
                    raise ValueError("룰루랄라 로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.")

                # shbrefresh 세션 확보 (SSO)
                logger.info("Establishing shbrefresh session via Refresh portal...")
                shbrefresh_page = page
                try:
                    nav_success, nav_page = await navigate_to_reservation_page(
                        page,
                        context
                    )
                    if nav_success and nav_page:
                        shbrefresh_page = nav_page
                        logger.info("shbrefresh session established successfully")
                    else:
                        logger.warning("Unable to confirm shbrefresh navigation – proceeding with existing page")
                except Exception as nav_error:
                    logger.error(
                        f"Failed to navigate to shbrefresh reservation page: {str(nav_error)}",
                        exc_info=True
                    )

                # 사용자 정보 크롤링 (이름, 점수)
                logger.info("Fetching user info from Lulu-Lala...")
                user_info = await _fetch_user_info_from_lulu_lala(shbrefresh_page)

                # 예약 내역 크롤링
                logger.info("Fetching reservations from Lulu-Lala...")
                reservations = await _fetch_reservations_from_lulu_lala(shbrefresh_page)

                # 세션 쿠키 저장 (shbrefresh까지 포함)
                cookies = await context.cookies()
                session_cookies = [
                    {"name": c["name"], "value": c["value"], "domain": c["domain"]}
                    for c in cookies
                ]

                await browser.close()

        except Exception as e:
            if isinstance(e, (ValueError, PermissionError)):
                raise
            logger.error(f"Playwright error during login: {str(e)}", exc_info=True)
            raise ValueError(f"로그인 중 오류가 발생했습니다: {str(e)}")

        # 4. 사용자 생성 또는 업데이트
        if not user:
            # 새 사용자 생성
            user_id = f"user_{username}_{int(datetime.utcnow().timestamp())}"
            user = User(
                id=user_id,
                lulu_lala_user_id=username,
                name=user_info.get("name", username),  # 크롤링한 실제 이름
                encrypted_password=encrypt_password(password),
                is_verified=True,  # 로그인 성공 = 인증 완료
                is_active=True,
                session_cookies=session_cookies,
                session_expires_at=datetime.utcnow() + timedelta(hours=6),
                last_login=datetime.utcnow(),
                created_at=datetime.utcnow(),
                points=user_info.get("points", 100),  # 크롤링한 실제 점수
                available_nights=0
            )
            db.add(user)
            logger.info(f"Created new user: {user.id} (name: {user.name}, points: {user.points})")
        else:
            # 기존 사용자 업데이트
            user.encrypted_password = encrypt_password(password)
            user.name = user_info.get("name", user.name)  # 이름 업데이트
            user.points = user_info.get("points", user.points)  # 점수 업데이트
            user.is_verified = True
            user.session_cookies = session_cookies
            user.session_expires_at = datetime.utcnow() + timedelta(hours=6)
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0  # 리셋
            user.locked_until = None
            logger.info(f"Updated existing user: {user.id} (name: {user.name}, points: {user.points})")

        await db.commit()
        await db.refresh(user)

        # 4.5. 예약 내역 저장
        if reservations:
            logger.info(f"Saving {len(reservations)} reservations to DB...")
            await _save_reservations_to_db(reservations, user.id, db)

        # 5. JWT 토큰 생성
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "lulu_lala_user_id": user.lulu_lala_user_id
            }
        )

        refresh_token, jti = create_refresh_token(
            data={"user_id": user.id}
        )

        # 리프레시 토큰 저장
        user.refresh_token_jti = jti
        user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=7)
        await db.commit()

        logger.info(f"Login successful for user: {user.id}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "lulu_lala_user_id": user.lulu_lala_user_id,
                "points": user.points,
                "available_nights": user.available_nights,
                "is_verified": user.is_verified,
                "last_login": user.last_login
            }
        }

    async def get_user_from_token(
        self,
        token: str,
        db: AsyncSession
    ) -> Optional[User]:
        """
        JWT 토큰에서 사용자 조회

        Args:
            token: JWT 액세스 토큰
            db: 데이터베이스 세션

        Returns:
            User | None: 사용자 객체 (토큰이 유효하지 않으면 None)
        """
        try:
            payload = verify_token(token, token_type="access")
            user_id = payload.get("user_id")

            if not user_id:
                logger.warning("Token missing user_id claim")
                return None

            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                logger.warning(f"User not found or inactive: {user_id}")
                return None

            return user

        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}", exc_info=True)
            return None

    async def refresh_access_token(
        self,
        refresh_token: str,
        db: AsyncSession
    ) -> Dict:
        """
        리프레시 토큰으로 새 액세스 토큰 발급

        Args:
            refresh_token: 리프레시 토큰
            db: 데이터베이스 세션

        Returns:
            Dict: {access_token, token_type}

        Raises:
            ValueError: 리프레시 토큰이 유효하지 않거나 만료됨
        """
        try:
            payload = verify_token(refresh_token, token_type="refresh")
            user_id = payload.get("user_id")
            jti = payload.get("jti")

            if not user_id or not jti:
                raise ValueError("Invalid refresh token")

            # 리프레시 토큰 JTI 확인 (무효화 여부)
            result = await db.execute(
                select(User).where(
                    User.id == user_id,
                    User.refresh_token_jti == jti
                )
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Refresh token has been revoked for user: {user_id}")
                raise ValueError("Refresh token has been revoked")

            if not user.is_active:
                raise ValueError("User account is inactive")

            # 만료 확인
            if user.refresh_token_expires_at and user.refresh_token_expires_at < datetime.utcnow():
                logger.warning(f"Refresh token expired for user: {user_id}")
                raise ValueError("Refresh token expired")

            # 새 액세스 토큰 생성
            access_token = create_access_token(
                data={
                    "user_id": user.id,
                    "lulu_lala_user_id": user.lulu_lala_user_id
                }
            )

            logger.info(f"Access token refreshed for user: {user_id}")

            return {
                "access_token": access_token,
                "token_type": "bearer"
            }

        except JWTError as e:
            logger.warning(f"Refresh token verification failed: {str(e)}")
            raise ValueError(f"Invalid or expired refresh token: {str(e)}")
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
            raise ValueError(f"Token refresh failed: {str(e)}")

    async def logout(
        self,
        token: str,
        db: AsyncSession
    ):
        """
        로그아웃 - 리프레시 토큰 무효화

        Args:
            token: JWT 액세스 토큰
            db: 데이터베이스 세션
        """
        try:
            user = await self.get_user_from_token(token, db)

            if user:
                # 리프레시 토큰 무효화
                user.refresh_token_jti = None
                user.refresh_token_expires_at = None
                await db.commit()
                logger.info(f"User logged out: {user.id}")

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
            # 로그아웃은 실패해도 무시 (이미 무효화된 토큰일 수 있음)


# 싱글톤 인스턴스
auth_service = AuthService()
