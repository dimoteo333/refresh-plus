from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class NotificationType(Base):
    """
    알림 타입 템플릿
    - 알림 타입별 메시지 템플릿 관리
    - 확장 가능한 알림 시스템
    """
    __tablename__ = "notification_types"

    # Primary Key
    id = Column(String, primary_key=True)  # 예: 'wishlist_available', 'high_win_probability'

    # 기본 정보
    name = Column(String(100), nullable=False)  # 표시명 (한글)
    description = Column(Text, nullable=True)  # 설명

    # 템플릿
    template_title = Column(String(255), nullable=True)  # 제목 템플릿
    template_body = Column(Text, nullable=True)  # 본문 템플릿 (Python .format() 사용)

    # 활성화 여부
    enabled = Column(Boolean, default=True)

    # 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
