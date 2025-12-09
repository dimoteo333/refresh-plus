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
            winning_score_at_time=user.current_points
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
