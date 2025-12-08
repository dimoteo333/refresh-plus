"""
알림 관련 API 엔드포인트
"""

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification_type import NotificationType
from app.models.notification_preference import NotificationPreference
from app.models.notification_log import NotificationLog
from app.schemas.notification import (
    NotificationPreferencesResponse,
    NotificationPreferenceUpdate,
    DeviceTokenRegister,
    DeviceTokenResponse,
    NotificationHistoryResponse,
    NotificationHistoryItem,
    NotificationTypeInfo
)
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    알림 설정 조회
    - 전역 알림 활성화 여부
    - 알림 타입별 활성화 상태
    """
    # 모든 알림 타입 조회
    types_result = await db.execute(
        select(NotificationType).where(NotificationType.enabled == True)
    )
    all_types = types_result.scalars().all()

    # 사용자 알림 설정 조회
    prefs_result = await db.execute(
        select(NotificationPreference)
        .where(NotificationPreference.user_id == current_user.id)
    )
    user_prefs = {
        pref.notification_type_id: pref.enabled
        for pref in prefs_result.scalars().all()
    }

    # 응답 구성
    types_info = [
        NotificationTypeInfo(
            id=nt.id,
            name=nt.name,
            description=nt.description,
            enabled=user_prefs.get(nt.id, True)  # 기본값: True
        )
        for nt in all_types
    ]

    return NotificationPreferencesResponse(
        global_enabled=current_user.notification_enabled,
        preferred_channel=current_user.preferred_notification_channel,
        device_type=current_user.device_type,
        pwa_installed=current_user.pwa_installed,
        types=types_info
    )


@router.put("/preferences")
async def update_notification_preferences(
    update: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    알림 설정 업데이트
    - 전역 알림 on/off
    - 알림 타입별 on/off
    """
    # 전역 설정 업데이트
    if update.global_enabled is not None:
        current_user.notification_enabled = update.global_enabled

    # 타입별 설정 업데이트
    if update.type_preferences:
        for type_id, enabled in update.type_preferences.items():
            # 기존 설정 조회
            existing = await db.execute(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == current_user.id,
                    NotificationPreference.notification_type_id == type_id
                )
            )
            pref = existing.scalar_one_or_none()

            if pref:
                # 업데이트
                pref.enabled = enabled
            else:
                # 새로 생성
                new_pref = NotificationPreference(
                    id=str(uuid4()),
                    user_id=current_user.id,
                    notification_type_id=type_id,
                    enabled=enabled
                )
                db.add(new_pref)

    await db.commit()

    return {"status": "success", "message": "알림 설정이 업데이트되었습니다."}


@router.post("/device-token", response_model=DeviceTokenResponse)
async def register_device_token(
    token_data: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    디바이스 토큰 등록/갱신
    - FCM 토큰 (Android)
    - Web Push 구독 (iOS PWA)
    - PWA 설치 시 보너스 포인트 5점 지급
    """
    pwa_bonus_applied = False

    # 채널별 토큰 저장
    if token_data.channel == 'fcm':
        current_user.fcm_token = token_data.token
        current_user.device_type = token_data.device_type

    elif token_data.channel == 'web_push':
        current_user.web_push_subscription = token_data.token
        current_user.device_type = token_data.device_type
        current_user.ios_version = token_data.ios_version

        # PWA 설치 보너스 (최초 1회만)
        if not current_user.pwa_installed:
            current_user.pwa_installed = True
            current_user.points += 5.0  # 보너스 포인트 5점 지급
            pwa_bonus_applied = True

    # 선호 채널 설정 (처음 등록하는 경우)
    if not current_user.preferred_notification_channel:
        current_user.preferred_notification_channel = token_data.channel

    await db.commit()

    return DeviceTokenResponse(
        status="success",
        channel=token_data.channel,
        device_type=token_data.device_type,
        pwa_bonus_applied=pwa_bonus_applied
    )


@router.get("/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    알림 발송 이력 조회
    - 페이지네이션 지원
    """
    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == current_user.id)
        .order_by(NotificationLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()

    notifications = [
        NotificationHistoryItem(
            id=log.id,
            notification_type_id=log.notification_type_id,
            channel=log.channel,
            title=log.title,
            body=log.body,
            status=log.status,
            sent_at=log.sent_at,
            created_at=log.created_at
        )
        for log in logs
    ]

    return NotificationHistoryResponse(
        total=len(notifications),
        notifications=notifications
    )
