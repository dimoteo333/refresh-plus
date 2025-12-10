"use client";

import { Bell, X } from "lucide-react";

interface NotificationPermissionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export default function NotificationPermissionModal({
  isOpen,
  onClose,
  onConfirm,
}: NotificationPermissionModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 배경 오버레이 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 모달 컨텐츠 */}
      <div className="relative z-10 w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
        >
          <X className="h-5 w-5" />
        </button>

        {/* 아이콘 */}
        <div className="flex justify-center">
          <div className="rounded-full bg-blue-100 p-4">
            <Bell className="h-10 w-10 text-blue-600" />
          </div>
        </div>

        {/* 제목 */}
        <h2 className="mt-4 text-center text-xl font-bold text-gray-900">
          알림 허용
        </h2>

        {/* 설명 */}
        <p className="mt-3 text-center text-sm text-gray-600">
          찜한 숙소의 예약 가능 시점과 당첨 가능성을 알림으로 받아보세요.
        </p>

        {/* 이점 리스트 */}
        <div className="mt-6 space-y-3">
          <div className="flex items-start gap-3 rounded-lg bg-blue-50 p-3">
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              1
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                예약 가능 시점 알림
              </p>
              <p className="mt-1 text-xs text-gray-600">
                찜한 숙소의 점수가 충분할 때 즉시 알려드립니다.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 rounded-lg bg-blue-50 p-3">
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              2
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                당첨 확률 분석
              </p>
              <p className="mt-1 text-xs text-gray-600">
                실시간 데이터를 기반으로 당첨 가능성을 알려드립니다.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 rounded-lg bg-blue-50 p-3">
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              3
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                놓치지 않는 예약 기회
              </p>
              <p className="mt-1 text-xs text-gray-600">
                경쟁률이 낮은 날짜를 알림으로 추천해드립니다.
              </p>
            </div>
          </div>
        </div>

        {/* 버튼 */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-700 transition hover:bg-gray-50"
          >
            나중에
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 rounded-xl bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:from-blue-700 hover:to-blue-800"
          >
            알림 허용
          </button>
        </div>

        {/* 안내 문구 */}
        <p className="mt-4 text-center text-xs text-gray-500">
          알림은 언제든지 설정에서 변경할 수 있습니다.
        </p>
      </div>
    </div>
  );
}
