"""
LangGraph 기반 RAG 챗봇 서비스
FAQ 기반 질의응답 챗봇
"""
import os
from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.services.faq_vector_service import get_faq_vector_service
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
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
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

    def get_stats(self) -> Dict[str, Any]:
        """
        챗봇 통계

        Returns:
            통계 정보
        """
        return self.faq_vector_service.get_collection_stats()


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
