from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.sql import func
from app.database import Base

class Wishlist(Base):
    """
    사용자별 즐겨찾기 목록
    """
    __tablename__ = "wishlists"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # 사용자id (FK)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    # 숙소id (FK)
    accommodation_id = Column(String, ForeignKey("accommodations.id"), index=True)

    # 예약 희망 일자 (선택 사항)
    desired_date = Column(Date, nullable=True)

    # 등록여부
    is_active = Column(Boolean, default=True)

    # 알림여부
    notify_enabled = Column(Boolean, default=True)

    # 푸시 알림 타입 (ios_webview, android_fcm, kakao)
    notification_type = Column(String, nullable=True)

    # FCM 토큰 (Android용)
    fcm_token = Column(String, nullable=True)

    # 등록시간
    created_at = Column(DateTime, default=func.now())

    # 업데이트시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
