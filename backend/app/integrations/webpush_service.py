"""
Web Push API 통합 (iOS PWA용)
- iOS 16.4+ Safari PWA에서 푸시 알림 지원
- VAPID 인증 사용
"""

import json
from typing import Dict, Any
from pywebpush import webpush, WebPushException
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class WebPushService:
    """Web Push API를 사용한 iOS PWA 푸시 알림 서비스"""

    def __init__(self):
        """VAPID 키로 초기화"""
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_claims = {
            "sub": f"mailto:{settings.VAPID_EMAIL}"
        }

        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("VAPID keys not configured. Web Push will not work.")

    def send_notification(
        self,
        subscription_info: Dict[str, Any],
        title: str,
        body: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """
        Web Push 알림 발송

        Args:
            subscription_info: 브라우저로부터 받은 PushSubscription 객체
            title: 알림 제목
            body: 알림 본문
            data: 추가 데이터 (선택사항)

        Returns:
            bool: 발송 성공 여부
        """
        if not self.vapid_private_key or not self.vapid_public_key:
            logger.error("VAPID keys not configured")
            return False

        try:
            # 페이로드 구성
            payload = json.dumps({
                "title": title,
                "body": body,
                "data": data or {},
                "icon": "/icon-192x192.png",
                "badge": "/badge-72x72.png"
            })

            # Web Push 발송
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )

            logger.info(f"Web Push sent successfully: {title}")
            return True

        except WebPushException as e:
            logger.error(f"Web Push failed: {e}")

            # 410 Gone: 구독이 만료됨 (DB에서 제거해야 함)
            if e.response and e.response.status_code == 410:
                logger.warning("Subscription expired (410 Gone) - should be removed from DB")

            return False

        except Exception as e:
            logger.error(f"Web Push error: {e}", exc_info=True)
            return False
