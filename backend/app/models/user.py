from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # Clerk ID
    email = Column(String, unique=True, index=True)
    name = Column(String)
    current_points = Column(Integer, default=100)
    max_points = Column(Integer, default=100)
    total_bookings = Column(Integer, default=0)
    successful_bookings = Column(Integer, default=0)
    firebase_token = Column(String, nullable=True)
    kakao_user_id = Column(String, nullable=True)
    last_point_recovery = Column(DateTime, default=func.now())
    tier = Column(String, default="silver")  # silver, gold, platinum
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @property
    def success_rate(self) -> float:
        if self.total_bookings == 0:
            return 0.0
        return self.successful_bookings / self.total_bookings
