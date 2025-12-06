"""
Chainlit 채팅 UI 앱
FAQ 기반 RAG 챗봇
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import chainlit as cl
from app.services.chatbot_service import get_chatbot_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 챗봇 서비스 초기화
chatbot_service = None


@cl.on_chat_start
async def start():
    """
    채팅 시작 시 실행
    """
    global chatbot_service

    try:
        # 챗봇 서비스 초기화
        if chatbot_service is None:
            chatbot_service = get_chatbot_service()

        # 환영 메시지
        await cl.Message(
            content="안녕하세요! 👋\n\n"
                    "저는 Refresh Plus 연성소 예약 플랫폼의 AI 도우미입니다.\n\n"
                    "숙소 예약, 포인트 시스템, 이용 방법 등에 대해 궁금하신 점을 물어보세요!"
        ).send()

        # 통계 정보 가져오기
        stats = chatbot_service.get_stats()
        total_docs = stats.get("total_documents", 0)

        if total_docs > 0:
            await cl.Message(
                content=f"📚 현재 {total_docs}개의 FAQ 데이터를 학습했습니다."
            ).send()
        else:
            await cl.Message(
                content="⚠️ 학습된 FAQ 데이터가 없습니다. 관리자에게 문의하세요."
            ).send()

    except Exception as e:
        logger.error(f"채팅 시작 오류: {e}")
        await cl.Message(
            content="죄송합니다. 챗봇 초기화 중 오류가 발생했습니다."
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """
    메시지 수신 시 실행

    Args:
        message: 사용자 메시지
    """
    global chatbot_service

    try:
        user_query = message.content

        # 로딩 메시지 표시
        msg = cl.Message(content="")
        await msg.send()

        # 챗봇 서비스 호출
        if chatbot_service is None:
            chatbot_service = get_chatbot_service()

        result = await chatbot_service.chat(query=user_query)

        # 응답 생성
        if result["success"]:
            response_text = result["response"]

            # 컨텍스트가 있으면 참고 자료 표시
            if result.get("context"):
                response_text += "\n\n---\n📖 **참고 자료**\n"
                response_text += "```\n"
                response_text += result["context"][:500]  # 500자 제한
                if len(result["context"]) > 500:
                    response_text += "...\n(더 보기 생략)"
                response_text += "\n```"

            msg.content = response_text
            await msg.update()

        else:
            error_msg = result.get("error", "알 수 없는 오류")
            msg.content = f"죄송합니다. 응답 생성 중 오류가 발생했습니다.\n\n오류: {error_msg}"
            await msg.update()

    except Exception as e:
        logger.error(f"메시지 처리 오류: {e}")
        msg.content = f"죄송합니다. 요청 처리 중 오류가 발생했습니다.\n\n오류: {str(e)}"
        await msg.update()


@cl.on_chat_end
async def end():
    """
    채팅 종료 시 실행
    """
    logger.info("채팅 종료")
