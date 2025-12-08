from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AccommodationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    region: str
    price: int = Field(..., gt=0)
    capacity: int = Field(..., gt=0)
    images: Optional[List[str]] = []
    amenities: Optional[List[str]] = []

class AccommodationCreate(AccommodationBase):
    pass

class AccommodationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    available_rooms: Optional[int] = None

class AccommodationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    region: str
    price: int
    capacity: Optional[int] = None
    images: Optional[List[str]] = []
    amenities: Optional[List[str]] = []
    summary: List[str] = []
    rating: float
    can_book_with_current_score: Optional[bool] = False
    avg_winning_score_4weeks: Optional[int] = 0
    availability: int
    my_score: Optional[int] = None
    can_book: Optional[bool] = None
    past_bookings: Optional[int] = None
    win_rate: Optional[float] = None

    class Config:
        from_attributes = True

class RandomAccommodationResponse(BaseModel):
    """랜덤 숙소 조회용 간소화된 스키마"""
    id: str
    name: str
    region: str
    first_image: Optional[str] = None

    class Config:
        from_attributes = True

class PopularAccommodationResponse(BaseModel):
    """실시간 인기 숙소 조회용 스키마"""
    id: str
    name: str
    region: str
    first_image: Optional[str] = None
    date: str
    applicants: int
    score: float

    class Config:
        from_attributes = True

class SOLRecommendedAccommodationResponse(BaseModel):
    """SOL점수 기반 추천 숙소 조회용 스키마"""
    id: str
    name: str
    region: str
    first_image: Optional[str] = None
    average_sol_score: float

    class Config:
        from_attributes = True

class SearchAccommodationResponse(BaseModel):
    """검색용 숙소 조회 스키마"""
    id: str
    name: str
    region: str
    accommodation_type: Optional[str] = None
    first_image: Optional[str] = None
    summary: List[str] = []
    avg_score: Optional[float] = None
    avg_price: Optional[float] = None
    sol_score: Optional[float] = None
    is_wishlisted: bool = False
    notify_enabled: bool = False
    # 날짜별 정보 (date 파라미터 제공 시)
    date: Optional[str] = None
    applicants: Optional[int] = None
    score: Optional[float] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class AvailableDateResponse(BaseModel):
    """예약 가능 날짜 정보"""
    date: str
    score: float
    applicants: int
    status: str
    weekday: int

    class Config:
        from_attributes = True

class WeekdayAverageResponse(BaseModel):
    """요일별 평균 점수 정보"""
    weekday: int
    weekday_name: str
    avg_score: float
    count: int

    class Config:
        from_attributes = True

class AccommodationDetailResponse(BaseModel):
    """숙소 상세 페이지용 스키마"""
    id: str
    name: str
    region: str
    address: Optional[str] = None
    contact: Optional[str] = None
    website: Optional[str] = None
    accommodation_type: Optional[str] = None
    capacity: int
    images: List[str] = []
    summary: List[str] = []
    available_dates: List[AvailableDateResponse] = []
    weekday_averages: List[WeekdayAverageResponse] = []
    ai_summary: Optional[List[str]] = None

    class Config:
        from_attributes = True
