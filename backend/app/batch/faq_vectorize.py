"""
FAQ 벡터화 배치 작업
크롤링된 FAQ를 ChromaDB에 벡터화하여 저장
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.faq_vector_service import get_faq_vector_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def vectorize_faqs():
    """
    FAQ 벡터화 메인 함수
    """
    logger.info("=" * 50)
    logger.info("FAQ 벡터화 배치 작업 시작")
    logger.info("=" * 50)

    try:
        # 데이터베이스 엔진 생성
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )

        # 세션 생성
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            # FAQ 벡터화 서비스
            faq_vector_service = get_faq_vector_service()

            # 모든 FAQ 벡터화
            result = await faq_vector_service.vectorize_all_faqs(session)

            logger.info(f"벡터화 완료:")
            logger.info(f"  - 성공: {result['success']}개")
            logger.info(f"  - 실패: {result['failed']}개")
            logger.info(f"  - 전체: {result['total']}개")

            # 통계 조회
            stats = faq_vector_service.get_collection_stats()
            logger.info(f"벡터 컬렉션 통계:")
            logger.info(f"  - 컬렉션: {stats['collection_name']}")
            logger.info(f"  - 문서 수: {stats['total_documents']}")

        logger.info("=" * 50)
        logger.info("FAQ 벡터화 배치 작업 완료")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"FAQ 벡터화 배치 작업 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(vectorize_faqs())
