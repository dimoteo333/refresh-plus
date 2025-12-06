"use client";

import { AvailableDate } from "@/types/accommodation";
import { useRef } from "react";

interface AvailableDatePickerProps {
  dates: AvailableDate[];
  selectedDate: AvailableDate | null;
  onSelectDate: (date: AvailableDate) => void;
}

export default function AvailableDatePicker({
  dates,
  selectedDate,
  onSelectDate,
}: AvailableDatePickerProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const formatDateParts = (dateStr: string) => {
    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return { month, day };
  };

  const getWeekdayName = (weekday: number) => {
    const weekdays = ["월", "화", "수", "목", "금", "토", "일"];
    return weekdays[weekday];
  };

  const getCircleClasses = (weekday: number, isSelected: boolean) => {
    if (isSelected) {
      return "bg-blue-600 border-blue-600 text-white shadow-lg";
    }

    if (weekday === 6) {
      return "border-red-400 text-red-600";
    }

    if (weekday === 5) {
      return "border-blue-800 text-blue-700";
    }

    return "border-gray-200 text-gray-900";
  };

  return (
    <div className="relative">
      {/* 가로 스크롤 컨테이너 */}
      <div
        ref={scrollContainerRef}
        className="flex overflow-x-auto gap-4 pb-2 scrollbar-hide"
        style={{
          scrollbarWidth: "none",
          msOverflowStyle: "none",
        }}
      >
        {dates.map((date, index) => {
          const isSelected = selectedDate?.date === date.date;
          const { month, day } = formatDateParts(date.date);
          const weekdayName = getWeekdayName(date.weekday);

          return (
            <button
              key={`${date.date}-${index}`}
              onClick={() => onSelectDate(date)}
              className={`
                flex-shrink-0 flex flex-col items-center gap-3 rounded-2xl border-2 p-3 transition-all
                ${
                  isSelected
                    ? "border-blue-200 bg-blue-50 shadow-md"
                    : "border-transparent bg-white hover:border-blue-100"
                }
              `}
              style={{ minWidth: "130px" }}
            >
              <div
                className={`flex h-24 w-24 flex-col items-center justify-center rounded-full border-2 text-center text-sm font-medium ${getCircleClasses(
                  date.weekday,
                  isSelected
                )}`}
              >
                <span className="text-[11px] tracking-wide">{month}월</span>
                <span className="text-2xl font-bold leading-none">{day}</span>
                <span className="text-xs">{weekdayName}요일</span>
              </div>

              <div className="text-center text-sm">
                <p
                  className={`font-semibold ${
                    isSelected ? "text-blue-700" : "text-gray-900"
                  }`}
                >
                  {date.score.toFixed(1)}점
                </p>
                <p className="text-xs text-gray-600">{date.applicants}명 신청</p>
                <span
                  className={`mt-1 inline-block rounded-full px-3 py-1 text-[11px] font-semibold ${
                    date.status === "신청중"
                      ? "bg-green-100 text-green-700"
                      : "bg-blue-100 text-blue-700"
                  }`}
                >
                  {date.status}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* 스크롤 표시자 (선택적) */}
      {dates.length > 3 && (
        <div className="mt-2 text-center text-xs text-gray-500">
          좌우로 스크롤하여 더 많은 날짜를 확인하세요 →
        </div>
      )}

      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
