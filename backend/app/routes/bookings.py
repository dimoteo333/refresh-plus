from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse, DirectReservationCreate, DirectReservationResponse
from app.dependencies import get_current_user
from app.services.booking_service import BookingService
from typing import List
from app.utils.logger import get_logger

router = APIRouter()
service = BookingService()
logger = get_logger(__name__)

@router.post("", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """예약 생성 (티켓팅 신청)"""

    try:
        booking = await service.create_booking(
            user_id=current_user.id,
            accommodation_id=booking_data.accommodation_id,
            check_in=booking_data.check_in,
            check_out=booking_data.check_out,
            guests=booking_data.guests,
            db=db
        )

        return booking

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create booking")

@router.get("", response_model=List[BookingResponse])
async def get_bookings(
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 예약 목록 조회"""

    bookings = await service.get_booking_history(
        user_id=current_user.id,
        status=status,
        db=db
    )

    return bookings

@router.post("/direct-reserve", response_model=DirectReservationResponse)
async def create_direct_reservation(
    reservation_data: DirectReservationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """lulu-lala 웹사이트에 직접 예약 요청"""

    try:
        result = await service.create_direct_reservation(
            user_id=current_user.id,
            accommodation_id=reservation_data.accommodation_id,
            check_in_date=reservation_data.check_in_date,
            phone_number=reservation_data.phone_number,
            db=db
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Direct reservation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="예약 처리 중 오류가 발생했습니다.")
