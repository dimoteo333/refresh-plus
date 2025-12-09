"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { MapPin, Search, Heart, Bell, BellOff, Calendar, Users, Star, Flame, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import BottomNav from "@/components/layout/BottomNav";
import { accommodationApi, wishlistApi } from "@/lib/api";
import { SearchAccommodation } from "@/types/accommodation";
import { useAuth } from "@/contexts/AuthContext";
import { useQueryClient } from "@tanstack/react-query";

// SOL 점수 원형 차트 컴포넌트
const CircularScore = ({ score }: { score: number }) => {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // 점수에 따른 색상 결정
  const getColor = (score: number) => {
    if (score >= 80) return "#10b981"; // green-500
    if (score >= 60) return "#3b82f6"; // blue-500
    if (score >= 40) return "#f59e0b"; // amber-500
    return "#ef4444"; // red-500
  };

  const color = getColor(score);

  return (
    <div className="relative flex items-center justify-center">
      <svg className="transform -rotate-90" width="70" height="70">
        {/* 배경 원 */}
        <circle
          cx="35"
          cy="35"
          r={radius}
          stroke="#e5e7eb"
          strokeWidth="6"
          fill="none"
        />
        {/* 진행 원 */}
        <circle
          cx="35"
          cy="35"
          r={radius}
          stroke={color}
          strokeWidth="6"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      {/* 중앙 점수 텍스트 */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="text-[10px] text-slate-500 font-medium">SOL</span>
      </div>
    </div>
  );
};

export default function SearchPage() {
  const router = useRouter();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("전체");
  const [regionOptions, setRegionOptions] = useState<string[]>(["전체"]);
  const [sortBy, setSortBy] = useState<"avg_score" | "name" | "wishlist" | "price" | "sol_score">(
    "avg_score"
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedDate, setSelectedDate] = useState("");
  const [searchResults, setSearchResults] = useState<SearchAccommodation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingWishlist, setUpdatingWishlist] = useState<string | null>(null);

  // 기본 날짜: 오늘 + 1달
  const getDefaultDate = () => {
    const today = new Date();
    const oneMonthLater = new Date(today.setMonth(today.getMonth() + 1));
    return oneMonthLater.toISOString().split("T")[0];
  };

  const sortOptions: {
    value: "avg_score" | "name" | "wishlist" | "price" | "sol_score";
    label: string;
  }[] = [
    { value: "avg_score", label: "평균 점수 순" },
    { value: "sol_score", label: "SOL 점수" },
    { value: "name", label: "이름 순" },
  ];

  useEffect(() => {
    const fetchRegions = async () => {
      try {
        const response = await accommodationApi.getRegions();
        const regions: string[] = response.data || [];
        const uniqueRegions = Array.from(new Set(regions.filter(Boolean)));
        setRegionOptions(["전체", ...uniqueRegions]);
      } catch (error) {
        console.error("지역 목록 조회 실패:", error);
      }
    };

    fetchRegions();
  }, []);

  const fetchSearchResults = useCallback(async () => {
    try {
      setIsLoading(true);
      // user.id를 전달하여 위시리스트 정보를 조회
      const userId = user?.id || "";
      const response = await accommodationApi.search(userId, {
        keyword,
        region: selectedRegion === "전체" ? undefined : selectedRegion,
        sort_by: sortBy,
        sort_order: sortOrder,
        date: selectedDate || undefined,
      });
      setSearchResults(response.data);
    } catch (error) {
      console.error("검색 실패:", error);
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, keyword, selectedRegion, sortBy, sortOrder, selectedDate]);

  // 검색 실행 (조건이 변경될 때마다)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchSearchResults();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [fetchSearchResults]);

  // 즐겨찾기 토글
  const handleWishlistToggle = async (accommodationId: string, isWishlisted: boolean) => {
    // 이미 처리 중이면 무시
    if (updatingWishlist === accommodationId) {
      return;
    }

    try {
      setUpdatingWishlist(accommodationId);

      // Optimistic update: 즉시 UI 업데이트 (즐겨찾기 상태 + 알림 아이콘)
      setSearchResults((prev) =>
        prev.map((acc) =>
          acc.id === accommodationId
            ? {
                ...acc,
                is_wishlisted: !isWishlisted,
                notify_enabled: !isWishlisted ? true : false // 추가 시 알림 ON, 해제 시 OFF
              }
            : acc
        )
      );

      const userId = user?.id || "";

      if (isWishlisted) {
        // 즐겨찾기 해제 - wishlist ID를 찾아서 삭제
        const wishlistResponse = await wishlistApi.getAll(userId);
        const wishlistItem = wishlistResponse.data.find(
          (item: any) => item.accommodation_id === accommodationId
        );
        if (wishlistItem) {
          await wishlistApi.remove(userId, wishlistItem.id);
        }
      } else {
        // 즐겨찾기 추가
        await wishlistApi.add(userId, {
          accommodation_id: accommodationId,
          notify_enabled: true,
        });
      }

      // React Query 캐시 무효화 (위시리스트 페이지 자동 갱신용)
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });

      // Optimistic update로 이미 UI가 업데이트되었으므로 fetchSearchResults 불필요
    } catch (error: any) {
      console.error("즐겨찾기 토글 실패:", error);

      // 에러 발생 시 롤백 (즐겨찾기 상태 + 알림 아이콘)
      setSearchResults((prev) =>
        prev.map((acc) =>
          acc.id === accommodationId
            ? {
                ...acc,
                is_wishlisted: isWishlisted,
                notify_enabled: isWishlisted ? true : false // 원래 상태로 복구
              }
            : acc
        )
      );

      // 사용자에게 에러 메시지 표시
      const errorMessage = error?.response?.data?.detail || "즐겨찾기 처리 중 오류가 발생했습니다.";
      alert(errorMessage);
    } finally {
      setUpdatingWishlist(null);
    }
  };

  // 알림 토글 (찜은 유지, 알림만 on/off)
  const handleNotificationToggle = async (accommodationId: string, currentNotifyEnabled: boolean) => {
    try {
      const userId = user?.id || "";

      // Optimistic update: 즉시 UI 업데이트
      setSearchResults((prev) =>
        prev.map((acc) =>
          acc.id === accommodationId
            ? { ...acc, notify_enabled: !currentNotifyEnabled }
            : acc
        )
      );

      // 해당 숙소의 wishlist 찾기
      const wishlistResponse = await wishlistApi.getAll(userId);
      const wishlistItem = wishlistResponse.data.find(
        (item: any) => item.accommodation_id === accommodationId && item.is_active
      );

      if (wishlistItem) {
        // 알림 설정만 업데이트
        await wishlistApi.update(userId, wishlistItem.id, {
          notify_enabled: !currentNotifyEnabled,
        });

        // React Query 캐시 무효화
        queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      }
    } catch (error: any) {
      console.error("알림 설정 변경 실패:", error);

      // 에러 발생 시 롤백
      setSearchResults((prev) =>
        prev.map((acc) =>
          acc.id === accommodationId
            ? { ...acc, notify_enabled: currentNotifyEnabled }
            : acc
        )
      );

      const errorMessage = error?.response?.data?.detail || "알림 설정 변경 중 오류가 발생했습니다.";
      alert(errorMessage);
    }
  };

  const handleSortClick = (value: typeof sortBy) => {
    if (sortBy === value) {
      setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(value);
      setSortOrder("desc");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50/70 to-white text-gray-900">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-28 pt-6 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="flex items-center justify-between gap-3 px-1 py-2 sm:px-2">
          <div className="flex items-center gap-3">
            <div className="relative h-12 w-12 overflow-hidden rounded-2xl border border-sky-100 bg-white shadow-sm">
              <Image
                src="/images/sol_standing.png"
                alt="SOL 스탠딩 로고"
                width={48}
                height={57}
                className="h-full w-full object-contain p-1"
              />
            </div>
            <div>
              <p className="text-sm font-semibold text-sky-700">검색</p>
              <p className="text-xs text-gray-600">지역, 숙소명으로 찾기</p>
            </div>
          </div>
          <button
            onClick={() => router.push("/popular")}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-red-500 to-orange-500 px-3 py-2 text-white shadow-sm transition-all hover:shadow-md hover:scale-105"
          >
            <Flame className="h-4 w-4" />
            <span className="text-xs font-semibold">인기 Top 10</span>
          </button>
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-6">
          {/* 검색 섹션 */}
          <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-5 shadow-lg backdrop-blur-lg">
            <h1 className="text-lg font-bold text-slate-900 sm:text-xl">
              원하는 숙소를 검색하세요
            </h1>

            <div className="mt-4 flex flex-col gap-3">
              {/* 검색어 입력 */}
              <div className="flex items-center gap-3 rounded-2xl border border-sky-100/70 bg-gradient-to-r from-sky-50/70 to-blue-50/50 px-4 py-3 shadow-sm">
                <Search className="h-5 w-5 flex-shrink-0 text-sky-600" />
                <input
                  type="text"
                  placeholder="지역, 숙소명 검색"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none"
                />
              </div>

              {/* 지역 & 날짜 필터 */}
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2 rounded-xl border border-sky-100/70 bg-white px-3 py-2.5 shadow-sm">
                  <MapPin className="h-4 w-4 flex-shrink-0 text-sky-600" />
                  <select
                    value={selectedRegion}
                    onChange={(e) => setSelectedRegion(e.target.value)}
                    className="w-full bg-transparent text-sm text-slate-800 focus:outline-none"
                  >
                    {regionOptions.map((region) => (
                      <option key={region} value={region}>
                        {region}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-2 rounded-xl border border-sky-100/70 bg-white px-3 py-2.5 shadow-sm">
                  <Calendar className="h-4 w-4 flex-shrink-0 text-sky-600" />
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    placeholder={getDefaultDate()}
                    className="w-full bg-transparent text-xs text-slate-800 focus:outline-none"
                  />
                </div>
              </div>

              {/* 정렬 옵션 */}
              <div className="flex items-center gap-2 overflow-x-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                <span className="text-xs font-semibold text-slate-700 whitespace-nowrap">정렬</span>
                <div className="flex gap-1.5">
                  {sortOptions.map((option) => {
                    const isActive = sortBy === option.value;
                    const orderLabel = isActive ? (sortOrder === "desc" ? "↓" : "↑") : "";
                    return (
                      <button
                        key={option.value}
                        onClick={() => handleSortClick(option.value)}
                        className={`rounded-full px-3 py-1.5 text-xs font-medium transition whitespace-nowrap ${
                          isActive
                            ? "bg-sky-600 text-white shadow-sm"
                            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                        }`}
                      >
                        {option.label} {orderLabel}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 검색 결과 요약 */}
              {(keyword || selectedRegion !== "전체" || selectedDate) && (
                <div className="mt-1 flex items-center justify-between rounded-lg bg-sky-50 px-3 py-2">
                  <p className="text-xs text-slate-700 font-medium">
                    검색 결과 <span className="text-sky-700 font-bold">{searchResults.length}</span>개
                    {selectedDate && (
                      <span className="ml-1 text-slate-500">
                        ({selectedDate})
                      </span>
                    )}
                  </p>
                  <button
                    onClick={() => {
                      setKeyword("");
                      setSelectedRegion("전체");
                      setSelectedDate("");
                    }}
                    className="text-xs text-sky-600 hover:text-sky-700 font-medium"
                  >
                    초기화
                  </button>
                </div>
              )}
            </div>
          </section>

          {/* 검색 결과 */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {isLoading ? (
              <div className="col-span-full py-12 text-center text-sm text-slate-600">
                검색 중...
              </div>
            ) : searchResults.length === 0 ? (
              <div className="col-span-full py-12 text-center text-sm text-slate-600">
                검색 결과가 없습니다.
              </div>
            ) : (
              searchResults.map((accommodation) => (
                <Card
                  key={accommodation.id}
                  onClick={() => router.push(`/accommodations/${accommodation.id}`)}
                  className="relative cursor-pointer overflow-hidden border-sky-100/80 bg-white/80 shadow-sm backdrop-blur transition-shadow hover:shadow-md"
                >
                  {/* 숙소 이미지 */}
                  <div className="relative h-48 w-full overflow-hidden bg-gradient-to-br from-sky-100 to-blue-100">
                    {accommodation.first_image ? (
                      <Image
                        src={accommodation.first_image}
                        alt={accommodation.name}
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <MapPin className="h-12 w-12 text-sky-300" />
                      </div>
                    )}

                    {/* 지역 배지 (이미지 위에 표시) */}
                    <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-white/90 px-3 py-1.5 text-xs font-medium text-sky-700 shadow-sm backdrop-blur-sm">
                      <MapPin className="h-3.5 w-3.5" />
                      {accommodation.region}
                    </div>

                    {/* 즐겨찾기 & 알림 버튼 (우측 상단) */}
                    <div className="absolute right-3 top-3 flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleWishlistToggle(
                            accommodation.id,
                            accommodation.is_wishlisted
                          );
                        }}
                        disabled={updatingWishlist === accommodation.id}
                        className={`rounded-full p-2 shadow-sm backdrop-blur-sm transition ${
                          updatingWishlist === accommodation.id
                            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                            : accommodation.is_wishlisted
                            ? "bg-red-500 text-white"
                            : "bg-white/90 text-gray-600 hover:bg-red-50"
                        }`}
                      >
                        <Heart
                          className={`h-4 w-4 ${
                            accommodation.is_wishlisted ? "fill-current" : ""
                          }`}
                        />
                      </button>
                      {accommodation.is_wishlisted && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleNotificationToggle(
                              accommodation.id,
                              accommodation.notify_enabled
                            );
                          }}
                          className={`rounded-full p-2 shadow-sm backdrop-blur-sm transition ${
                            accommodation.notify_enabled
                              ? "bg-blue-500 text-white"
                              : "bg-white/90 text-gray-600 hover:bg-blue-50"
                          }`}
                        >
                          {accommodation.notify_enabled ? (
                            <Bell className="h-4 w-4" />
                          ) : (
                            <BellOff className="h-4 w-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 숙소 정보 */}
                  <CardContent className="p-4">
                    <div className="flex gap-4">
                      {/* 왼쪽: 숙소 정보 */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-base font-semibold text-slate-900">
                          {accommodation.name}
                        </h3>
                        <p className="mt-1 text-xs text-slate-600">
                          {accommodation.accommodation_type || "숙소"}
                        </p>

                        {accommodation.summary && accommodation.summary.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {accommodation.summary.slice(0, 5).map((item, index) => (
                              <Badge
                                key={`${accommodation.id}-summary-${index}`}
                                className="bg-sky-100 text-sky-800 hover:bg-sky-100"
                              >
                                {item}
                              </Badge>
                            ))}
                          </div>
                        )}

                        {/* 날짜별 신청 현황 (날짜 선택 시) */}
                        {selectedDate && accommodation.date && (
                          <div className="mt-3 space-y-2">
                            <div className="flex items-center justify-between rounded-lg bg-blue-50 px-3 py-2">
                              <div className="flex items-center gap-2">
                                <Users className="h-4 w-4 text-blue-600" />
                                <span className="text-xs text-slate-600">
                                  신청 인원
                                </span>
                              </div>
                              <span className="text-sm font-semibold text-blue-700">
                                {accommodation.applicants || 0}명
                              </span>
                            </div>
                            <div className="flex items-center justify-between rounded-lg bg-amber-50 px-3 py-2">
                              <div className="flex items-center gap-2">
                                <Star className="h-4 w-4 text-amber-600" />
                                <span className="text-xs text-slate-600">
                                  신청 점수
                                </span>
                              </div>
                              <span className="text-sm font-semibold text-amber-700">
                                {accommodation.score ? accommodation.score.toFixed(1) : 0}점
                              </span>
                            </div>

                            {/* AI 예측 점수 */}
                            {(() => {
                              if (!accommodation.weekday_averages || accommodation.weekday_averages.length === 0) {
                                return null;
                              }

                              // 선택된 날짜의 요일 계산 (0=월, 1=화, ..., 6=일)
                              const date = new Date(selectedDate);
                              const dayOfWeek = (date.getDay() + 6) % 7; // 일요일(0)을 6으로 변환

                              // 해당 요일의 평균 점수 찾기
                              const selectedWeekdayData = accommodation.weekday_averages.find(
                                (d) => d.weekday === dayOfWeek
                              );

                              if (!selectedWeekdayData || selectedWeekdayData.count === 0) {
                                return null;
                              }

                              // 전체 평균 점수 계산
                              const validScores = accommodation.weekday_averages.filter((d) => d.count > 0);
                              if (validScores.length === 0) {
                                return null;
                              }

                              const totalScore = validScores.reduce((sum, d) => sum + d.avg_score, 0);
                              const overallAverage = Number(accommodation.score);

                              const diff = selectedWeekdayData.avg_score - overallAverage;
                              const weekdayName = selectedWeekdayData.weekday_name;

                              let bgGradient = "from-violet-50 to-indigo-50";
                              let borderColor = "border-violet-100";
                              let iconColor = "text-violet-600";
                              let textColor = "text-violet-900";
                              let message = `예측 점수: ${selectedWeekdayData.avg_score.toFixed(1)}점`;
                              let subMessage = `평균 ${overallAverage.toFixed(1)}점과 비슷한 수준`;

                              return (
                                <div className={`rounded-xl border-2 ${borderColor} bg-gradient-to-br ${bgGradient} px-4 py-3 shadow-sm backdrop-blur-sm`}>
                                  <div className="flex items-start gap-2">
                                    <Sparkles className={`h-4 w-4 mt-0.5 flex-shrink-0 ${iconColor} animate-pulse`} />
                                    <div className="flex-1">
                                      <p className={`text-xs font-bold ${textColor} leading-tight`}>
                                        {message}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              );
                            })()}
                          </div>
                        )}

                        {/* 평균 점수 (날짜 미선택 시) */}
                        {!selectedDate && accommodation.avg_score !== null &&
                          accommodation.avg_score !== undefined && (
                            <div className="mt-3 flex items-center justify-between rounded-lg bg-sky-50 px-3 py-2">
                              <span className="text-xs text-slate-600">
                                평균 점수
                              </span>
                              <span className="text-sm font-semibold text-sky-700">
                                {accommodation.avg_score}점
                              </span>
                            </div>
                          )}
                      </div>

                      {/* 오른쪽: SOL 점수 원형 차트 */}
                      {accommodation.sol_score !== null &&
                        accommodation.sol_score !== undefined && (
                        <div className="flex items-center justify-center">
                          <CircularScore score={accommodation.sol_score} />
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </section>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
