from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, ScoreRecoverySchedule
from app.dependencies import get_current_user
from app.config import settings
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """현재 사용자 프로필 조회"""
    return current_user

@router.get("/me/score-recovery-schedule", response_model=ScoreRecoverySchedule)
async def get_score_recovery_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """점수 회복 스케줄 조회"""

    next_recovery = current_user.last_point_recovery + timedelta(
        hours=settings.POINTS_RECOVERY_HOURS
    )

    return ScoreRecoverySchedule(
        current_score=current_user.points,
        max_score=current_user.max_points,
        recovery_per_period=10,
        recovery_period_hours=settings.POINTS_RECOVERY_HOURS,
        next_recovery=next_recovery
    )
