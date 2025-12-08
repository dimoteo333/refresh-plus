"""
통합 알림 서비스
- FCM (Android) 및 Web Push (iOS PWA) 지원
- 템플릿 기반 메시지 렌더링
- 중복 방지 로직
- 알림 이력 추적
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.notification_type import NotificationType
from app.models.notification_preference import NotificationPreference
from app.models.notification_log import NotificationLog
from app.integrations.firebase_service import FirebaseService
from app.integrations.webpush_service import WebPushService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class NotificationService:
    """통합 알림 발송 서비스"""

    def __init__(self):
        """서비스 초기화"""
        self.firebase_service = FirebaseService()
        self.webpush_service = WebPushService()

    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        data: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        알림 발송 메인 메서드

        Args:
            user_id: 사용자 ID
            notification_type: 알림 타입 (예: 'wishlist_available')
            data: 템플릿 변수 (예: {'accommodation_name': '호텔', 'date': '2024-12-25'})
            db: 데이터베이스 세션 (선택사항)

        Returns:
            bool: 발송 성공 여부
        """
        should_close_db = False
        if db is None:
            db = AsyncSessionLocal()
            should_close_db = True

        try:
            # 1. 사용자 조회
            user = await self._get_user(db, user_id)
            if not user or not user.notification_enabled:
                logger.info(f"Notifications disabled for user {user_id}")
                return False

            # 2. 사용자 알림 설정 확인
            if not await self._check_user_preference(db, user_id, notification_type):
                logger.info(f"User {user_id} disabled notification type: {notification_type}")
                return False

            # 3. 중복 체크
            dedup_key = self._generate_dedup_key(user_id, notification_type, data)
            if await self._is_duplicate(db, dedup_key):
                logger.info(f"Duplicate notification skipped: {dedup_key}")
                return False

            # 4. 템플릿 로드
            template = await self._get_notification_template(db, notification_type)
            if not template or not template.enabled:
                logger.error(f"Template not found or disabled: {notification_type}")
                return False

            # 5. 메시지 렌더링
            title = self._render_template(template.template_title, data)
            body = self._render_template(template.template_body, data)

            # 6. 채널 선택 및 발송
            channel = user.preferred_notification_channel or self._auto_select_channel(user)
            if not channel:
                logger.warning(f"No valid channel for user {user_id}")
                await self._log_notification(
                    db, user_id, notification_type, 'none', title, body, data,
                    status='failed',
                    error_message='No valid notification channel',
                    dedup_key=dedup_key
                )
                return False

            success = await self._send_via_channel(channel, user, title, body, data)

            # 7. 로그 저장
            await self._log_notification(
                db, user_id, notification_type, channel, title, body, data,
                status='sent' if success else 'failed',
                error_message=None if success else 'Send failed',
                dedup_key=dedup_key
            )

            return success

        except Exception as e:
            logger.error(f"Notification send failed: {e}", exc_info=True)
            return False

        finally:
            if should_close_db:
                await db.close()

    async def send_bulk_notification(
        self,
        users_data: List[Dict[str, Any]],
        notification_type: str
    ) -> Dict[str, int]:
        """
        여러 사용자에게 알림 발송 (최적화됨)

        Args:
            users_data: [{'user_id': 'id1', 'data': {...}}, ...]
            notification_type: 알림 타입

        Returns:
            {'sent': 10, 'failed': 2}
        """
        sent = 0
        failed = 0

        async with AsyncSessionLocal() as db:
            for user_info in users_data:
                try:
                    success = await self.send_notification(
                        user_id=user_info['user_id'],
                        notification_type=notification_type,
                        data=user_info['data'],
                        db=db
                    )
                    if success:
                        sent += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Bulk send error for user {user_info.get('user_id')}: {e}")
                    failed += 1

        return {"sent": sent, "failed": failed}

    async def _send_via_channel(
        self,
        channel: str,
        user: User,
        title: str,
        body: str,
        data: Dict[str, Any]
    ) -> bool:
        """채널별 발송"""
        try:
            if channel == 'fcm' and user.fcm_token:
                return await self._send_fcm(user.fcm_token, title, body, data)
            elif channel == 'web_push' and user.web_push_subscription:
                return await self._send_web_push(user.web_push_subscription, title, body, data)
            else:
                logger.warning(f"Invalid channel or missing token: {channel}")
                return False
        except Exception as e:
            logger.error(f"Channel send failed ({channel}): {e}", exc_info=True)
            return False

    async def _send_fcm(
        self,
        token: str,
        title: str,
        body: str,
        data: Dict[str, Any]
    ) -> bool:
        """Firebase FCM 발송"""
        try:
            await self.firebase_service.send_notification(
                token=token,
                title=title,
                body=body,
                data=data
            )
            logger.info(f"FCM sent successfully: {title}")
            return True
        except Exception as e:
            logger.error(f"FCM send failed: {e}", exc_info=True)
            return False

    async def _send_web_push(
        self,
        subscription: str,
        title: str,
        body: str,
        data: Dict[str, Any]
    ) -> bool:
        """Web Push 발송 (iOS PWA)"""
        try:
            # subscription이 JSON 문자열이면 파싱
            if isinstance(subscription, str):
                subscription_info = json.loads(subscription)
            else:
                subscription_info = subscription

            result = self.webpush_service.send_notification(
                subscription_info=subscription_info,
                title=title,
                body=body,
                data=data
            )
            return result
        except Exception as e:
            logger.error(f"Web Push send failed: {e}", exc_info=True)
            return False

    def _auto_select_channel(self, user: User) -> Optional[str]:
        """자동 채널 선택"""
        # Android → FCM
        if user.device_type == 'android' and user.fcm_token:
            return 'fcm'
        # iOS PWA → Web Push
        elif user.device_type == 'ios' and user.pwa_installed and user.web_push_subscription:
            return 'web_push'
        # 기본값: None
        return None

    def _generate_dedup_key(
        self,
        user_id: str,
        notification_type: str,
        data: Dict[str, Any]
    ) -> str:
        """중복 방지 키 생성 (MD5 해시)"""
        parts = [user_id, notification_type]

        # accommodation_id가 있으면 추가
        if 'accommodation_id' in data:
            parts.append(str(data['accommodation_id']))

        # date가 있으면 추가
        if 'date' in data:
            parts.append(str(data['date']))

        key_str = '_'.join(parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _is_duplicate(self, db: AsyncSession, dedup_key: str) -> bool:
        """중복 알림 체크"""
        result = await db.execute(
            select(NotificationLog)
            .where(
                NotificationLog.dedup_key == dedup_key,
                NotificationLog.dedup_expires_at > datetime.utcnow()
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """템플릿 렌더링 (Python .format() 사용)"""
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Template variable missing: {e}")
            return template
        except Exception as e:
            logger.error(f"Template render error: {e}")
            return template

    async def _get_user(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """사용자 조회"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_notification_template(
        self,
        db: AsyncSession,
        notification_type: str
    ) -> Optional[NotificationType]:
        """알림 템플릿 조회"""
        result = await db.execute(
            select(NotificationType).where(NotificationType.id == notification_type)
        )
        return result.scalar_one_or_none()

    async def _check_user_preference(
        self,
        db: AsyncSession,
        user_id: str,
        notification_type: str
    ) -> bool:
        """사용자 알림 설정 확인"""
        result = await db.execute(
            select(NotificationPreference)
            .where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type_id == notification_type
            )
        )
        pref = result.scalar_one_or_none()

        # 기본값: 활성화 (설정이 없으면 True)
        return pref.enabled if pref else True

    async def _log_notification(
        self,
        db: AsyncSession,
        user_id: str,
        notification_type: str,
        channel: str,
        title: str,
        body: str,
        data: Dict[str, Any],
        status: str,
        error_message: Optional[str] = None,
        dedup_key: Optional[str] = None
    ):
        """알림 로그 저장"""
        try:
            # 알림 타입에 따라 만료 시간 설정
            if notification_type == 'wishlist_available':
                # 8시간 쿨다운 (09:00와 20:00 중복 방지)
                dedup_expires = datetime.utcnow() + timedelta(hours=8)
            else:
                # 24시간 쿨다운 (기본값)
                dedup_expires = datetime.utcnow() + timedelta(hours=24)

            log = NotificationLog(
                id=str(uuid4()),
                user_id=user_id,
                notification_type_id=notification_type,
                channel=channel,
                title=title,
                body=body,
                data=data,
                status=status,
                error_message=error_message,
                sent_at=datetime.utcnow() if status == 'sent' else None,
                dedup_key=dedup_key,
                dedup_expires_at=dedup_expires
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to log notification: {e}", exc_info=True)
            await db.rollback()
