from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, case
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.booking import Booking, BookingStatus
from app.models.accommodation import Accommodation
from app.models.today_accommodation import TodayAccommodation
from app.models.accommodation_date import AccommodationDate
from app.models.wishlist import Wishlist
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

    async def search_accommodations(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        keyword: Optional[str] = None,
        limit: int = 50
    ):
        """
        숙소 검색 (지역, 숙소명)
        - keyword가 없으면 region="서울"인 숙소를 우선 표시
        - keyword가 있으면 지역 또는 숙소명으로 검색
        - user_id가 없으면 즐겨찾기 정보는 false로 반환
        """

        # 기본 쿼리
        query = select(Accommodation)

        if keyword and keyword.strip():
            # 검색어가 있으면 지역 또는 숙소명으로 검색
            search_pattern = f"%{keyword.strip()}%"
            query = query.where(
                or_(
                    Accommodation.region.like(search_pattern),
                    Accommodation.name.like(search_pattern)
                )
            )
        else:
            # 검색어가 없으면 서울 지역 우선 표시
            query = query.order_by(
                # region이 '서울'이면 0, 아니면 1 (서울이 먼저 오도록)
                case(
                    (Accommodation.region == "서울", 0),
                    else_=1
                ),
                Accommodation.name
            )

        query = query.limit(limit)
        result = await db.execute(query)
        accommodations = result.scalars().all()

        # 각 숙소에 대해 평균 점수, 즐겨찾기 정보 조회
        search_results = []
        for accommodation in accommodations:
            # 평균 점수 계산 (마감(신청종료) 상태의 날짜들만)
            avg_score_result = await db.execute(
                select(func.avg(AccommodationDate.score))
                .where(
                    (AccommodationDate.accommodation_id == accommodation.id) &
                    (AccommodationDate.status == "마감(신청종료)")
                )
            )
            avg_score = avg_score_result.scalar()

            # 즐겨찾기 정보 조회 (user_id가 있는 경우만)
            is_wishlisted = False
            notify_enabled = False
            if user_id:
                wishlist_result = await db.execute(
                    select(Wishlist)
                    .where(
                        (Wishlist.user_id == user_id) &
                        (Wishlist.accommodation_id == accommodation.id) &
                        (Wishlist.is_active == True)
                    )
                )
                wishlist = wishlist_result.scalar_one_or_none()
                is_wishlisted = wishlist is not None
                notify_enabled = wishlist.notify_enabled if wishlist else False

            # 첫 번째 이미지 추출
            first_image = accommodation.images[0] if accommodation.images else None
            summary = (accommodation.summary or [])[:5]

            search_results.append({
                "id": accommodation.id,
                "name": accommodation.name,
                "region": accommodation.region,
                "accommodation_type": accommodation.accommodation_type,
                "first_image": first_image,
                "summary": summary,
                "avg_score": round(avg_score, 1) if avg_score else None,
                "is_wishlisted": is_wishlisted,
                "notify_enabled": notify_enabled
            })

        return search_results

    async def get_available_dates(
        self,
        accommodation_id: str,
        db: AsyncSession
    ) -> List[dict]:
        """
        예약 가능한 날짜 조회 (today_accommodation_info)
        - status='신청중' 또는 '신청가능(최초 객실오픈)' 상태만 조회
        - 날짜 순으로 정렬
        """

        result = await db.execute(
            select(TodayAccommodation)
            .where(
                (TodayAccommodation.accommodation_id == accommodation_id) &
                (TodayAccommodation.status.in_([
                    "신청중",
                    "신청가능(최초 객실오픈)"
                ]))
            )
            .order_by(TodayAccommodation.date)
        )

        dates = result.scalars().all()

        return [
            {
                "date": date.date,
                "score": date.score,
                "applicants": date.applicants,
                "status": date.status,
                "weekday": date.weekday
            }
            for date in dates
        ]

    async def get_weekday_averages(
        self,
        accommodation_id: str,
        db: AsyncSession
    ) -> List[dict]:
        """
        요일별 평균 점수 조회 (accommodation_dates)
        - status='마감(신청종료)' 상태만 조회
        - 요일별로 그룹화하여 평균 점수 계산
        """

        # 최근 3개월 데이터만 사용
        three_months_ago = datetime.now() - timedelta(days=90)
        three_months_ago_str = three_months_ago.strftime("%Y-%m-%d")

        result = await db.execute(
            select(
                AccommodationDate.weekday,
                func.avg(AccommodationDate.score).label('avg_score'),
                func.count(AccommodationDate.id).label('count')
            )
            .where(
                (AccommodationDate.accommodation_id == accommodation_id) &
                (AccommodationDate.status == "마감(신청종료)") &
                (AccommodationDate.date >= three_months_ago_str)
            )
            .group_by(AccommodationDate.weekday)
            .order_by(AccommodationDate.weekday)
        )

        weekday_data = result.all()

        # 요일 이름 매핑 (0=월요일, 6=일요일)
        weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

        return [
            {
                "weekday": data.weekday,
                "weekday_name": weekday_names[data.weekday] if data.weekday is not None else "",
                "avg_score": round(data.avg_score, 1) if data.avg_score else 0.0,
                "count": data.count
            }
            for data in weekday_data
        ]

    async def get_accommodation_detail(
        self,
        accommodation_id: str,
        db: AsyncSession
    ) -> Optional[dict]:
        """
        숙소 상세 정보 조회
        - 기본 정보 + 예약 가능 날짜 + 요일별 평균 점수
        """

        # 숙소 조회
        result = await db.execute(
            select(Accommodation).where(Accommodation.id == accommodation_id)
        )
        accommodation = result.scalar_one_or_none()

        if not accommodation:
            return None

        # 예약 가능 날짜 조회
        available_dates = await self.get_available_dates(accommodation_id, db)

        # 요일별 평균 점수 조회
        weekday_averages = await self.get_weekday_averages(accommodation_id, db)

        return {
            "id": accommodation.id,
            "name": accommodation.name,
            "region": accommodation.region,
            "address": accommodation.address,
            "contact": accommodation.contact,
            "website": accommodation.website,
            "accommodation_type": accommodation.accommodation_type,
            "capacity": accommodation.capacity,
            "images": accommodation.images or [],
            "summary": (accommodation.summary or [])[:5],
            "available_dates": available_dates,
            "weekday_averages": weekday_averages
        }
