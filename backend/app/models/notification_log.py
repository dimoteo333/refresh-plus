from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class NotificationLog(Base):
    """
    알림 발송 이력
    - 모든 알림 발송 기록
    - 중복 방지 및 분석용
    """
    __tablename__ = "notification_logs"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    notification_type_id = Column(String, ForeignKey("notification_types.id"), nullable=False, index=True)

    # 발송 정보
    channel = Column(String(50), nullable=False)  # 'fcm', 'web_push'
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)  # 추가 페이로드

    # 상태
    status = Column(String(50), nullable=False, index=True)  # 'sent', 'failed', 'pending'
    error_message = Column(Text, nullable=True)

    # 중복 방지
    dedup_key = Column(String(255), nullable=True, index=True)  # MD5 해시
    dedup_expires_at = Column(DateTime, nullable=True, index=True)  # 중복 체크 만료 시각

    # 타임스탬프
    sent_at = Column(DateTime, nullable=True)  # 실제 발송 시각
    created_at = Column(DateTime, default=func.now(), index=True)
