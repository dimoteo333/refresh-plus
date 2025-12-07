"""
챗봇 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services.chatbot_service import get_chatbot_service
from app.services.faq_vector_service import get_faq_vector_service
from app.dependencies import get_current_user
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 라우터는 prefix 없이 생성하고, app.include_router에서 /api/chatbot으로 prefix를 붙인다.
# 기존 prefix가 중복되어 실제 경로가 /api/chatbot/chatbot/* 로 노출되어 404가 발생했다.
router = APIRouter(tags=["chatbot"])


# 스키마
class ChatRequest(BaseModel):
    """
    채팅 요청
    """
    query: str


class ChatResponse(BaseModel):
    """
    채팅 응답
    """
    success: bool
    response: str
    context: Optional[str] = None
    error: Optional[str] = None


class VectorizeResponse(BaseModel):
    """
    벡터화 응답
    """
    success: int
    failed: int
    total: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    챗봇 질의응답

    Args:
        request: 채팅 요청
        current_user: 현재 사용자 (인증 필요)

    Returns:
        챗봇 응답
    """
    try:
        chatbot_service = get_chatbot_service()
        result = await chatbot_service.chat(query=request.query)

        return ChatResponse(
            success=result["success"],
            response=result["response"],
            context=result.get("context"),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"챗봇 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectorize", response_model=VectorizeResponse)
async def vectorize_faqs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    FAQ 벡터화 (관리자 전용)

    모든 FAQ를 벡터화하여 ChromaDB에 저장합니다.
    기존 벡터는 초기화됩니다.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 사용자 (관리자 권한 필요)

    Returns:
        벡터화 결과
    """
    try:
        # TODO: 관리자 권한 확인
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")

        faq_vector_service = get_faq_vector_service()
        result = await faq_vector_service.vectorize_all_faqs(db)

        return VectorizeResponse(
            success=result["success"],
            failed=result["failed"],
            total=result["total"]
        )

    except Exception as e:
        logger.error(f"벡터화 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_chatbot_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    챗봇 통계

    Args:
        current_user: 현재 사용자 (인증 필요)

    Returns:
        챗봇 및 벡터 스토어 통계
    """
    try:
        chatbot_service = get_chatbot_service()
        stats = await chatbot_service.get_stats()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
