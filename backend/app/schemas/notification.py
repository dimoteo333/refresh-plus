"""
알림 관련 Pydantic 스키마
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

# ===== 알림 설정 =====

class NotificationTypeInfo(BaseModel):
    """알림 타입 정보"""
    id: str
    name: str
    description: Optional[str] = None
    enabled: bool

class NotificationPreferencesResponse(BaseModel):
    """알림 설정 조회 응답"""
    global_enabled: bool = Field(description="전역 알림 활성화 여부")
    preferred_channel: Optional[str] = Field(None, description="선호 채널 (fcm, web_push)")
    device_type: Optional[str] = Field(None, description="디바이스 타입 (ios, android, web)")
    pwa_installed: bool = Field(False, description="PWA 설치 여부")
    types: List[NotificationTypeInfo] = Field(description="알림 타입별 활성화 상태")

class NotificationPreferenceUpdate(BaseModel):
    """알림 설정 업데이트 요청"""
    global_enabled: Optional[bool] = Field(None, description="전역 알림 활성화 여부")
    type_preferences: Optional[Dict[str, bool]] = Field(
        None,
        description="타입별 활성화 설정 {'wishlist_available': True, 'high_win_probability': False}"
    )

# ===== 디바이스 토큰 =====

class DeviceTokenRegister(BaseModel):
    """디바이스 토큰 등록 요청"""
    channel: str = Field(description="채널 타입: fcm, web_push")
    token: str = Field(description="FCM 토큰 또는 Web Push 구독 JSON")
    device_type: str = Field(description="디바이스 타입: ios, android, web")
    ios_version: Optional[str] = Field(None, description="iOS 버전 (예: 16.4)")

class DeviceTokenResponse(BaseModel):
    """디바이스 토큰 등록 응답"""
    status: str
    channel: str
    device_type: str
    pwa_bonus_applied: bool = Field(False, description="PWA 설치 보너스 적용 여부")

# ===== 알림 이력 =====

class NotificationHistoryItem(BaseModel):
    """알림 이력 항목"""
    id: str
    notification_type_id: str
    channel: str
    title: Optional[str]
    body: Optional[str]
    status: str
    sent_at: Optional[datetime]
    created_at: datetime

class NotificationHistoryResponse(BaseModel):
    """알림 이력 조회 응답"""
    total: int
    notifications: List[NotificationHistoryItem]

# ===== 테스트용 =====

class TestNotificationRequest(BaseModel):
    """테스트 알림 발송 요청 (개발용)"""
    notification_type: str = Field(description="알림 타입 ID")
    data: Dict[str, Any] = Field(description="템플릿 변수")
