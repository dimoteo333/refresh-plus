"""
당첨 가능성 높음 알림 배치 작업 (12:00 KST)
- 사용자 점수가 숙소 평균 당첨 점수보다 높을 때 알림 발송
- 매일 12:00 KST 실행
"""

import json
from datetime import datetime
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models.wishlist import Wishlist
from app.models.user import User
from app.models.accommodation import Accommodation
from app.models.today_accommodation import TodayAccommodation
from app.services.notification_service import NotificationService
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def process_winnable_notification():
    """
    당첨 가능성 높음 알림
    - 사용자의 points >= 숙소의 평균 당첨 score
    - 24시간 중복 방지 (하루 1회만)
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info("=" * 80)
            logger.info("Starting winnable notification")
            logger.info("=" * 80)

            notification_service = NotificationService()

            # 위시리스트 + 오늘 신청 가능 숙소 조인 쿼리
            # 조건: 사용자 점수 >= 숙소 평균 점수
            query = (
                select(
                    Wishlist.user_id,
                    Wishlist.accommodation_id,
                    Wishlist.desired_date,
                    Accommodation.name.label('accommodation_name'),
                    User.points.label('user_score'),
                    TodayAccommodation.score.label('avg_score'),
                    TodayAccommodation.applicants,
                    TodayAccommodation.status,
                    TodayAccommodation.date
                )
                .join(User, Wishlist.user_id == User.id)
                .join(Accommodation, Wishlist.accommodation_id == Accommodation.id)
                .join(
                    TodayAccommodation,
                    and_(
                        TodayAccommodation.accommodation_id == Wishlist.accommodation_id,
                        TodayAccommodation.date == Wishlist.desired_date
                    )
                )
                .where(
                    Wishlist.notify_enabled == True,
                    Wishlist.is_active == True,
                    User.notification_enabled == True,
                    TodayAccommodation.status.in_(['신청중', '신청가능(최초 객실오픈)', '신청가능(상시 신청중)']),
                    User.points >= TodayAccommodation.score  # 핵심 조건: 사용자 점수 >= 평균 점수
                )
            )

            result = await db.execute(query)
            notifications_to_send = result.fetchall()

            logger.info(f"Found {len(notifications_to_send)} users with high win probability")

            sent_count = 0
            failed_count = 0

            for notif in notifications_to_send:
                try:
                    # 알림 발송
                    success = await notification_service.send_notification(
                        user_id=notif.user_id,
                        notification_type='high_win_probability',
                        data={
                            'accommodation_id': notif.accommodation_id,
                            'accommodation_name': notif.accommodation_name,
                            'date': str(notif.date),
                            'user_score': int(notif.user_score),
                            'avg_score': notif.avg_score,
                            'applicants': notif.applicants
                        },
                        db=db
                    )

                    if success:
                        sent_count += 1
                        logger.info(
                            f"✓ Sent to user {notif.user_id}: {notif.accommodation_name} "
                            f"(user: {notif.user_score}점, avg: {notif.avg_score}점)"
                        )
                    else:
                        failed_count += 1
                        logger.warning(f"✗ Failed to send to user {notif.user_id}")

                except Exception as e:
                    logger.error(f"Error sending notification to user {notif.user_id}: {e}")
                    failed_count += 1

            logger.info("=" * 80)
            logger.info(f"Winnable notification completed")
            logger.info(f"Sent: {sent_count}, Failed: {failed_count}")
            logger.info("=" * 80)

            return {
                "status": "success",
                "sent": sent_count,
                "failed": failed_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Winnable notification failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

def handler(event, context):
    """AWS Lambda 핸들러"""
    import asyncio

    try:
        result = asyncio.run(process_winnable_notification())
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
