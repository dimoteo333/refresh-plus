'use client';

/**
 * 알림 설정 페이지
 * - 전역 알림 on/off
 * - 알림 타입별 on/off
 * - 디바이스 정보 표시
 * - 알림 이력 보기
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, BellOff, Smartphone, History, Gift } from 'lucide-react';
import { notificationApi } from '@/lib/api';
import { useNotificationSetup } from '@/hooks/useNotificationSetup';

interface NotificationType {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface NotificationPreferences {
  global_enabled: boolean;
  preferred_channel: string | null;
  device_type: string | null;
  pwa_installed: boolean;
  types: NotificationType[];
}

export default function NotificationSettingsPage() {
  const router = useRouter();
  const {
    isSupported,
    isIOSSupported,
    isPWA,
    permission,
    isSubscribed,
    isLoading: setupLoading,
    requestPermissionAndSubscribe,
    unsubscribe,
  } = useNotificationSetup();

  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 초기 로드
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await notificationApi.getPreferences(token);
      setPreferences(response.data);
    } catch (error) {
      console.error('Failed to load preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  // 전역 알림 토글
  const handleGlobalToggle = async () => {
    if (!preferences) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const newValue = !preferences.global_enabled;

      // 활성화 시 권한 요청 및 구독
      if (newValue && !isSubscribed) {
        const success = await requestPermissionAndSubscribe();
        if (!success) {
          alert('알림 권한이 필요합니다.');
          setSaving(false);
          return;
        }
      }

      await notificationApi.updatePreferences(token, {
        global_enabled: newValue,
      });

      setPreferences({
        ...preferences,
        global_enabled: newValue,
      });
    } catch (error) {
      console.error('Failed to update global setting:', error);
      alert('설정 업데이트에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // 타입별 알림 토글
  const handleTypeToggle = async (typeId: string) => {
    if (!preferences) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const updatedTypes = preferences.types.map((type) =>
        type.id === typeId ? { ...type, enabled: !type.enabled } : type
      );

      await notificationApi.updatePreferences(token, {
        type_preferences: {
          [typeId]: !preferences.types.find((t) => t.id === typeId)?.enabled,
        },
      });

      setPreferences({
        ...preferences,
        types: updatedTypes,
      });
    } catch (error) {
      console.error('Failed to update type setting:', error);
      alert('설정 업데이트에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // PWA 설치 유도
  const handlePWAPrompt = () => {
    alert(
      'Safari 하단의 공유 버튼(↑)을 탭하고 "홈 화면에 추가"를 선택하세요.\n\nPWA 설치 시 보너스 포인트 5점이 지급됩니다!'
    );
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-gray-500">로딩 중...</div>
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-red-500">설정을 불러올 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-2xl">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">알림 설정</h1>
          <p className="mt-2 text-sm text-gray-600">
            찜한 숙소의 예약 가능 시점과 당첨 가능성을 알림으로 받아보세요.
          </p>
        </div>

        {/* PWA 설치 안내 (iOS, 미설치 시) */}
        {preferences.device_type === 'ios' && !preferences.pwa_installed && (
          <div className="mb-6 rounded-lg bg-yellow-50 p-4 border border-yellow-200">
            <div className="flex items-start gap-3">
              <Gift className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900">
                  PWA 설치하고 보너스 포인트 5점 받기!
                </h3>
                <p className="mt-1 text-sm text-yellow-800">
                  홈 화면에 추가하면 푸시 알림을 받을 수 있습니다.
                </p>
                <button
                  onClick={handlePWAPrompt}
                  className="mt-3 rounded-lg bg-yellow-600 px-4 py-2 text-sm font-medium text-white hover:bg-yellow-700"
                >
                  설치 방법 보기
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 디바이스 정보 */}
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Smartphone className="h-5 w-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">디바이스 정보</h2>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">디바이스 타입:</span>
              <span className="font-medium">{preferences.device_type || '알 수 없음'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">알림 채널:</span>
              <span className="font-medium">
                {preferences.preferred_channel === 'web_push' && 'Web Push (iOS PWA)'}
                {preferences.preferred_channel === 'fcm' && 'Firebase (Android)'}
                {!preferences.preferred_channel && '미설정'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">PWA 설치:</span>
              <span className="font-medium">
                {preferences.pwa_installed ? '✓ 설치됨' : '✗ 미설치'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">알림 권한:</span>
              <span className="font-medium">
                {permission === 'granted' && '✓ 허용됨'}
                {permission === 'denied' && '✗ 거부됨'}
                {permission === 'default' && '대기 중'}
              </span>
            </div>
          </div>
        </div>

        {/* 전역 알림 설정 */}
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {preferences.global_enabled ? (
                <Bell className="h-6 w-6 text-blue-600" />
              ) : (
                <BellOff className="h-6 w-6 text-gray-400" />
              )}
              <div>
                <h2 className="font-semibold text-gray-900">전체 알림</h2>
                <p className="text-sm text-gray-600">모든 알림을 받습니다</p>
              </div>
            </div>
            <button
              onClick={handleGlobalToggle}
              disabled={saving || setupLoading}
              className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                preferences.global_enabled ? 'bg-blue-600' : 'bg-gray-300'
              } ${saving || setupLoading ? 'opacity-50' : ''}`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                  preferences.global_enabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* 알림 타입별 설정 */}
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <h2 className="mb-4 font-semibold text-gray-900">알림 종류</h2>
          <div className="space-y-4">
            {preferences.types.map((type) => (
              <div key={type.id} className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{type.name}</h3>
                  <p className="text-sm text-gray-600">{type.description}</p>
                </div>
                <button
                  onClick={() => handleTypeToggle(type.id)}
                  disabled={!preferences.global_enabled || saving}
                  className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                    type.enabled && preferences.global_enabled
                      ? 'bg-blue-600'
                      : 'bg-gray-300'
                  } ${
                    !preferences.global_enabled || saving ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <span
                    className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                      type.enabled && preferences.global_enabled
                        ? 'translate-x-7'
                        : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* 알림 이력 버튼 */}
        <button
          onClick={() => router.push('/settings/notifications/history')}
          className="mb-6 w-full rounded-lg bg-white p-4 shadow-sm hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <History className="h-6 w-6 text-gray-600" />
              <span className="font-medium text-gray-900">알림 이력 보기</span>
            </div>
            <span className="text-gray-400">→</span>
          </div>
        </button>

        {/* 안내 메시지 */}
        {!isSupported && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
            이 브라우저는 푸시 알림을 지원하지 않습니다.
          </div>
        )}

        {preferences.device_type === 'ios' && !isIOSSupported && (
          <div className="rounded-lg bg-yellow-50 p-4 text-sm text-yellow-800">
            푸시 알림을 받으려면 iOS 16.4 이상이 필요합니다.
          </div>
        )}
      </div>
    </div>
  );
}
