from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import uuid
from app.models.booking import Booking, BookingStatus
from app.models.accommodation import Accommodation
from app.models.user import User
from app.models.wishlist import Wishlist
from app.utils.logger import get_logger
from app.integrations.firebase_service import FirebaseService
from app.integrations.kakao_service import KakaoService

logger = get_logger(__name__)
firebase_service = FirebaseService()
kakao_service = KakaoService()

class BookingService:

    async def create_booking(
        self,
        user_id: str,
        accommodation_id: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        db: AsyncSession
    ) -> Booking:
        """예약 생성 (티켓팅)"""

        # 사용자 조회
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        # 숙소 조회
        acc_result = await db.execute(
            select(Accommodation).where(Accommodation.id == accommodation_id)
        )
        accommodation = acc_result.scalar_one_or_none()

        # 해당 날짜에 이미 예약한 사용자가 있는지 확인
        existing = await db.execute(
            select(Booking).where(
                (Booking.user_id == user_id) &
                (Booking.check_in == check_in) &
                (Booking.status.in_([BookingStatus.WON, BookingStatus.COMPLETED]))
            )
        )

        if existing.scalar_one_or_none():
            raise ValueError("User already has a booking for this date")

        # 예약 객체 생성 (PENDING 상태로 시작)
        booking = Booking(
            id=f"booking_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            accommodation_id=accommodation_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            status=BookingStatus.PENDING,
            winning_score_at_time=user.points
        )

        # DB 저장
        db.add(booking)
        user.total_bookings += 1
        db.add(user)
        await db.commit()
        await db.refresh(booking)

        logger.info(f"Booking created: {booking.id} - Status: PENDING")

        return booking

    async def _send_booking_notification(
        self,
        user: User,
        booking: Booking,
        accommodation: Accommodation,
        db: AsyncSession
    ):
        """예약 결과 알림 발송"""

        message = (
            f"🎉 당첨되셨습니다!\n{accommodation.name}\n"
            f"{booking.check_in.strftime('%Y.%m.%d')} ~ "
            f"{booking.check_out.strftime('%Y.%m.%d')}"
            if booking.status == BookingStatus.WON
            else f"😢 아쉽게 낙첨되셨습니다.\n{accommodation.name}"
        )

        # Firebase FCM (Android)
        if user.firebase_token:
            await firebase_service.send_notification(
                token=user.firebase_token,
                title="예약 결과",
                body=message,
                data={
                    "booking_id": booking.id,
                    "status": booking.status
                }
            )

        # Kakao Talk (iOS & PC)
        if user.kakao_user_id:
            await kakao_service.send_message(
                user_id=user.kakao_user_id,
                message=message
            )

    async def get_booking_history(
        self,
        user_id: str,
        status: str | None = None,
        db: AsyncSession = None
    ) -> list[Booking]:
        """사용자의 예약 이력 조회 (숙소 정보 포함)"""

        query = select(Booking).where(Booking.user_id == user_id)

        if status:
            query = query.where(Booking.status == BookingStatus[status.upper()])

        # 숙소 정보를 함께 로드
        query = query.options(joinedload(Booking.accommodation))
        query = query.order_by(Booking.created_at.desc())

        result = await db.execute(query)
        return result.scalars().unique().all()

    async def create_direct_reservation(
        self,
        user_id: str,
        accommodation_id: str,
        check_in_date: str,  # YYYY-MM-DD
        phone_number: str,   # 010-1234-5678
        db: AsyncSession
    ) -> dict:
        """lulu-lala에 직접 예약 요청 및 Booking 저장"""

        # 1. 시간 제한 체크 (08:00-21:00 KST)
        from app.utils.time_utils import is_reservation_time_allowed
        if not is_reservation_time_allowed():
            raise ValueError("예약은 08시~21시 사이에만 가능합니다.")

        # 2. 사용자 및 숙소 조회
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        accommodation_result = await db.execute(
            select(Accommodation).where(Accommodation.id == accommodation_id)
        )
        accommodation = accommodation_result.scalar_one_or_none()
        if not accommodation:
            raise ValueError("숙소를 찾을 수 없습니다.")

        # 3. session_cookies 확인
        if not user.session_cookies:
            raise ValueError("로그인 세션이 만료되었습니다. 다시 로그인해주세요.")

        # 4. 중복 예약 체크
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        existing = await db.execute(
            select(Booking).where(
                (Booking.user_id == user_id) &
                (Booking.check_in == check_in) &
                (Booking.status.in_([BookingStatus.WON, BookingStatus.COMPLETED]))
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("이미 해당 날짜에 예약이 존재합니다.")

        # 5. lulu-lala POST 요청
        import httpx
        from app.utils.phone_utils import parse_phone_number

        hp01, hp02, hp03 = parse_phone_number(phone_number)
        check_out = check_in + timedelta(days=1)

        # 쿠키 준비
        cookies = {c["name"]: c["value"] for c in user.session_cookies}

        # Form data
        form_data = {
            "bankerHp": phone_number.replace("-", ""),
            "submitFlag": "N",
            "checkinDate": check_in_date,
            "checkoutDate": check_out.strftime("%Y-%m-%d"),
            "rbroomNo": accommodation.accommodation_id,  # Body에는 accommodation_id 사용
            "rblockDate": check_in_date,
            "hp01": hp01,
            "hp02": hp02,
            "hp03": hp03,
            "privacy_check": "Y"
        }

        url = f"https://shbrefresh.interparkb2b.co.kr/condo/{accommodation.id}/reserve"

        logger.info(f"Sending direct reservation request to lulu-lala: {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    data=form_data,
                    cookies=cookies,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )

            # 6. 응답 확인 (302 Redirect면 성공)
            if response.status_code != 302:
                logger.error(f"Direct reservation failed: HTTP {response.status_code}")
                raise ValueError("예약에 실패했습니다. 다시 시도해주세요.")

            logger.info(f"Direct reservation HTTP 302 redirect received - Success!")

            # 7. Booking 생성 (WON 상태)
            booking = Booking(
                id=f"booking_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                accommodation_id=accommodation_id,
                check_in=check_in,
                check_out=check_out,
                guests=2,  # 기본값
                status=BookingStatus.WON,
                points_deducted=10,  # POINTS_PER_BOOKING
                winning_score_at_time=user.points,
                confirmation_number=f"DIRECT-{check_in.strftime('%Y%m%d')}-{user_id[:6]}",
                is_from_crawler=False
            )

            db.add(booking)
            db.add(user)
            await db.commit()
            await db.refresh(booking)

            logger.info(f"Direct reservation success: {booking.id}")

            return {
                "success": True,
                "booking_id": booking.id,
                "message": "예약에 성공했습니다. 해당 숙박에 대한 배정 결과는 익일 07시에 확인 가능합니다."
            }

        except httpx.TimeoutException:
            logger.error("Direct reservation timeout")
            raise ValueError("예약 요청 시간이 초과되었습니다. 다시 시도해주세요.")
        except httpx.RequestError as e:
            logger.error(f"Direct reservation request error: {str(e)}")
            raise ValueError("예약 요청 중 오류가 발생했습니다.")
        except Exception as e:
            logger.error(f"Direct reservation unexpected error: {str(e)}")
            raise ValueError("예약 처리 중 오류가 발생했습니다.")
