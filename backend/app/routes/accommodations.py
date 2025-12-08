from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.accommodation import Accommodation
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.schemas.accommodation import AccommodationResponse, RandomAccommodationResponse, PopularAccommodationResponse, SearchAccommodationResponse, AccommodationDetailResponse, AvailableDateResponse
from app.dependencies import get_current_user
from app.services.accommodation_service import AccommodationService
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()
service = AccommodationService()

@router.get("", response_model=List[AccommodationResponse])
async def get_accommodations(
    region: str = Query(None),
    sort_by: str = Query("popularity", regex="^(popularity|price|rating)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    숙소 목록 조회
    - region: 지역 필터
    - sort_by: 정렬 기준 (popularity, price, rating)
    - page: 페이지 번호
    - limit: 페이지당 개수
    """

    # 기본 쿼리
    query = select(Accommodation)

    # 지역 필터
    if region:
        query = query.where(Accommodation.region == region)

    # 정렬
    if sort_by == "price":
        query = query.order_by(Accommodation.price)
    elif sort_by == "rating":
        query = query.order_by(Accommodation.rating.desc())
    else:  # popularity (기본값)
        query = query.order_by(Accommodation.available_rooms.desc())

    # 페이지네이션
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    accommodations = result.scalars().all()

    # 각 숙소에 대해 사용자의 예약 가능 여부 계산
    responses = []
    for acc in accommodations:
        can_book = await service.can_user_book(
            current_user.id,
            acc.id,
            current_user.current_points,
            db
        )

        # 최근 4주간 평균 당첨 점수 계산
        avg_winning_score = await service.get_avg_winning_score_4weeks(
            acc.id,
            db
        )

        responses.append(
            AccommodationResponse(
                id=acc.id,
                name=acc.name,
                region=acc.region,
                price=acc.price,
                can_book_with_current_score=can_book,
                avg_winning_score_4weeks=avg_winning_score,
                availability=acc.available_rooms,
                rating=acc.rating,
                summary=(acc.summary or [])[:5]
            )
        )

    return responses

@router.get("/random", response_model=List[RandomAccommodationResponse])
async def get_random_accommodations(
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    랜덤 숙소 목록 조회 (인증 불필요)
    메인 페이지 carousel용
    - limit: 조회할 숙소 개수 (기본값: 5)
    """

    accommodations = await service.get_random_accommodations(db, limit)

    return [
        RandomAccommodationResponse(
            id=acc.id,
            name=acc.name,
            region=acc.region,
            first_image=acc.images[0] if acc.images and len(acc.images) > 0 else None
        )
        for acc in accommodations
    ]

@router.get("/popular", response_model=List[PopularAccommodationResponse])
async def get_popular_accommodations(
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    실시간 인기 숙소 목록 조회 (인증 불필요)
    메인 페이지 인기 숙소 섹션용
    - limit: 조회할 숙소 개수 (기본값: 5)
    - status='신청가능'인 숙소만 조회
    - score 기준 내림차순 정렬
    """

    results = await service.get_popular_accommodations(db, limit)

    return [
        PopularAccommodationResponse(
            id=acc.id,
            name=acc.name,
            region=acc.region,
            first_image=acc.images[0] if acc.images and len(acc.images) > 0 else None,
            date=today_acc.date,
            applicants=today_acc.applicants,
            score=today_acc.score
        )
        for today_acc, acc in results
    ]

@router.get("/search", response_model=List[SearchAccommodationResponse])
async def search_accommodations(
    keyword: str = Query(None, description="검색 키워드 (지역 또는 숙소명)"),
    region: str = Query(None, description="지역 필터 (전체/all은 무시)"),
    sort_by: str = Query("avg_score", regex="^(default|avg_score|name|wishlist|price|sol_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    available_only: bool = Query(False, description="신청 가능 숙소만 조회"),
    date: str = Query(None, description="특정 날짜 필터링 (YYYY-MM-DD 형식)"),
    limit: int = Query(50, ge=1, le=100),
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    숙소 검색 (지역, 숙소명, 날짜)
    - keyword가 있으면 지역 또는 숙소명으로 검색
    - region 파라미터로 특정 지역 필터링 (전체/all/빈값은 무시)
    - sort_by: avg_score(평균 점수), name(가나다순), wishlist(즐겨찾기 우선), price(온라인 평균가), sol_score(추후 적용)
    - sort_order: asc/desc
    - available_only: today_accommodation_info에 신청 가능/신청중 상태가 있는 숙소만
    - date: 특정 날짜 필터링 (제공 시 today_accommodation_info 기준으로 신청중/신청가능 상태만 조회)
    - 각 숙소의 평균 점수 (마감(신청종료) 상태의 날짜들만)
    - 사용자의 즐겨찾기, 알림 설정 정보 포함 (로그인한 경우)
    """

    # JWT 토큰 우선, 없으면 X-User-ID 사용
    current_user_id = None
    if authorization:
        # JWT 토큰으로 사용자 조회
        try:
            token = authorization.replace("Bearer ", "").strip()
            from app.services.auth_service import auth_service
            user = await auth_service.get_user_from_token(token, db)
            if user:
                current_user_id = user.id
        except:
            pass  # JWT 토큰 인증 실패 시 무시하고 계속 진행

    # JWT 인증 실패 시 X-User-ID 사용
    if not current_user_id and user_id:
        current_user_id = user_id

    results = await service.search_accommodations(
        db=db,
        user_id=current_user_id,
        keyword=keyword,
        region=region,
        sort_by=sort_by,
        sort_order=sort_order,
        available_only=available_only,
        date=date,
        limit=limit
    )

    return results

@router.get("/regions", response_model=List[str])
async def get_regions(
    db: AsyncSession = Depends(get_db)
):
    """accommodations 테이블의 지역 목록 조회 (중복 제거, 정렬)"""

    return await service.get_regions(db)

@router.get("/detail/{accommodation_id}", response_model=AccommodationDetailResponse)
async def get_accommodation_detail_page(
    accommodation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    숙소 상세 페이지 정보 조회 (인증 불필요)
    - 기본 정보 (이미지, 제목, 지역, 주소, 연락처, 웹사이트, 타입, 인원수)
    - 예약 가능 날짜 (today_accommodation_info, 신청중/신청가능 상태)
    - 요일별 평균 점수 (accommodation_dates, 마감(신청종료) 상태, 최근 3개월)
    """

    detail = await service.get_accommodation_detail(accommodation_id, db)

    if not detail:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    return detail

@router.get("/detail/{accommodation_id}/ai-summary", response_model=Optional[List[str]])
async def get_accommodation_ai_summary(
    accommodation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    숙소 AI 3줄 요약 (비동기 호출용)
    - OpenAI 키가 없으면 null 반환
    - 장점/특징 위주로 요약
    """

    summary = await service.get_ai_summary(accommodation_id, db)
    return summary

@router.get("/{accommodation_id}/dates", response_model=List[AvailableDateResponse])
async def get_accommodation_dates(
    accommodation_id: str,
    start_date: Optional[str] = Query(None, description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 숙소의 날짜별 점수와 신청 인원 조회
    - TodayAccommodation 우선 (최신 데이터)
    - AccommodationDate는 TodayAccommodation에 없는 날짜만
    - 날짜 범위 지정 가능 (start_date, end_date)
    """
    from app.models.accommodation_date import AccommodationDate
    from app.models.today_accommodation import TodayAccommodation

    # 숙소 존재 확인
    result = await db.execute(
        select(Accommodation).where(Accommodation.id == accommodation_id)
    )
    accommodation = result.scalar_one_or_none()

    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    # TodayAccommodation 쿼리 (최신 데이터 우선)
    today_acc_query = select(
        TodayAccommodation.date,
        TodayAccommodation.score,
        TodayAccommodation.applicants,
        TodayAccommodation.status,
        TodayAccommodation.weekday
    ).where(TodayAccommodation.accommodation_id == accommodation_id)

    # 날짜 범위 필터
    if start_date:
        today_acc_query = today_acc_query.where(TodayAccommodation.date >= start_date)

    if end_date:
        today_acc_query = today_acc_query.where(TodayAccommodation.date <= end_date)

    # TodayAccommodation 조회
    today_result = await db.execute(today_acc_query)
    today_dates = today_result.all()

    # TodayAccommodation에 있는 날짜들
    today_date_set = {row[0] for row in today_dates}

    # AccommodationDate 쿼리 (TodayAccommodation에 없는 날짜만)
    acc_date_query = select(
        AccommodationDate.date,
        AccommodationDate.score,
        AccommodationDate.applicants,
        AccommodationDate.status,
        AccommodationDate.weekday
    ).where(AccommodationDate.accommodation_id == accommodation_id)

    # 날짜 범위 필터
    if start_date:
        acc_date_query = acc_date_query.where(AccommodationDate.date >= start_date)

    if end_date:
        acc_date_query = acc_date_query.where(AccommodationDate.date <= end_date)

    # TodayAccommodation에 없는 날짜만 조회
    if today_date_set:
        acc_date_query = acc_date_query.where(~AccommodationDate.date.in_(today_date_set))

    # AccommodationDate 조회
    acc_result = await db.execute(acc_date_query)
    acc_dates = acc_result.all()

    # 두 결과 합치고 날짜로 정렬
    all_dates = list(today_dates) + list(acc_dates)
    all_dates.sort(key=lambda x: x[0])  # 날짜로 정렬

    return [
        AvailableDateResponse(
            date=date,
            score=score or 0.0,
            applicants=applicants or 0,
            status=status or "미정",
            weekday=weekday or 0
        )
        for date, score, applicants, status, weekday in all_dates
    ]

@router.get("/{accommodation_id}", response_model=AccommodationResponse)
async def get_accommodation_detail(
    accommodation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """숙소 상세 정보 조회"""

    # 숙소 조회
    result = await db.execute(
        select(Accommodation).where(Accommodation.id == accommodation_id)
    )
    accommodation = result.scalar_one_or_none()

    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    # 사용자의 과거 예약 현황
    past_bookings_result = await db.execute(
        select(Booking).where(
            (Booking.user_id == current_user.id) &
            (Booking.accommodation_id == accommodation_id) &
            (Booking.status.in_([BookingStatus.WON, BookingStatus.COMPLETED]))
        )
    )
    past_bookings = len(past_bookings_result.scalars().all())

    # 승률 계산
    win_rate = (
        past_bookings / current_user.total_bookings
        if current_user.total_bookings > 0
        else 0.0
    )

    # 당첨 필요 점수 (4주)
    avg_winning_score = await service.get_avg_winning_score_4weeks(
        accommodation_id,
        db
    )

    return AccommodationResponse(
        id=accommodation.id,
        name=accommodation.name,
        description=accommodation.description,
        price=accommodation.price,
        images=accommodation.images,
        amenities=accommodation.amenities,
        summary=(accommodation.summary or [])[:5],
        my_score=current_user.current_points,
        can_book=current_user.current_points >= avg_winning_score,
        past_bookings=past_bookings,
        win_rate=win_rate,
        avg_winning_score_4weeks=avg_winning_score,
        availability=accommodation.available_rooms,
        rating=accommodation.rating,
        region=accommodation.region
    )
