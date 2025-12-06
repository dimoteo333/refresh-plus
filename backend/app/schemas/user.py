from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    id: str  # 사용자 ID

class UserUpdate(BaseModel):
    name: Optional[str] = None
    firebase_token: Optional[str] = None
    kakao_user_id: Optional[str] = None

class UserResponse(UserBase):
    id: str
    current_points: int
    max_points: int
    total_bookings: int
    successful_bookings: int
    tier: str
    created_at: datetime

    class Config:
        from_attributes = True

class ScoreRecoverySchedule(BaseModel):
    current_score: int
    max_score: int
    recovery_per_period: int
    recovery_period_hours: int
    next_recovery: datetime
