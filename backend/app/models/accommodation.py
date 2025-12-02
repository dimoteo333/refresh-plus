from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class Accommodation(Base):
    __tablename__ = "accommodations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    region = Column(String, index=True)
    price = Column(Integer)
    capacity = Column(Integer)
    images = Column(JSON, default=list)  # URL 리스트
    amenities = Column(JSON, default=list)  # 편의시설
    rating = Column(Float, default=4.0)
    available_rooms = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
