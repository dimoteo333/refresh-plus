from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WishlistCreate(BaseModel):
    accommodation_id: str
    notify_when_bookable: bool = True

class WishlistResponse(BaseModel):
    id: str
    user_id: str
    accommodation_id: str
    notify_when_bookable: bool
    created_at: datetime

    class Config:
        from_attributes = True
