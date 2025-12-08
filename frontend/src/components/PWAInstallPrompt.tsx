'use client';

/**
 * PWA 설치 프롬프트 컴포넌트
 * - iOS Safari용 안내 모달
 * - Android/Desktop용 설치 버튼
 * - 보너스 포인트 5점 강조
 */

import { useState, useEffect } from 'react';
import { getDeviceType, isPWAInstalled, isIOSWebPushSupported } from '@/lib/webpush';
import { X, Download, Gift } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function PWAInstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [deviceType, setDeviceType] = useState<'ios' | 'android' | 'web'>('web');
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const device = getDeviceType();
    setDeviceType(device);

    // 이미 PWA로 설치되어 있으면 표시 안 함
    if (isPWAInstalled()) {
      return;
    }

    // 이전에 닫았는지 확인 (24시간 내)
    const dismissed = localStorage.getItem('pwa_prompt_dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      const now = Date.now();
      if (now - dismissedTime < 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // iOS인 경우
    if (device === 'ios') {
      // iOS 16.4+ Web Push 지원 확인
      if (isIOSWebPushSupported()) {
        setShowPrompt(true);
      }
    }

    // Android/Desktop인 경우 - beforeinstallprompt 이벤트 대기
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, []);

  const handleInstall = async () => {
    if (deviceType === 'ios') {
      // iOS는 수동 설치 안내만 가능
      return;
    }

    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        console.log('PWA installed');
      }

      setDeferredPrompt(null);
      setShowPrompt(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('pwa_prompt_dismissed', Date.now().toString());
    setShowPrompt(false);
  };

  if (!showPrompt) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        {/* 닫기 버튼 */}
        <button
          onClick={handleDismiss}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
        >
          <X size={24} />
        </button>

        {/* 아이콘 */}
        <div className="mb-4 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
            <Download className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        {/* 제목 */}
        <h2 className="mb-2 text-center text-2xl font-bold text-gray-900">
          앱으로 설치하고
        </h2>
        <div className="mb-4 flex items-center justify-center gap-2">
          <Gift className="h-6 w-6 text-yellow-500" />
          <span className="text-xl font-bold text-yellow-600">
            보너스 포인트 5점 받기!
          </span>
        </div>

        {/* 설명 */}
        <p className="mb-6 text-center text-gray-600">
          {deviceType === 'ios'
            ? '홈 화면에 추가하면 푸시 알림을 받을 수 있습니다.'
            : '설치하면 더 빠르고 편리하게 이용할 수 있습니다.'}
        </p>

        {/* iOS 설치 안내 */}
        {deviceType === 'ios' && (
          <div className="mb-6 rounded-lg bg-gray-50 p-4">
            <p className="mb-2 font-semibold text-gray-900">설치 방법:</p>
            <ol className="list-inside list-decimal space-y-1 text-sm text-gray-700">
              <li>Safari 하단의 공유 버튼 (↑) 탭</li>
              <li>"홈 화면에 추가" 선택</li>
              <li>"추가" 버튼 탭</li>
            </ol>
          </div>
        )}

        {/* 버튼 */}
        <div className="flex gap-3">
          <button
            onClick={handleDismiss}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-3 font-medium text-gray-700 hover:bg-gray-50"
          >
            나중에
          </button>
          <button
            onClick={handleInstall}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700"
          >
            {deviceType === 'ios' ? '확인' : '설치하기'}
          </button>
        </div>
      </div>
    </div>
  );
}
