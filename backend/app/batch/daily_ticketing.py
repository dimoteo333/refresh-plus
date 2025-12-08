"""
매일 00:00에 실행되는 배치 작업
- 각 숙소별로 당일 예약 티켓팅 수행
- 예약 가능한 사용자 중 점수가 높은 순서대로 당첨 결정
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.accommodation import Accommodation
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def process_daily_ticketing():
    """
    매일 00:00에 실행
    - PENDING 상태의 모든 예약을 검토
    - 숙소별로 점수 높은 사용자를 WON으로 변경
    - 나머지는 LOST로 변경
    """

    async with AsyncSessionLocal() as db:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        try:
            # 오늘 PENDING 상태의 모든 예약 조회
            pending_bookings = await db.execute(
                select(Booking)
                .where(
                    (Booking.status == BookingStatus.PENDING) &
                    (Booking.check_in >= datetime.combine(today, datetime.min.time())) &
                    (Booking.check_in < datetime.combine(tomorrow, datetime.min.time()))
                )
                .order_by(Booking.accommodation_id, User.current_points.desc())
            )
            bookings = pending_bookings.scalars().all()

            # 숙소별로 그룹화
            bookings_by_accommodation = {}
            for booking in bookings:
                if booking.accommodation_id not in bookings_by_accommodation:
                    bookings_by_accommodation[booking.accommodation_id] = []
                bookings_by_accommodation[booking.accommodation_id].append(booking)

            # 숙소별로 처리
            for accommodation_id, accommodation_bookings in bookings_by_accommodation.items():
                # 점수 높은 순서로 정렬
                sorted_bookings = sorted(
                    accommodation_bookings,
                    key=lambda b: b.winning_score_at_time,
                    reverse=True
                )

                # 첫 번째 (점수 가장 높은)는 당첨, 나머지는 낙첨
                for idx, booking in enumerate(sorted_bookings):
                    if idx == 0:
                        booking.status = BookingStatus.WON

                        # 사용자 점수 차감
                        user_result = await db.execute(
                            select(User).where(User.id == booking.user_id)
                        )
                        user = user_result.scalar_one()
                        user.points -= 10  # 버그 수정: current_points → points
                        user.successful_bookings += 1
                        booking.points_deducted = 10
                        booking.confirmation_number = (
                            f"REFRESH-{today.strftime('%Y%m%d')}-{booking.user_id[:6].upper()}"
                        )
                    else:
                        booking.status = BookingStatus.LOST

                    db.add(booking)

            await db.commit()

            logger.info(
                f"Daily ticketing completed: "
                f"{len(bookings_by_accommodation)} accommodations, "
                f"{len(bookings)} bookings processed"
            )

            return {
                "status": "success",
                "accommodations_processed": len(bookings_by_accommodation),
                "bookings_processed": len(bookings),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Daily ticketing failed: {str(e)}", exc_info=True)
            raise

def handler(event, context):
    """AWS Lambda 핸들러"""
    import asyncio

    try:
        result = asyncio.run(process_daily_ticketing())
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
