"""
FAQ 벡터화 서비스
FAQ 데이터를 ChromaDB에 벡터화하여 저장
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.faq import FAQ
from app.integrations.vector_store import get_vector_store
import logging

logger = logging.getLogger(__name__)


class FAQVectorService:
    """
    FAQ 벡터화 서비스
    """

    def __init__(self):
        """
        초기화
        """
        self.vector_store = get_vector_store()

    async def vectorize_all_faqs(self, db: AsyncSession) -> Dict[str, Any]:
        """
        모든 FAQ를 벡터화하여 저장

        Args:
            db: 데이터베이스 세션

        Returns:
            처리 결과 (성공/실패 개수)
        """
        try:
            # 기존 컬렉션 초기화
            self.vector_store.reset_collection()
            logger.info("기존 FAQ 벡터 컬렉션 초기화됨")

            # 모든 FAQ 가져오기
            result = await db.execute(
                select(FAQ).order_by(FAQ.order.asc())
            )
            faqs = result.scalars().all()

            if not faqs:
                logger.warning("벡터화할 FAQ가 없습니다.")
                return {"success": 0, "failed": 0, "total": 0}

            # 문서, 메타데이터, ID 리스트 준비
            documents = []
            metadatas = []
            ids = []

            for faq in faqs:
                # 질문과 답변을 결합하여 문서 생성
                doc_text = f"질문: {faq.question}\n답변: {faq.answer}"
                documents.append(doc_text)

                # 메타데이터
                metadata = {
                    "faq_id": faq.id,
                    "question": faq.question,
                    "category": faq.category or "기타",
                    "order": faq.order or 0
                }
                metadatas.append(metadata)

                # ID (faq_id 사용)
                ids.append(f"faq_{faq.id}")

            # ChromaDB에 추가
            self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"{len(faqs)}개 FAQ 벡터화 완료")

            return {
                "success": len(faqs),
                "failed": 0,
                "total": len(faqs)
            }

        except Exception as e:
            logger.error(f"FAQ 벡터화 실패: {e}")
            raise

    async def add_faq_to_vector(
        self,
        db: AsyncSession,
        faq_id: str
    ) -> bool:
        """
        특정 FAQ를 벡터화하여 추가

        Args:
            db: 데이터베이스 세션
            faq_id: FAQ ID

        Returns:
            성공 여부
        """
        try:
            # FAQ 가져오기
            result = await db.execute(
                select(FAQ).where(FAQ.id == faq_id)
            )
            faq = result.scalar_one_or_none()

            if not faq:
                logger.warning(f"FAQ ID {faq_id}를 찾을 수 없습니다.")
                return False

            # 문서 생성
            doc_text = f"질문: {faq.question}\n답변: {faq.answer}"

            # 메타데이터
            metadata = {
                "faq_id": faq.id,
                "question": faq.question,
                "category": faq.category or "기타",
                "order": faq.order or 0
            }

            # ChromaDB에 추가
            self.vector_store.add_documents(
                documents=[doc_text],
                metadatas=[metadata],
                ids=[f"faq_{faq.id}"]
            )

            logger.info(f"FAQ ID {faq_id} 벡터화 완료")
            return True

        except Exception as e:
            logger.error(f"FAQ 벡터화 실패: {e}")
            return False

    def search_similar_faqs(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        유사한 FAQ 검색

        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 개수
            category: 카테고리 필터 (선택)

        Returns:
            검색 결과
        """
        try:
            # 필터 조건
            where = None
            if category:
                where = {"category": category}

            # 검색
            results = self.vector_store.query(
                query_text=query,
                n_results=n_results,
                where=where
            )

            return results

        except Exception as e:
            logger.error(f"FAQ 검색 실패: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        벡터 컬렉션 통계

        Returns:
            통계 정보
        """
        try:
            count = self.vector_store.get_collection_count()
            return {
                "collection_name": self.vector_store.collection_name,
                "total_documents": count
            }
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            raise


# 싱글톤 인스턴스
_faq_vector_service: Optional[FAQVectorService] = None


def get_faq_vector_service() -> FAQVectorService:
    """
    FAQVectorService 싱글톤 인스턴스 반환
    """
    global _faq_vector_service
    if _faq_vector_service is None:
        _faq_vector_service = FAQVectorService()
    return _faq_vector_service
