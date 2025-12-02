from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.accommodation import Accommodation
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.schemas.accommodation import AccommodationResponse
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
                rating=acc.rating
            )
        )

    return responses

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
        my_score=current_user.current_points,
        can_book=current_user.current_points >= avg_winning_score,
        past_bookings=past_bookings,
        win_rate=win_rate,
        avg_winning_score_4weeks=avg_winning_score,
        availability=accommodation.available_rooms,
        rating=accommodation.rating,
        region=accommodation.region
    )
