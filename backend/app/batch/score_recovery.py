"""
매시간 실행되는 배치 작업
- 마지막 점수 회복 이후 POINTS_RECOVERY_HOURS가 경과한 사용자의 점수 회복
- 회복 완료시 알림 발송
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models.user import User
from app.config import settings
from app.integrations.firebase_service import FirebaseService
from app.integrations.kakao_service import KakaoService
from app.utils.logger import get_logger

logger = get_logger(__name__)
firebase_service = FirebaseService()
kakao_service = KakaoService()

async def process_score_recovery():
    """
    매시간 실행
    - 점수 회복 조건을 만족한 사용자 조회
    - 점수 회복
    - 알림 발송
    """

    async with AsyncSessionLocal() as db:
        try:
            recovery_hours = settings.POINTS_RECOVERY_HOURS
            recovery_threshold = datetime.utcnow() - timedelta(hours=recovery_hours)

            # 회복 가능한 사용자 조회
            recoverable_users = await db.execute(
                select(User).where(
                    and_(
                        User.current_points < User.max_points,
                        User.last_point_recovery < recovery_threshold
                    )
                )
            )
            users = recoverable_users.scalars().all()

            recovered_count = 0

            for user in users:
                # 점수 회복 (최대 10점)
                recovery_amount = min(10, user.max_points - user.current_points)
                user.current_points += recovery_amount
                user.last_point_recovery = datetime.utcnow()

                db.add(user)
                recovered_count += 1

                # 알림 발송
                message = f"✨ 포인트가 {recovery_amount}점 회복되었습니다! 현재 포인트: {user.current_points}/{user.max_points}"

                if user.firebase_token:
                    await firebase_service.send_notification(
                        token=user.firebase_token,
                        title="포인트 회복",
                        body=message,
                        data={"type": "score_recovery"}
                    )

                if user.kakao_user_id:
                    await kakao_service.send_message(
                        user_id=user.kakao_user_id,
                        message=message
                    )

            await db.commit()

            logger.info(f"Score recovery completed: {recovered_count} users recovered")

            return {
                "status": "success",
                "users_recovered": recovered_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Score recovery failed: {str(e)}", exc_info=True)
            raise

def handler(event, context):
    """AWS Lambda 핸들러"""
    import asyncio

    try:
        result = asyncio.run(process_score_recovery())
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }
