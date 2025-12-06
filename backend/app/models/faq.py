from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class FAQ(Base):
    """
    FAQ 정보
    """
    __tablename__ = "faqs"

    # FAQ ID (PK) - 자동 생성 또는 순번
    id = Column(String, primary_key=True, index=True)
    
    # 질문
    question = Column(Text, nullable=False)
    
    # 답변
    answer = Column(Text, nullable=False)
    
    # 카테고리 (선택사항)
    category = Column(String, nullable=True, index=True)
    
    # 순서 (FAQ 목록에서의 순서)
    order = Column(Integer, nullable=True)
    
    # 등록시간
    created_at = Column(DateTime, default=func.now())
    
    # 업데이트시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

