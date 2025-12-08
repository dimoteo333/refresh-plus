from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class WishlistCreate(BaseModel):
    accommodation_id: str
    desired_date: Optional[date] = None
    notify_enabled: bool = True
    notification_type: Optional[str] = None  # ios_webview, android_fcm, kakao
    fcm_token: Optional[str] = None

class WishlistUpdate(BaseModel):
    desired_date: Optional[date] = None
    notify_enabled: Optional[bool] = None
    notification_type: Optional[str] = None
    fcm_token: Optional[str] = None

class WishlistResponse(BaseModel):
    id: str
    user_id: str
    accommodation_id: str
    desired_date: Optional[date] = None
    is_active: bool
    notify_enabled: bool
    notification_type: Optional[str] = None
    fcm_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
