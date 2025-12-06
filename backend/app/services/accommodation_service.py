from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List
from app.models.booking import Booking, BookingStatus
from app.models.accommodation import Accommodation
from app.models.today_accommodation import TodayAccommodation
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AccommodationService:

    async def can_user_book(
        self,
        user_id: str,
        accommodation_id: str,
        user_points: int,
        db: AsyncSession
    ) -> bool:
        """사용자가 현재 점수로 예약 가능한지 확인"""

        avg_score = await self.get_avg_winning_score_4weeks(accommodation_id, db)
        return user_points >= avg_score

    async def get_avg_winning_score_4weeks(
        self,
        accommodation_id: str,
        db: AsyncSession
    ) -> int:
        """최근 4주간 평균 당첨 점수 계산"""

        four_weeks_ago = datetime.now() - timedelta(weeks=4)

        result = await db.execute(
            select(func.avg(Booking.winning_score_at_time)).where(
                (Booking.accommodation_id == accommodation_id) &
                (Booking.status == BookingStatus.WON) &
                (Booking.created_at >= four_weeks_ago)
            )
        )

        avg_score = result.scalar()
        return int(avg_score) if avg_score else 0

    async def get_random_accommodations(
        self,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Accommodation]:
        """랜덤하게 숙소를 조회"""

        result = await db.execute(
            select(Accommodation)
            .order_by(func.random())
            .limit(limit)
        )

        return result.scalars().all()

    async def get_popular_accommodations(
        self,
        db: AsyncSession,
        limit: int = 5
    ):
        """실시간 인기 숙소 상위 N개 조회 (신청 가능한 숙소, score 기준 내림차순)"""

        result = await db.execute(
            select(
                TodayAccommodation,
                Accommodation
            )
            .join(
                Accommodation,
                TodayAccommodation.accommodation_id == Accommodation.id
            )
            .where(
                TodayAccommodation.status.in_([
                    "신청가능(최초 객실오픈)",
                    "신청중"
                ])
            )
            .order_by(TodayAccommodation.score.desc())
            .limit(limit)
        )

        return result.all()
