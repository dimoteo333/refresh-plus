from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base

class NotificationPreference(Base):
    """
    사용자별 알림 설정
    - 알림 타입별로 활성화/비활성화 가능
    """
    __tablename__ = "notification_preferences"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type_id = Column(String, ForeignKey("notification_types.id"), nullable=False, index=True)

    # 설정
    enabled = Column(Boolean, default=True)  # 활성화 여부

    # 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 유니크 제약 조건
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type_id', name='uq_user_notif_type'),
    )
