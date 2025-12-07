"""
LangGraph 기반 RAG 챗봇 서비스
FAQ 기반 질의응답 챗봇
"""
import asyncio
import csv
import os
from pathlib import Path
from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.faq import FAQ
from app.services.faq_vector_service import get_faq_vector_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)


# 상태 정의
class ChatbotState(TypedDict):
    """
    챗봇 대화 상태
    """
    messages: Sequence[HumanMessage | AIMessage | SystemMessage]
    query: str
    context: Optional[str]
    response: Optional[str]
    error: Optional[str]


class ChatbotService:
    """
    RAG 챗봇 서비스
    """

    def __init__(self):
        """
        초기화
        """
        # OpenAI API 키 확인
        self.openai_api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다.")

        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=self.openai_api_key
        ) if self.openai_api_key else None

        # FAQ 벡터 서비스
        self.faq_vector_service = get_faq_vector_service()

        # LangGraph 워크플로우 구성
        self.workflow = self._build_workflow()
        self._initialized = False
        self._init_lock = asyncio.Lock()

    def _build_workflow(self) -> StateGraph:
        """
        LangGraph 워크플로우 구성

        Returns:
            StateGraph 인스턴스
        """
        # 상태 그래프 생성
        workflow = StateGraph(ChatbotState)

        # 노드 추가
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("generate", self._generate_response)

        # 엣지 설정
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # 컴파일
        return workflow.compile()

    def _retrieve_context(self, state: ChatbotState) -> ChatbotState:
        """
        벡터 검색으로 관련 FAQ 컨텍스트 가져오기

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        try:
            query = state["query"]
            logger.info(f"검색 쿼리: {query}")

            # 유사한 FAQ 검색
            results = self.faq_vector_service.search_similar_faqs(
                query=query,
                n_results=3  # 상위 3개 결과
            )

            # 컨텍스트 구성
            if results and results.get("documents") and len(results["documents"][0]) > 0:
                context_parts = []
                for i, doc in enumerate(results["documents"][0]):
                    context_parts.append(f"[참고 {i+1}]\n{doc}")

                context = "\n\n".join(context_parts)
                state["context"] = context
                logger.info(f"검색 완료: {len(results['documents'][0])}개 문서")
            else:
                state["context"] = None
                logger.warning("관련 FAQ를 찾을 수 없습니다.")

            return state

        except Exception as e:
            logger.error(f"컨텍스트 검색 실패: {e}")
            state["error"] = str(e)
            return state

    def _generate_response(self, state: ChatbotState) -> ChatbotState:
        """
        LLM을 사용하여 응답 생성

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        try:
            if not self.llm:
                state["response"] = "OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의하세요."
                return state

            query = state["query"]
            context = state.get("context")

            # 프롬프트 템플릿
            if context:
                system_prompt = """당신은 신한은행 임직원을 위한 Refresh Plus 연성소 예약 플랫폼의 고객 지원 챗봇입니다.

아래 참고 자료를 바탕으로 사용자의 질문에 친절하고 정확하게 답변해주세요.

참고 자료:
{context}

답변 시 주의사항:
1. 참고 자료에 있는 정보를 우선적으로 사용하세요
2. 참고 자료에 없는 내용은 "죄송하지만 해당 정보를 찾을 수 없습니다"라고 안내하세요
3. 친절하고 공손한 어투로 답변하세요
4. 필요시 참고 자료의 번호를 인용하세요 (예: [참고 1]에 따르면...)
"""
                user_prompt = f"사용자 질문: {query}"

                messages = [
                    SystemMessage(content=system_prompt.format(context=context)),
                    HumanMessage(content=user_prompt)
                ]
            else:
                system_prompt = """당신은 신한은행 임직원을 위한 Refresh Plus 연성소 예약 플랫폼의 고객 지원 챗봇입니다.

관련 FAQ를 찾을 수 없었습니다. 일반적인 지식을 바탕으로 도움을 드리거나,
더 구체적인 질문을 부탁드려도 좋습니다.

답변 시 주의사항:
1. 친절하고 공손한 어투로 답변하세요
2. 확실하지 않은 정보는 추측하지 말고, 관리자에게 문의하도록 안내하세요
"""
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=query)
                ]

            # LLM 호출
            response = self.llm.invoke(messages)
            state["response"] = response.content
            logger.info("응답 생성 완료")

            return state

        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            state["error"] = str(e)
            state["response"] = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
            return state

    async def chat(self, query: str) -> Dict[str, Any]:
        """
        사용자 질문에 대한 챗봇 응답

        Args:
            query: 사용자 질문

        Returns:
            챗봇 응답 및 메타데이터
        """
        try:
            # FAQ 데이터 및 벡터 스토어 준비
            await self._ensure_initialized()

            # 초기 상태
            initial_state: ChatbotState = {
                "messages": [],
                "query": query,
                "context": None,
                "response": None,
                "error": None
            }

            # 워크플로우 실행
            result = self.workflow.invoke(initial_state)

            return {
                "success": True,
                "response": result.get("response"),
                "context": result.get("context"),
                "error": result.get("error")
            }

        except Exception as e:
            logger.error(f"챗봇 처리 실패: {e}")
            return {
                "success": False,
                "response": "죄송합니다. 요청 처리 중 오류가 발생했습니다.",
                "context": None,
                "error": str(e)
            }

    async def get_stats(self) -> Dict[str, Any]:
        """
        챗봇 통계

        Returns:
            통계 정보
        """
        await self._ensure_initialized()
        return self.faq_vector_service.get_collection_stats()

    async def _ensure_initialized(self) -> None:
        """
        FAQ DB 데이터 및 벡터 스토어를 준비한다.
        - faqs 테이블이 비어 있으면 CSV를 읽어 채운다.
        - 벡터 스토어에 데이터가 없으면 벡터화한다.
        """
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            try:
                async with AsyncSessionLocal() as db:
                    # 현재 FAQ 개수 확인
                    faq_count_result = await db.execute(select(func.count(FAQ.id)))
                    faq_count = faq_count_result.scalar() or 0

                    # 필요 시 CSV에서 FAQ 로드
                    if faq_count == 0:
                        inserted = await self._import_faqs_from_csv(db)
                        faq_count = inserted
                        logger.info(f"CSV에서 {inserted}개의 FAQ를 로드했습니다.")
                    else:
                        logger.info(f"이미 {faq_count}개의 FAQ 데이터가 존재합니다.")

                    # 벡터 스토어 상태 확인 후 벡터화
                    stats = self.faq_vector_service.get_collection_stats()
                    vector_count = stats.get("total_documents", 0) if stats else 0
                    if vector_count < faq_count and faq_count > 0:
                        await self.faq_vector_service.vectorize_all_faqs(db)
                        logger.info("FAQ 벡터화 완료")
                    elif vector_count == 0 and faq_count == 0:
                        logger.warning("FAQ 데이터가 없어 벡터화를 건너뜁니다.")
                    else:
                        logger.info(f"벡터 스토어에 {vector_count}개 문서가 이미 존재합니다.")

                self._initialized = True
            except Exception as e:
                logger.error(f"챗봇 초기화 실패: {e}")
                raise

    async def _import_faqs_from_csv(self, db: AsyncSession) -> int:
        """
        FAQ CSV를 읽어 DB에 채운다.

        Args:
            db: DB 세션

        Returns:
            추가된 FAQ 개수
        """
        base_dir = Path(__file__).resolve().parents[2]  # backend 디렉토리
        csv_path = base_dir / "docs" / "faq.csv"

        if not csv_path.exists():
            logger.warning(f"FAQ CSV 파일을 찾을 수 없습니다: {csv_path}")
            return 0

        # UTF-8 BOM 우선, 실패 시 CP949로 재시도
        encodings_to_try = ["utf-8-sig", "cp949"]
        rows = None
        for enc in encodings_to_try:
            try:
                with csv_path.open("r", encoding=enc, newline="") as f:
                    rows = list(csv.DictReader(f))
                break
            except UnicodeDecodeError:
                continue

        if rows is None:
            logger.error("FAQ CSV를 읽을 수 없습니다. 인코딩을 확인하세요.")
            return 0

        faqs_to_add = []
        for idx, row in enumerate(rows):
            question = (row.get("question") or "").strip()
            answer = (row.get("answer") or "").strip()
            if not question or not answer:
                logger.warning(f"{idx+1}번째 행에 질문/답변이 없어 건너뜁니다.")
                continue

            raw_id = (row.get("id") or "").strip()
            faq_id = raw_id if raw_id else str(idx + 1)
            category = (row.get("category") or None) or None
            order_raw = (row.get("order") or "").strip()
            try:
                order_val = int(order_raw) if order_raw else idx + 1
            except ValueError:
                order_val = idx + 1

            faq = FAQ(
                id=faq_id,
                question=question,
                answer=answer,
                category=category,
                order=order_val,
            )
            faqs_to_add.append(faq)

        if not faqs_to_add:
            logger.warning("CSV에서 유효한 FAQ 데이터를 찾지 못했습니다.")
            return 0

        db.add_all(faqs_to_add)
        await db.commit()
        return len(faqs_to_add)


# 싱글톤 인스턴스
_chatbot_service: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """
    ChatbotService 싱글톤 인스턴스 반환
    """
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
