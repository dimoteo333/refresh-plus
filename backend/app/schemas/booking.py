from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.booking import BookingStatus

class BookingCreate(BaseModel):
    accommodation_id: str
    check_in: datetime
    check_out: datetime
    guests: int = Field(..., gt=0, le=10)

class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None

class AccommodationBasic(BaseModel):
    """예약 정보에 포함될 기본 숙소 정보"""
    id: str
    name: str
    region: Optional[str] = None
    first_image: Optional[str] = None

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    id: str
    user_id: str
    accommodation_id: Optional[str] = None  # 크롤링 예약은 nullable
    accommodation_name: Optional[str] = None  # 크롤링한 호텔명
    accommodation: Optional[AccommodationBasic] = None  # 조인된 숙소 정보
    check_in: Optional[datetime] = None  # 크롤링 시 파싱 실패 가능
    check_out: Optional[datetime] = None
    guests: int
    status: BookingStatus
    points_deducted: int
    winning_score_at_time: Optional[int] = None
    confirmation_number: Optional[str] = None
    is_from_crawler: bool = False  # 크롤링 예약 구분
    created_at: datetime

    class Config:
        from_attributes = True
