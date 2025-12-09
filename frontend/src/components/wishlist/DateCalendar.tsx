"use client";

import { useState, useEffect } from "react";
import { X, Calendar as CalendarIcon, Users, TrendingUp, Check } from "lucide-react";
import { AvailableDate } from "@/types/accommodation";
import { accommodationApi } from "@/lib/api";

interface DateCalendarProps {
  accommodationId: string;
  accommodationName: string;
  selectedDates: string[];
  onClose: () => void;
  onDatesChange: (dates: string[]) => void;
}

export default function DateCalendar({
  accommodationId,
  accommodationName,
  selectedDates,
  onClose,
  onDatesChange,
}: DateCalendarProps) {
  const [dates, setDates] = useState<AvailableDate[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [localSelectedDates, setLocalSelectedDates] = useState<string[]>(selectedDates);
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  useEffect(() => {
    fetchDates();
  }, [accommodationId, currentMonth]);

  const fetchDates = async () => {
    try {
      setLoading(true);
      // 현재 월의 시작과 끝
      const startDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
      const endDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);

      const response = await accommodationApi.getDates(accommodationId, {
        start_date: startDate.toISOString().split("T")[0],
        end_date: endDate.toISOString().split("T")[0],
      });

      setDates(response.data);

      // 초기 로드 시 신청 중인 날짜가 있는 월로 이동
      if (!initialLoadDone && response.data.length > 0) {
        const applicationOpenDates = response.data.filter(
          (d: AvailableDate) =>
            d.status === "신청중" || d.status === "신청가능(최초 객실오픈)"
        );

        if (applicationOpenDates.length > 0) {
          // 신청 중인 날짜가 있으면 그대로 유지
          setInitialLoadDone(true);
        } else {
          // 신청 중인 날짜가 없으면 다음 월로 이동
          const nextMonth = new Date(currentMonth);
          nextMonth.setMonth(nextMonth.getMonth() + 1);
          setCurrentMonth(nextMonth);
        }
      } else if (!initialLoadDone) {
        setInitialLoadDone(true);
      }
    } catch (error) {
      console.error("Failed to fetch dates:", error);
      setInitialLoadDone(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDateToggle = (day: number) => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    setLocalSelectedDates((prev) =>
      prev.includes(dateStr) ? prev.filter((d) => d !== dateStr) : [...prev, dateStr]
    );
  };

  const handleSave = () => {
    onDatesChange(localSelectedDates);
    onClose();
  };

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const getDaysInMonth = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDayOfWeek = firstDay.getDay();

    const days: (number | null)[] = [];

    // 이전 달의 빈 칸 채우기
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null);
    }

    // 현재 달의 날짜 채우기
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }

    return days;
  };

  const getDateInfo = (day: number): AvailableDate | undefined => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return dates.find((d) => d.date === dateStr);
  };

  const isDateSelected = (day: number): boolean => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return localSelectedDates.includes(dateStr);
  };

  const weekDays = ["일", "월", "화", "수", "목", "금", "토"];
  const days = getDaysInMonth();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarIcon className="h-6 w-6" />
            <div>
              <h2 className="text-xl font-bold">{accommodationName}</h2>
              <p className="text-sm text-blue-100">알림 받을 날짜를 선택하세요</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Month Navigation */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={handlePrevMonth}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
            >
              이전 달
            </button>
            <h3 className="text-lg font-semibold">
              {currentMonth.getFullYear()}년 {currentMonth.getMonth() + 1}월
            </h3>
            <button
              onClick={handleNextMonth}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
            >
              다음 달
            </button>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap items-center gap-3 sm:gap-4 mb-4 p-2.5 sm:p-3 bg-gray-50 rounded-lg text-xs sm:text-sm">
            <div className="flex items-center gap-1.5 sm:gap-2">
              <div className="w-3 h-3 sm:w-4 sm:h-4 bg-blue-500 rounded"></div>
              <span className="text-gray-700">선택됨</span>
            </div>
            <div className="flex items-center gap-1.5 sm:gap-2">
              <div className="w-3 h-3 sm:w-4 sm:h-4 border-2 border-red-500 rounded"></div>
              <span className="text-gray-700">신청 중</span>
            </div>
            <div className="flex items-center gap-1.5 sm:gap-2">
              <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4 text-gray-600" />
              <span className="text-gray-700">점수</span>
            </div>
            <div className="flex items-center gap-1.5 sm:gap-2">
              <Users className="h-3 w-3 sm:h-4 sm:w-4 text-gray-600" />
              <span className="text-gray-700">신청인원</span>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-2">
                {/* Week Day Headers */}
                {weekDays.map((day, index) => (
                  <div
                    key={day}
                    className={`text-center font-semibold py-2 ${
                      index === 0 ? "text-red-600" : index === 6 ? "text-blue-600" : "text-gray-700"
                    }`}
                  >
                    {day}
                  </div>
                ))}

                {/* Calendar Days */}
                {days.map((day, index) => {
                  if (day === null) {
                    return <div key={`empty-${index}`} className="min-h-[70px] sm:min-h-[85px]"></div>;
                  }

                  const dateInfo = getDateInfo(day);
                  const isSelected = isDateSelected(day);
                  const hasInfo = !!dateInfo;

                  // 신청 중인 상태 확인
                  const isApplicationOpen = hasInfo && (
                    dateInfo.status === "신청중" ||
                    dateInfo.status === "신청가능(최초 객실오픈)"
                  );

                  // 마감된 상태 확인
                  const isClosed = hasInfo && dateInfo.status === "마감(신청종료)";

                  return (
                    <button
                      key={day}
                      onClick={() => !isClosed && handleDateToggle(day)}
                      disabled={isClosed}
                      className={`
                        min-h-[70px] sm:min-h-[85px] p-1 sm:p-1.5 rounded-xl sm:rounded-2xl border-2 transition
                        ${isClosed
                          ? "cursor-not-allowed bg-gray-100 border-gray-300 opacity-60"
                          : "cursor-pointer hover:shadow-md"
                        }
                        ${isSelected
                          ? "border-blue-500 bg-blue-50"
                          : isApplicationOpen
                            ? "border-red-500 bg-red-50/30"
                            : !isClosed
                              ? "border-gray-200 hover:border-gray-300"
                              : ""
                        }
                      `}
                    >
                      <div className="flex flex-col items-center justify-center h-full gap-0.5">
                        <div className="flex items-center gap-1">
                          <span className={`text-xs sm:text-sm font-semibold ${
                            isClosed
                              ? "text-gray-400"
                              : index % 7 === 0
                                ? "text-red-600"
                                : index % 7 === 6
                                  ? "text-blue-600"
                                  : "text-gray-700"
                          }`}>
                            {day}
                          </span>
                          {isSelected && !isClosed && <Check className="h-2.5 w-2.5 sm:h-3 sm:w-3 text-blue-600" />}
                        </div>
                        {hasInfo && (
                          <>
                            {/* 신청 중인 경우: 점수 + 신청 인원 */}
                            {isApplicationOpen && (
                              <div className="flex flex-col items-center gap-0.5 w-full">
                                <div className="flex items-center gap-0.5 text-[10px] sm:text-[11px] text-gray-700">
                                  <TrendingUp className="h-2.5 w-2.5 sm:h-3 sm:w-3 flex-shrink-0" />
                                  <span className="font-medium truncate">{dateInfo.score.toFixed(1)}</span>
                                </div>
                                <div className="flex items-center gap-0.5 text-[10px] sm:text-[11px] text-gray-700">
                                  <Users className="h-2.5 w-2.5 sm:h-3 sm:w-3 flex-shrink-0" />
                                  <span className="font-medium truncate">{dateInfo.applicants}</span>
                                </div>
                              </div>
                            )}

                            {/* 마감된 경우: 점수만 (회색 음영) */}
                            {isClosed && (
                              <div className="flex items-center gap-0.5 text-[10px] sm:text-[11px] text-gray-400 mt-0.5">
                                <TrendingUp className="h-2.5 w-2.5 sm:h-3 sm:w-3 flex-shrink-0" />
                                <span className="truncate">{dateInfo.score.toFixed(1)}</span>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Selected Dates Summary */}
              {localSelectedDates.length > 0 && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">
                    선택한 날짜 ({localSelectedDates.length}개)
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {localSelectedDates.map((date) => (
                      <span
                        key={date}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                      >
                        {new Date(date).toLocaleDateString("ko-KR", {
                          month: "long",
                          day: "numeric",
                        })}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}
