"use client";

import { useState, useEffect, useRef } from "react";
import { X, Clock } from "lucide-react";
import { AccommodationDetail, AvailableDate } from "@/types/accommodation";

interface DirectReservationModalProps {
  isOpen: boolean;
  onClose: () => void;
  accommodation: AccommodationDetail;
  selectedDate: AvailableDate;
  userName: string;
  onSubmit: (phoneNumber: string) => Promise<void>;
}

export default function DirectReservationModal({
  isOpen,
  onClose,
  accommodation,
  selectedDate,
  userName,
  onSubmit,
}: DirectReservationModalProps) {
  const [phone1, setPhone1] = useState("010");
  const [phone2, setPhone2] = useState("");
  const [phone3, setPhone3] = useState("");
  const [privacyAgreed, setPrivacyAgreed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [timeWarning, setTimeWarning] = useState<string | null>(null);
  const [isTimeAllowed, setIsTimeAllowed] = useState(true);

  const phone2Ref = useRef<HTMLInputElement>(null);
  const phone3Ref = useRef<HTMLInputElement>(null);

  // 시간 제한 체크
  useEffect(() => {
    const checkTime = () => {
      const now = new Date();
      const kstOffset = 9 * 60; // KST = UTC+9
      const kstTime = new Date(now.getTime() + (kstOffset - now.getTimezoneOffset()) * 60000);
      const hour = kstTime.getHours();

      if (hour >= 20 && hour < 21) {
        setTimeWarning("예약 가능 시간이 얼마 남지 않았습니다.");
        setIsTimeAllowed(true);
      } else if (hour < 8 || hour >= 21) {
        setTimeWarning("예약은 08시~21시 사이에만 가능합니다.");
        setIsTimeAllowed(false);
      } else {
        setTimeWarning(null);
        setIsTimeAllowed(true);
      }
    };

    checkTime();
    const interval = setInterval(checkTime, 60000); // 1분마다 체크

    return () => clearInterval(interval);
  }, []);

  const handlePhone2Change = (value: string) => {
    if (value.length <= 4) {
      setPhone2(value);
      if (value.length === 4) {
        phone3Ref.current?.focus();
      }
    }
  };

  const handlePhone3Change = (value: string) => {
    if (value.length <= 4) {
      setPhone3(value);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isTimeAllowed) {
      alert("예약 가능 시간이 아닙니다.");
      return;
    }

    if (!privacyAgreed) {
      alert("개인정보 취급 동의가 필요합니다.");
      return;
    }

    if (phone2.length !== 4 || phone3.length !== 4) {
      alert("올바른 연락처를 입력해주세요.");
      return;
    }

    const fullPhone = `${phone1}-${phone2}-${phone3}`;

    try {
      setIsSubmitting(true);
      await onSubmit(fullPhone);
    } catch (error) {
      console.error("예약 실패:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const checkInDate = new Date(selectedDate.date);
  const checkOutDate = new Date(checkInDate);
  checkOutDate.setDate(checkOutDate.getDate() + 1);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white shadow-xl">
        {/* 헤더 */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white p-4">
          <h2 className="text-xl font-bold">예약하기</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 hover:bg-gray-100"
            disabled={isSubmitting}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* 시간 경고 */}
        {timeWarning && (
          <div className={`mx-4 mt-4 flex items-center gap-2 rounded-lg p-3 ${
            isTimeAllowed ? "bg-yellow-50 text-yellow-800" : "bg-red-50 text-red-800"
          }`}>
            <Clock className="h-5 w-5" />
            <p className="text-sm font-medium">{timeWarning}</p>
          </div>
        )}

        {/* 내용 */}
        <form onSubmit={handleSubmit} className="p-4 space-y-6">
          {/* 숙소 정보 */}
          <div className="rounded-lg bg-gray-50 p-4 space-y-2">
            <div className="text-sm text-gray-600">숙소 지역</div>
            <div className="font-semibold">{accommodation.region}</div>

            <div className="text-sm text-gray-600 mt-3">숙소 정보</div>
            <div className="font-semibold">{accommodation.name}</div>

            <div className="text-sm text-gray-600 mt-3">숙박 날짜</div>
            <div className="font-semibold">
              {checkInDate.toLocaleDateString('ko-KR')} ~ {checkOutDate.toLocaleDateString('ko-KR')} (1박)
            </div>

            {accommodation.accommodation_type && (
              <>
                <div className="text-sm text-gray-600 mt-3">숙박 타입</div>
                <div className="font-semibold">{accommodation.accommodation_type}</div>
              </>
            )}

            <div className="text-sm text-gray-600 mt-3">룸 정보</div>
            <div className="font-semibold">기준 {accommodation.capacity}인</div>
          </div>

          {/* 숙박자 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              숙박자 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={userName}
              disabled
              className="w-full rounded-lg border border-gray-300 bg-gray-100 px-4 py-2"
            />
          </div>

          {/* 연락처 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              연락처 <span className="text-red-500">*</span>
            </label>
            <div className="flex items-center justify-center gap-2">
              <input
                type="text"
                value={phone1}
                disabled
                className="w-14 rounded-lg border border-gray-300 bg-gray-100 px-2 py-2 text-center text-sm"
              />
              <span className="text-gray-400">-</span>
              <input
                ref={phone2Ref}
                type="tel"
                value={phone2}
                onChange={(e) => handlePhone2Change(e.target.value.replace(/\D/g, ""))}
                maxLength={4}
                placeholder="1234"
                className="w-16 rounded-lg border border-gray-300 px-2 py-2 text-center text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              <span className="text-gray-400">-</span>
              <input
                ref={phone3Ref}
                type="tel"
                value={phone3}
                onChange={(e) => handlePhone3Change(e.target.value.replace(/\D/g, ""))}
                maxLength={4}
                placeholder="5678"
                className="w-16 rounded-lg border border-gray-300 px-2 py-2 text-center text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* 개인정보 동의 */}
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="privacy"
              checked={privacyAgreed}
              onChange={(e) => setPrivacyAgreed(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-gray-300"
              disabled={isSubmitting}
            />
            <label htmlFor="privacy" className="text-sm text-gray-700">
              개인정보 취급 동의서에 동의합니다. <span className="text-red-500">*</span>
            </label>
          </div>

          {/* 예약 버튼 */}
          <button
            type="submit"
            disabled={!isTimeAllowed || isSubmitting || !privacyAgreed || phone2.length !== 4 || phone3.length !== 4}
            className={`w-full rounded-lg py-3 font-semibold text-white transition ${
              !isTimeAllowed || isSubmitting || !privacyAgreed || phone2.length !== 4 || phone3.length !== 4
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {isSubmitting ? "예약 처리 중..." : "예약하기"}
          </button>
        </form>
      </div>
    </div>
  );
}
