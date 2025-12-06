from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """
    사용자 정보
    """
    __tablename__ = "users"

    # 사용자id (PK, Clerk ID)
    id = Column(String, primary_key=True, index=True)
    
    # 사용자명
    name = Column(String)
    
    # 점수
    points = Column(Integer, default=100)
    
    # 사용가능박수
    available_nights = Column(Integer, default=0)
    
    # 등록시간
    created_at = Column(DateTime, default=func.now())
    
    # 업데이트시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
