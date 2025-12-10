"""
Firebase Cloud Messaging 통합
"""

import firebase_admin
from firebase_admin import credentials, messaging
from app.config import settings
from app.utils.logger import get_logger
from typing import Dict, Any, Optional
import json

logger = get_logger(__name__)

class FirebaseService:
    def __init__(self):
        self.app = None
        self._initialize()

    def _initialize(self):
        """Firebase 초기화"""
        try:
            if not firebase_admin._apps:
                if settings.FIREBASE_CREDENTIALS_JSON:
                    # JSON 문자열을 딕셔너리로 파싱
                    cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                    cred = credentials.Certificate(cred_dict)
                    self.app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized successfully")
                else:
                    logger.warning("Firebase credentials not configured")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase credentials JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> str:
        """
        개별 디바이스로 알림 전송

        Args:
            token: FCM 토큰
            title: 알림 제목
            body: 알림 본문
            data: 추가 데이터
            image_url: 이미지 URL

        Returns:
            message_id
        """

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url
                ),
                data=data or {},
                token=token,
            )

            message_id = messaging.send(message)
            logger.info(f"FCM message sent: {message_id}")

            return message_id

        except Exception as e:
            logger.error(f"Failed to send FCM notification: {str(e)}")
            raise

    async def send_multicast(
        self,
        tokens: list,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        여러 디바이스로 알림 전송 (최대 500개)
        """

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens,
            )

            response = messaging.send_multicast(message)

            logger.info(
                f"Multicast sent: {response.success_count} succeeded, "
                f"{response.failure_count} failed"
            )

            return response

        except Exception as e:
            logger.error(f"Failed to send multicast: {str(e)}")
            raise
