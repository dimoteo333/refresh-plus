from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, case, exists
from datetime import datetime, timedelta
from typing import List, Optional
from langchain_openai import ChatOpenAI
from app.models.booking import Booking, BookingStatus
from app.models.accommodation import Accommodation
from app.models.today_accommodation import TodayAccommodation
from app.models.accommodation_date import AccommodationDate
from app.models.wishlist import Wishlist
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

class AccommodationService:

    def __init__(self):
        """Optional LLM 초기화 (OpenAI 키가 있을 때만)"""
        openai_api_key = settings.OPENAI_API_KEY
        self.llm = None
        if openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    model=settings.RAG_MODEL or "gpt-4o-mini",
                    temperature=0.2,
                    openai_api_key=openai_api_key,
                )
            except Exception as e:
                logger.warning(f"OpenAI 클라이언트 초기화 실패: {e}")

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
        region: Optional[str] = None,
        sort_by: str = "avg_score",
        sort_order: str = "desc",
        available_only: bool = False,
        date: Optional[str] = None,
        limit: int = 50
    ):
        """
        숙소 검색 (지역, 숙소명)
        - keyword가 있으면 지역 또는 숙소명으로 검색
        - region 파라미터로 특정 지역 필터링 (전체/all/빈값은 무시)
        - sort_by: avg_score(평균 점수), name(가나다순), wishlist(즐겨찾기 우선), price(온라인 평균가), sol_score(추후 추가)
        - sort_order: asc/desc
        - available_only: today_accommodation_info에 신청 가능/신청중 상태가 있는 숙소만
        - date: 특정 날짜 필터링 (YYYY-MM-DD 형식), 제공 시 today_accommodation_info 기준 조회
        - user_id가 없으면 즐겨찾기 정보는 false로 반환
        """

        normalized_region = region.strip() if region else None
        if normalized_region in ["전체", "all", "ALL", "All", ""]:
            normalized_region = None

        # 평균 점수 서브쿼리 (마감된 날짜만)
        avg_score_subquery = (
            select(
                AccommodationDate.accommodation_id.label("accommodation_id"),
                func.avg(AccommodationDate.score).label("avg_score")
            )
            .where(AccommodationDate.status == "마감(신청종료)")
            .group_by(AccommodationDate.accommodation_id)
            .subquery()
        )

        # 온라인 평균가 서브쿼리 (가격순 정렬용)
        avg_price_subquery = (
            select(
                AccommodationDate.accommodation_id.label("accommodation_id"),
                func.avg(AccommodationDate.online_price).label("avg_price")
            )
            .where(AccommodationDate.online_price.isnot(None))
            .group_by(AccommodationDate.accommodation_id)
            .subquery()
        )

        # 즐겨찾기 서브쿼리 (사용자 있는 경우만)
        wishlist_subquery = None
        if user_id:
            wishlist_subquery = (
                select(
                    Wishlist.accommodation_id.label("accommodation_id"),
                    func.max(
                        case(
                            (Wishlist.is_active == True, 1),
                            else_=0
                        )
                    ).label("is_wishlisted"),
                    func.max(
                        case(
                            ((Wishlist.is_active == True) & (Wishlist.notify_enabled == True), 1),
                            else_=0
                        )
                    ).label("notify_enabled"),
                )
                .where((Wishlist.user_id == user_id) & (Wishlist.is_active == True))
                .group_by(Wishlist.accommodation_id)
                .subquery()
            )

        # 날짜별 오늘 숙소 정보 서브쿼리 (date 파라미터 제공 시)
        today_acc_subquery = None
        if date:
            today_acc_subquery = (
                select(
                    TodayAccommodation.accommodation_id.label("accommodation_id"),
                    TodayAccommodation.date.label("date"),
                    TodayAccommodation.applicants.label("applicants"),
                    TodayAccommodation.score.label("score"),
                    TodayAccommodation.status.label("status")
                )
                .where(
                    (TodayAccommodation.date == date) &
                    (TodayAccommodation.status.in_([
                        "신청중",
                        "신청가능(최초 객실오픈)",
                        "신청가능(상시 신청중)"
                    ]))
                )
                .subquery()
            )

        # 기본 쿼리
        query = (
            select(
                Accommodation,
                avg_score_subquery.c.avg_score.label("avg_score"),
                avg_price_subquery.c.avg_price.label("avg_price"),
            )
            .join(
                avg_score_subquery,
                avg_score_subquery.c.accommodation_id == Accommodation.id,
                isouter=True
            )
            .join(
                avg_price_subquery,
                avg_price_subquery.c.accommodation_id == Accommodation.id,
                isouter=True
            )
        )

        # 날짜별 정보 조인 (date 파라미터 제공 시)
        if today_acc_subquery is not None:
            query = (
                query.add_columns(
                    today_acc_subquery.c.date.label("today_date"),
                    today_acc_subquery.c.applicants.label("today_applicants"),
                    today_acc_subquery.c.score.label("today_score"),
                    today_acc_subquery.c.status.label("today_status")
                )
                .join(
                    today_acc_subquery,
                    today_acc_subquery.c.accommodation_id == Accommodation.id,
                    isouter=False  # INNER JOIN: 해당 날짜에 데이터가 있는 숙소만 조회
                )
            )

        if wishlist_subquery is not None:
            query = (
                query.add_columns(
                    wishlist_subquery.c.is_wishlisted.label("is_wishlisted"),
                    wishlist_subquery.c.notify_enabled.label("notify_enabled")
                )
                .join(
                    wishlist_subquery,
                    wishlist_subquery.c.accommodation_id == Accommodation.id,
                    isouter=True
                )
            )

        if keyword and keyword.strip():
            # 검색어가 있으면 지역 또는 숙소명으로 검색
            search_pattern = f"%{keyword.strip()}%"
            query = query.where(
                or_(
                    Accommodation.region.like(search_pattern),
                    Accommodation.name.like(search_pattern)
                )
            )

        if normalized_region:
            query = query.where(Accommodation.region == normalized_region)

        if available_only:
            available_statuses = [
                "신청중",
                "신청가능(최초 객실오픈)",
                "신청가능(상시 신청중)"
            ]
            availability_exists = (
                select(TodayAccommodation.id)
                .where(
                    (TodayAccommodation.accommodation_id == Accommodation.id) &
                    (TodayAccommodation.status.in_(available_statuses))
                )
                .limit(1)
            )
            query = query.where(exists(availability_exists))

        normalized_sort = (sort_by or "default").lower()
        normalized_order = "asc" if (sort_order or "").lower() == "asc" else "desc"

        def order_direction(column):
            return column.asc() if normalized_order == "asc" else column.desc()

        if normalized_sort == "avg_score":
            query = query.order_by(
                order_direction(func.coalesce(avg_score_subquery.c.avg_score, 0)),
                Accommodation.name
            )
        elif normalized_sort == "name":
            query = query.order_by(order_direction(Accommodation.name))
        elif normalized_sort == "wishlist" and wishlist_subquery is not None:
            query = query.order_by(
                order_direction(func.coalesce(wishlist_subquery.c.is_wishlisted, 0)),
                order_direction(func.coalesce(avg_score_subquery.c.avg_score, 0)),
                Accommodation.name
            )
        elif normalized_sort == "price":
            query = query.order_by(
                order_direction(func.coalesce(avg_price_subquery.c.avg_price, 0)),
                Accommodation.name
            )
        elif normalized_sort == "sol_score":
            # TODO: sol_score 적용 시 필드에 맞춰 정렬 로직 업데이트
            query = query.order_by(
                order_direction(func.coalesce(avg_score_subquery.c.avg_score, 0)),
                Accommodation.name
            )
        else:
            query = query.order_by(
                order_direction(func.coalesce(avg_score_subquery.c.avg_score, 0)),
                Accommodation.name
            )

        query = query.limit(limit)
        result = await db.execute(query)
        rows = result.all()

        # 각 숙소에 대해 평균 점수, 즐겨찾기 정보, 날짜별 정보 조합
        search_results = []
        for row in rows:
            # 날짜 정보 포함 여부에 따라 row 구조가 다름
            if today_acc_subquery is not None and wishlist_subquery is not None:
                accommodation, avg_score, avg_price, today_date, today_applicants, today_score, today_status, is_wishlisted_raw, notify_enabled_raw = row
                is_wishlisted = bool(is_wishlisted_raw)
                notify_enabled = bool(notify_enabled_raw)
            elif today_acc_subquery is not None:
                accommodation, avg_score, avg_price, today_date, today_applicants, today_score, today_status = row
                is_wishlisted = False
                notify_enabled = False
            elif wishlist_subquery is not None:
                accommodation, avg_score, avg_price, is_wishlisted_raw, notify_enabled_raw = row
                today_date = None
                today_applicants = None
                today_score = None
                today_status = None
                is_wishlisted = bool(is_wishlisted_raw)
                notify_enabled = bool(notify_enabled_raw)
            else:
                accommodation, avg_score, avg_price = row
                today_date = None
                today_applicants = None
                today_score = None
                today_status = None
                is_wishlisted = False
                notify_enabled = False

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
                "avg_price": round(avg_price, 0) if avg_price else None,
                "is_wishlisted": is_wishlisted,
                "notify_enabled": notify_enabled,
                "date": today_date,
                "applicants": today_applicants,
                "score": round(today_score, 1) if today_score else None,
                "status": today_status
            })

        return search_results

    async def get_regions(self, db: AsyncSession) -> List[str]:
        """accommodations 테이블의 지역 목록 조회 (중복 제거, 정렬)"""

        result = await db.execute(
            select(Accommodation.region)
            .distinct()
            .where(Accommodation.region.isnot(None))
            .order_by(Accommodation.region)
        )
        return [row[0] for row in result.fetchall()]

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
        - 기본 정보 + 예약 가능 날짜 + 요일별 평균 점수 + AI 요약
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
            "weekday_averages": weekday_averages,
            "ai_summary": None  # 프론트에서 별도 비동기 호출
        }

    async def get_ai_summary(self, accommodation_id: str, db: AsyncSession) -> Optional[List[str]]:
        """OpenAI로 3줄 요약 생성 (키 없으면 None, 비동기 별도 호출)"""
        if not self.llm:
            return None

        # 숙소 기본 정보 가져오기
        result = await db.execute(
            select(Accommodation).where(Accommodation.id == accommodation_id)
        )
        accommodation = result.scalar_one_or_none()
        if not accommodation:
            return None

        available_dates = await self.get_available_dates(accommodation_id, db)
        weekday_averages = await self.get_weekday_averages(accommodation_id, db)

        try:
            available_info = ""
            if available_dates:
                first_date = available_dates[0].get("date")
                available_info = f"가장 가까운 신청일: {first_date}" if first_date else ""

            avg_scores = ", ".join(
                f"{item.get('weekday_name')} {item.get('avg_score')}점"
                for item in weekday_averages[:3]
            )

            prompt = (
                "인터넷 검색 결과를 참고해 아래 숙소의 장점과 특징(뷰, 부대시설, 접근성 등)을 3줄로 요약하세요. "
                "실제 검색이 어려우면 제공된 정보만으로 합리적이고 검증 가능한 범위에서만 서술하고, 추측은 피하세요. "
                "각 문장은 35자 내외 한국어 문장으로, 불릿 없이 줄바꿈으로 구분합니다. "
                "포인트·규정·가격 등 확실하지 않은 정보는 언급하지 마세요.\n\n"
                f"숙소명: {accommodation.name}\n"
                f"지역: {accommodation.region}\n"
                f"주소: {accommodation.address or '정보 없음'}\n"
                f"숙소 타입: {accommodation.accommodation_type or '정보 없음'}\n"
                f"요약 키워드: {(accommodation.summary or [])[:5]}\n"
                f"수용 인원: {accommodation.capacity}\n"
                f"예약 가능 정보: {available_info}\n"
                f"요일별 평균 점수: {avg_scores or '정보 없음'}\n"
            )

            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            lines = [line.strip(" -•") for line in content.splitlines() if line.strip()]
            return lines[:3] if lines else None
        except Exception as e:
            logger.warning(f"AI 요약 생성 실패: {e}")
            return None
