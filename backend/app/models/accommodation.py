from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class Accommodation(Base):
    """
    숙소 정보 원장
    """
    __tablename__ = "accommodations"

    # 숙소Id (PK)
    id = Column(String, primary_key=True, index=True)
    
    # 지역
    region = Column(String, index=True)
    
    # 숙소id (원본 시스템의 ID, 중복 가능성 있음)
    accommodation_id = Column(String, nullable=True, index=True)
    
    # 숙소명
    name = Column(String, index=True)
    
    # 주소
    address = Column(Text, nullable=True)
    
    # 연락처
    contact = Column(String, nullable=True)
    
    # 체크인/아웃
    check_in_out = Column(String, nullable=True)
    
    # 홈페이지
    website = Column(String, nullable=True)
    
    # 숙소 타입
    accommodation_type = Column(String, nullable=True)
    
    # 숙소 인원
    capacity = Column(Integer, default=2)
    
    # 숙소 이미지 URL (여러 개) - JSON 배열
    images = Column(JSON, default=list)
    
    # 등록시간
    created_at = Column(DateTime, default=func.now())
    
    # 업데이트시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
