from fastapi import APIRouter, Depends
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/history")
async def get_score_history(
    current_user: User = Depends(get_current_user)
):
    """점수 변동 이력 조회"""
    # TODO: Implement score history tracking
    return {
        "current_score": current_user.points,
        "history": []
    }
