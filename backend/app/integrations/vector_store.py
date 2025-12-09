"""
ChromaDB 벡터 스토어 설정
FAQ RAG 챗봇을 위한 벡터 데이터베이스
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    ChromaDB 벡터 스토어 관리 클래스
    """

    def __init__(
        self,
        collection_name: str = "faq_collection",
        persist_directory: str | Path | None = None,
        use_openai: bool = False
    ):
        """
        초기화

        Args:
            collection_name: 컬렉션 이름
            persist_directory: ChromaDB 저장 경로
            use_openai: OpenAI 임베딩 사용 여부 (False면 HuggingFace 사용)
        """
        self.collection_name = collection_name
        default_dir = Path(__file__).resolve().parents[2] / "chroma_db"
        self.persist_directory = Path(
            persist_directory
            or settings.CHROMA_PERSIST_DIRECTORY
            or default_dir
        ).expanduser().resolve()
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # 임베딩 함수 설정
        if use_openai:
            # OpenAI 임베딩 사용 (API 키 필요)
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name="text-embedding-ada-002"
            )
        else:
            # HuggingFace 임베딩 사용 (로컬, 무료)
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="jhgan/ko-sroberta-multitask"  # 한국어 특화 모델
            )

        # 컬렉션 가져오기 또는 생성
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"기존 컬렉션 '{collection_name}' 로드됨")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"새 컬렉션 '{collection_name}' 생성됨")

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        문서를 벡터 스토어에 추가

        Args:
            documents: 문서 텍스트 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"{len(documents)}개 문서 추가됨")
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        유사도 검색

        Args:
            query_text: 쿼리 텍스트
            n_results: 반환할 결과 개수
            where: 필터 조건 (메타데이터 기반)

        Returns:
            검색 결과
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"검색 실패: {e}")
            raise

    def delete_collection(self) -> None:
        """
        컬렉션 삭제
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"컬렉션 '{self.collection_name}' 삭제됨")
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {e}")
            raise

    def reset_collection(self) -> None:
        """
        컬렉션 초기화 (모든 데이터 삭제 후 재생성)
        """
        try:
            self.delete_collection()
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"컬렉션 '{self.collection_name}' 초기화됨")
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {e}")
            raise

    def get_collection_count(self) -> int:
        """
        컬렉션의 문서 개수 반환
        """
        return self.collection.count()


# 싱글톤 인스턴스
_vector_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    """
    VectorStore 싱글톤 인스턴스 반환
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(
            collection_name="faq_collection",
            persist_directory=None,
            use_openai=False  # HuggingFace 사용 (무료)
        )
    return _vector_store
