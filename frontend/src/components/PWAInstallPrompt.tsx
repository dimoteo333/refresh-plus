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
  const [showIOSInstructions, setShowIOSInstructions] = useState(false);

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
      // iOS는 설치 안내 확장
      setShowIOSInstructions(true);
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

  // iOS용 작은 팝업
  if (deviceType === 'ios') {
    return (
      <>
        {/* 백드롭 */}
        <div
          className="fixed inset-0 z-40 bg-black/30 transition-opacity"
          onClick={handleDismiss}
        />

        {/* 바텀 시트 */}
        <div className="fixed bottom-0 left-0 right-0 z-50 animate-slide-up">
          {!showIOSInstructions ? (
            // 첫 화면: 간단한 안내
            <div className="mx-4 mb-4 rounded-2xl bg-white p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600">
                  <Download className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">
                    앱 설치로 푸시 알림 받기
                  </p>
                  <p className="text-xs text-gray-600">
                    홈 화면에 추가하고 실시간 알림을 받아보세요
                  </p>
                </div>
                <button
                  onClick={handleDismiss}
                  className="flex-shrink-0 text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={handleDismiss}
                  className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  나중에
                </button>
                <button
                  onClick={handleInstall}
                  className="flex-1 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  설치 방법 보기
                </button>
              </div>
            </div>
          ) : (
            // 두 번째 화면: 설치 안내
            <div className="rounded-t-3xl bg-white pb-safe shadow-xl">
              <div className="p-6">
                {/* 핸들 바 */}
                <div className="mb-4 flex justify-center">
                  <div className="h-1 w-12 rounded-full bg-gray-300" />
                </div>

                {/* 제목 */}
                <div className="mb-6 text-center">
                  <div className="mb-2 inline-flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                    <Download className="h-8 w-8 text-blue-600" />
                  </div>
                  <h3 className="mt-3 text-lg font-bold text-gray-900">
                    앱 설치 방법
                  </h3>
                  <p className="mt-1 text-sm text-gray-600">
                    Safari에서 간단하게 설치할 수 있어요
                  </p>
                </div>

                {/* 단계별 안내 */}
                <div className="space-y-3">
                  <div className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
                    <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                      1
                    </div>
                    <p className="text-sm text-gray-700">
                      Safari 하단의 <span className="font-semibold">공유 버튼 (↑)</span> 탭
                    </p>
                  </div>
                  <div className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
                    <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                      2
                    </div>
                    <p className="text-sm text-gray-700">
                      <span className="font-semibold">"홈 화면에 추가"</span> 선택
                    </p>
                  </div>
                  <div className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
                    <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                      3
                    </div>
                    <p className="text-sm text-gray-700">
                      오른쪽 상단의 <span className="font-semibold">"추가"</span> 버튼 탭
                    </p>
                  </div>
                </div>

                {/* 완료 버튼 */}
                <button
                  onClick={handleDismiss}
                  className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700"
                >
                  확인
                </button>
              </div>
            </div>
          )}
        </div>
      </>
    );
  }

  // Android/Desktop용 팝업 (기존 유지)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <button
          onClick={handleDismiss}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
        >
          <X size={24} />
        </button>

        <div className="mb-4 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
            <Download className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <h2 className="mb-2 text-center text-2xl font-bold text-gray-900">
          앱으로 설치하고
        </h2>
        <div className="mb-4 flex items-center justify-center gap-2">
          <Gift className="h-6 w-6 text-yellow-500" />
          <span className="text-xl font-bold text-yellow-600">
            푸시알림을 받으세요!
          </span>
        </div>

        <p className="mb-6 text-center text-gray-600">
          설치하면 더 빠르고 편리하게 이용할 수 있습니다.
        </p>

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
            설치하기
          </button>
        </div>
      </div>
    </div>
  );
}
