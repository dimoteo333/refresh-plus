/**
 * 알림 설정 훅
 * - Service Worker 등록
 * - Push 구독 관리
 * - 디바이스 토큰 등록
 */

import { useState, useEffect, useCallback } from 'react';
import {
  registerServiceWorker,
  requestNotificationPermission,
  subscribeToPush,
  unsubscribeFromPush,
  getDeviceType,
  getIOSVersion,
  isPWAInstalled,
  isWebPushSupported,
  isIOSWebPushSupported,
} from '@/lib/webpush';
import { api } from '@/lib/api';

interface NotificationSetupState {
  isSupported: boolean;
  isIOSSupported: boolean;
  isPWA: boolean;
  permission: NotificationPermission | null;
  isSubscribed: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useNotificationSetup() {
  const [state, setState] = useState<NotificationSetupState>({
    isSupported: false,
    isIOSSupported: false,
    isPWA: false,
    permission: null,
    isSubscribed: false,
    isLoading: true,
    error: null,
  });

  // 초기화
  useEffect(() => {
    const init = async () => {
      try {
        const isSupported = isWebPushSupported();
        const isIOSSupported = isIOSWebPushSupported();
        const isPWA = isPWAInstalled();
        const permission = isSupported ? Notification.permission : null;

        setState((prev) => ({
          ...prev,
          isSupported,
          isIOSSupported,
          isPWA,
          permission,
          isLoading: false,
        }));

        // Service Worker 자동 등록
        if (isSupported) {
          await registerServiceWorker();
        }
      } catch (error) {
        console.error('Notification setup init failed:', error);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: '알림 초기화에 실패했습니다.',
        }));
      }
    };

    init();
  }, []);

  // 알림 권한 요청 및 구독
  const requestPermissionAndSubscribe = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      // 1. 알림 권한 요청
      const permission = await requestNotificationPermission();
      setState((prev) => ({ ...prev, permission }));

      if (permission !== 'granted') {
        throw new Error('알림 권한이 거부되었습니다.');
      }

      // 2. Web Push 구독
      const subscription = await subscribeToPush();
      if (!subscription) {
        throw new Error('Push 구독에 실패했습니다.');
      }

      // 3. 서버에 토큰 등록
      const deviceType = getDeviceType();
      const iosVersion = getIOSVersion();

      const response = await api.post('/notifications/device-token', {
        channel: 'web_push',
        token: JSON.stringify(subscription.toJSON()),
        device_type: deviceType,
        ios_version: iosVersion,
      });

      setState((prev) => ({
        ...prev,
        isSubscribed: true,
        isLoading: false,
      }));

      // PWA 보너스 포인트 알림
      if (response.data.pwa_bonus_applied) {
        alert('🎉 PWA 설치 보너스 5점이 지급되었습니다!');
      }

      return true;
    } catch (error: any) {
      console.error('Permission and subscribe failed:', error);
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error.message || '알림 설정에 실패했습니다.',
      }));
      return false;
    }
  }, []);

  // 구독 해제
  const unsubscribe = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      await unsubscribeFromPush();

      setState((prev) => ({
        ...prev,
        isSubscribed: false,
        isLoading: false,
      }));

      return true;
    } catch (error: any) {
      console.error('Unsubscribe failed:', error);
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error.message || '구독 해제에 실패했습니다.',
      }));
      return false;
    }
  }, []);

  // Android FCM 토큰 등록 (외부에서 호출)
  const registerFCMToken = useCallback(async (token: string) => {
    try {
      await api.post('/notifications/device-token', {
        channel: 'fcm',
        token,
        device_type: 'android',
      });
      return true;
    } catch (error) {
      console.error('FCM token registration failed:', error);
      return false;
    }
  }, []);

  return {
    ...state,
    requestPermissionAndSubscribe,
    unsubscribe,
    registerFCMToken,
  };
}
