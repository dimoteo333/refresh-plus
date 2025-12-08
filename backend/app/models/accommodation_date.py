from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.database import Base

class AccommodationDate(Base):
    """
    날짜별 숙소 내역
    """
    __tablename__ = "accommodation_dates"

    # Primary Key (복합키 대신 단일 ID 사용)
    id = Column(String, primary_key=True, index=True)
    
    # 연도
    year = Column(Integer, index=True)
    
    # 몇주차
    week_number = Column(Integer, nullable=True)
    
    # 월
    month = Column(Integer, index=True)
    
    # 일
    day = Column(Integer, index=True)
    
    # 요일 (0=월요일, 6=일요일)
    weekday = Column(Integer, nullable=True)
    
    # 날짜 (YYYY-MM-DD 형식, 인덱싱 및 조회용)
    date = Column(String, index=True)
    
    # 숙소id (FK)
    accommodation_id = Column(String, ForeignKey("accommodations.id"), index=True)
    
    # 신청인원
    applicants = Column(Integer, default=0)
    
    # 점수
    score = Column(Float, default=0.0)
    
    # 신청상태 (예: "신청중", "마감", "신청불가", "객실없음" 등)
    status = Column(String, nullable=True, index=True)

    # 온라인 가격 (네이버 호텔에서 크롤링한 실제 숙박 금액)
    online_price = Column(Float, nullable=True)

    # 등록시간
    created_at = Column(DateTime, default=func.now())

    # 업데이트시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
