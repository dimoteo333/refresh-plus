from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
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
    accommodation_id = Column(String, ForeignKey("accommodations.id"), index=True)
    check_in = Column(DateTime, index=True)
    check_out = Column(DateTime)
    guests = Column(Integer, default=1)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, index=True)
    points_deducted = Column(Integer, default=0)
    winning_score_at_time = Column(Integer)  # 당첨당시 필요한 점수
    confirmation_number = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
