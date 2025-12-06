from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class FAQVector(Base):
    """
    FAQ 벡터 임베딩 저장
    RAG 챗봇을 위한 FAQ 벡터화 데이터
    """
    __tablename__ = "faq_vectors"

    # Vector ID (PK)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 원본 FAQ ID (FK)
    faq_id = Column(String, ForeignKey("faqs.id"), nullable=False, index=True)

    # 텍스트 청크 (question + answer 조합 또는 분할된 텍스트)
    text_chunk = Column(Text, nullable=False)

    # 벡터 임베딩 (JSON 형태로 저장, Turso vector extension 사용 시 변경 가능)
    embedding = Column(JSON, nullable=False)

    # 메타데이터 (카테고리, 청크 인덱스 등)
    meta_data = Column(JSON, nullable=True)

    # 등록시간
    created_at = Column(DateTime, default=func.now())

    # 업데이트시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
