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
