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

class BookingResponse(BaseModel):
    id: str
    user_id: str
    accommodation_id: str
    check_in: datetime
    check_out: datetime
    guests: int
    status: BookingStatus
    points_deducted: int
    winning_score_at_time: Optional[int] = None
    confirmation_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
