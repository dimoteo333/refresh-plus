"""
위시리스트 알림 배치 작업 (오전 09:00 KST)
- 찜한 숙소가 오늘 신청 가능 상태가 되었을 때 알림 발송
- 매일 09:00 KST 실행
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

async def process_wishlist_notification_morning():
    """
    찜한 날짜 신청 오픈 알림 (오전)
    - wishlists와 today_accommodation_info 매칭
    - 신청 가능 상태인 경우 알림 발송
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info("=" * 80)
            logger.info("Starting wishlist notification (morning)")
            logger.info("=" * 80)

            notification_service = NotificationService()

            # 위시리스트 + 오늘 신청 가능 숙소 조인 쿼리
            query = (
                select(
                    Wishlist.user_id,
                    Wishlist.accommodation_id,
                    Wishlist.desired_date,
                    Accommodation.name.label('accommodation_name'),
                    TodayAccommodation.score,
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
                    TodayAccommodation.status.in_(['신청중', '신청가능(최초 객실오픈)', '신청가능(상시 신청중)'])
                )
            )

            result = await db.execute(query)
            notifications_to_send = result.fetchall()

            logger.info(f"Found {len(notifications_to_send)} wishlists to notify")

            sent_count = 0
            failed_count = 0

            for notif in notifications_to_send:
                try:
                    # 알림 발송
                    success = await notification_service.send_notification(
                        user_id=notif.user_id,
                        notification_type='wishlist_available',
                        data={
                            'accommodation_id': notif.accommodation_id,
                            'accommodation_name': notif.accommodation_name,
                            'date': str(notif.date),
                            'score': notif.score,
                            'applicants': notif.applicants
                        },
                        db=db
                    )

                    if success:
                        sent_count += 1
                        logger.info(f"✓ Sent to user {notif.user_id}: {notif.accommodation_name} ({notif.date})")
                    else:
                        failed_count += 1
                        logger.warning(f"✗ Failed to send to user {notif.user_id}")

                except Exception as e:
                    logger.error(f"Error sending notification to user {notif.user_id}: {e}")
                    failed_count += 1

            logger.info("=" * 80)
            logger.info(f"Wishlist notification (morning) completed")
            logger.info(f"Sent: {sent_count}, Failed: {failed_count}")
            logger.info("=" * 80)

            return {
                "status": "success",
                "sent": sent_count,
                "failed": failed_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Wishlist notification (morning) failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

def handler(event, context):
    """AWS Lambda 핸들러"""
    import asyncio

    try:
        result = asyncio.run(process_wishlist_notification_morning())
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
