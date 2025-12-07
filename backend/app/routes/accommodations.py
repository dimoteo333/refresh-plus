from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.accommodation import Accommodation
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.schemas.accommodation import AccommodationResponse, RandomAccommodationResponse, PopularAccommodationResponse, SearchAccommodationResponse, AccommodationDetailResponse
from app.dependencies import get_current_user
from app.services.accommodation_service import AccommodationService
from typing import List
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
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    숙소 검색 (지역, 숙소명)
    - keyword가 없으면 region="서울"인 숙소를 우선 표시
    - keyword가 있으면 지역 또는 숙소명으로 검색
    - 각 숙소의 평균 점수 (마감(신청종료) 상태의 날짜들만)
    - 사용자의 즐겨찾기, 알림 설정 정보 포함 (로그인한 경우)
    """

    results = await service.search_accommodations(
        db=db,
        user_id=user_id,
        keyword=keyword,
        limit=limit
    )

    return results

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
