from fastapi import APIRouter, Depends
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """알림 설정 조회"""
    return {
        "push_enabled": True,
        "push_on_booking_result": True,
        "push_on_wishlist_bookable": True,
        "push_on_score_recovery": False,
        "kakao_enabled": True
    }

@router.put("/preferences")
async def update_notification_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user)
):
    """알림 설정 업데이트"""
    # TODO: Implement preference storage
    return preferences
