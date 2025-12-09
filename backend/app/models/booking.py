from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from app.database import Base

class BookingStatus(str, Enum):
    PENDING = "pending"      # 진행 중
    WON = "won"              # 당첨
    LOST = "lost"            # 낙첨
    COMPLETED = "completed"  # 완료
    CANCELLED = "cancelled"  # 취소

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    accommodation_id = Column(String, ForeignKey("accommodations.id"), index=True, nullable=True)  # 크롤링 예약은 nullable
    accommodation_name = Column(String, nullable=True)  # 크롤링한 호텔명 저장
    check_in = Column(DateTime, index=True, nullable=True)  # 크롤링 시 파싱 실패 가능
    check_out = Column(DateTime, nullable=True)
    guests = Column(Integer, default=1)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, index=True)
    points_deducted = Column(Integer, default=0)
    winning_score_at_time = Column(Integer, nullable=True)  # 크롤링 예약은 없을 수 있음
    confirmation_number = Column(String, unique=True, nullable=True)  # 룰루랄라 접수번호 (revNo)
    is_from_crawler = Column(Boolean, default=False)  # 크롤링으로 가져온 예약인지 구분
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    accommodation = relationship("Accommodation", foreign_keys=[accommodation_id], lazy="joined")
