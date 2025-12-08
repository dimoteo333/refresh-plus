"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Heart, MapPin, Calendar, Bell, BellOff, Trash2, CalendarPlus } from "lucide-react";
import { useWishlist } from "@/hooks/useWishlist";
import { useAuth } from "@/contexts/AuthContext";
import { accommodationApi } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";
import { Badge } from "@/components/ui/badge";
import { Wishlist } from "@/types/wishlist";
import DateCalendar from "@/components/wishlist/DateCalendar";

interface AccommodationInfo {
  id: string;
  name: string;
  region: string;
  first_image?: string;
  avg_score?: number;
}

export default function WishlistPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { wishlist, removeFromWishlist, removeById, updateWishlist, addToWishlist, isLoading } = useWishlist();
  const [accommodationDetails, setAccommodationDetails] = useState<Record<string, AccommodationInfo>>({});
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [selectedAccommodation, setSelectedAccommodation] = useState<{ id: string; name: string } | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login?redirect=/wishlist");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    const fetchAccommodationDetails = async () => {
      if (!wishlist || wishlist.length === 0) return;

      const details: Record<string, AccommodationInfo> = {};

      for (const item of wishlist) {
        try {
          const response = await accommodationApi.getDetailPage(item.accommodation_id);
          const data = response.data;
          details[item.accommodation_id] = {
            id: data.id,
            name: data.name,
            region: data.region,
            first_image: data.images?.[0],
          };
        } catch (err) {
          console.error(`Failed to fetch accommodation ${item.accommodation_id}:`, err);
        }
      }

      setAccommodationDetails(details);
    };

    fetchAccommodationDetails();
  }, [wishlist]);

  const handleRemove = async (accommodationId: string) => {
    if (confirm("이 숙소를 찜 목록에서 삭제하시겠습니까?")) {
      try {
        await removeFromWishlist(accommodationId);
      } catch (err: any) {
        alert(err.response?.data?.detail || "삭제 중 오류가 발생했습니다.");
      }
    }
  };

  const handleToggleNotification = async (accommodationId: string) => {
    try {
      // 해당 숙소의 모든 날짜별 wishlist 조회
      const accommodationWishlists = wishlist.filter(
        (w: Wishlist) => w.accommodation_id === accommodationId
      );

      // 현재 알림 상태 확인 (하나라도 true면 모두 false로, 모두 false면 모두 true로)
      const hasEnabledNotification = accommodationWishlists.some((w: Wishlist) => w.notify_enabled);
      const newNotifyState = !hasEnabledNotification;

      // 모든 wishlist 항목에 대해 일괄 업데이트
      await Promise.all(
        accommodationWishlists.map((w: Wishlist) =>
          updateWishlist({
            id: w.id,
            data: {
              notify_enabled: newNotifyState,
            },
          })
        )
      );
    } catch (err: any) {
      alert(err.response?.data?.detail || "알림 설정 변경 중 오류가 발생했습니다.");
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const handleOpenCalendar = (accommodationId: string) => {
    const accommodation = accommodationDetails[accommodationId];
    if (accommodation) {
      setSelectedAccommodation({ id: accommodationId, name: accommodation.name });
      setCalendarOpen(true);
    }
  };

  const handleDatesChange = async (dates: string[]) => {
    if (!selectedAccommodation) return;

    try {
      // 현재 해당 숙소의 날짜별 wishlist 조회
      const currentDateWishlists = wishlist.filter(
        (w: Wishlist) =>
          w.accommodation_id === selectedAccommodation.id &&
          w.desired_date !== null
      );

      const currentDates = currentDateWishlists.map((w: Wishlist) => w.desired_date!);

      // 삭제할 날짜들 (현재 있는데 새로 선택 안된 것들)
      const datesToRemove = currentDates.filter((d: string) => !dates.includes(d));

      // 추가할 날짜들 (새로 선택된 것 중 현재 없는 것들)
      const datesToAdd = dates.filter((d: string) => !currentDates.includes(d));

      // 삭제 처리
      for (const date of datesToRemove) {
        const wishlistItem = currentDateWishlists.find((w: Wishlist) => w.desired_date === date);
        if (wishlistItem) {
          await removeById(wishlistItem.id);
        }
      }

      // 추가 처리
      for (const date of datesToAdd) {
        await addToWishlist({
          accommodation_id: selectedAccommodation.id,
          desired_date: date,
          notify_enabled: true,
        });
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "날짜 알림 설정 중 오류가 발생했습니다.");
    }
  };

  const getAccommodationDates = (accommodationId: string): string[] => {
    return wishlist
      .filter((w: Wishlist) => w.accommodation_id === accommodationId && w.desired_date !== null)
      .map((w: Wishlist) => w.desired_date!)
      .sort();
  };

  // 숙소별로 그룹화하여 중복 제거
  const getUniqueAccommodations = (): Wishlist[] => {
    const accommodationMap = new Map<string, Wishlist>();

    wishlist.forEach((item: Wishlist) => {
      if (!accommodationMap.has(item.accommodation_id)) {
        accommodationMap.set(item.accommodation_id, item);
      }
    });

    return Array.from(accommodationMap.values());
  };

  // 해당 숙소의 알림 상태 확인 (하나라도 알림이 켜져 있으면 true)
  const isNotificationEnabled = (accommodationId: string): boolean => {
    return wishlist
      .filter((w: Wishlist) => w.accommodation_id === accommodationId)
      .some((w: Wishlist) => w.notify_enabled);
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50/70 to-white flex items-center justify-center">
        <div className="text-center text-slate-700">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-sky-600"></div>
          <p className="mt-4 text-sm">로그인 확인 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50/70 to-white text-gray-900">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-28 pt-6 sm:px-6 lg:px-8">
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
              <p className="text-sm font-semibold text-sky-700">찜한 숙소</p>
              <p className="text-xs text-gray-600">즐겨찾기 · 알림 관리</p>
            </div>
          </div>
          {wishlist && wishlist.length > 0 && (
            <Badge className="bg-sky-100 text-sky-800">
              총 {getUniqueAccommodations().length}개
            </Badge>
          )}
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-6">
          <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-5 shadow-lg backdrop-blur-lg sm:p-6">
            <div className="flex items-center justify-between gap-3">
            </div>

            <div className="mt-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-12 text-slate-700">
                  <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-sky-600"></div>
                </div>
              ) : wishlist && wishlist.length === 0 ? (
                <div className="text-center py-12">
                  <Heart className="h-16 w-16 text-slate-200 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-slate-900 mb-2">찜한 숙소가 없습니다</h2>
                  <p className="text-slate-600 mb-6">마음에 드는 숙소를 찜해보세요!</p>
                  <button
                    onClick={() => router.push("/search")}
                    className="rounded-xl bg-sky-600 px-6 py-3 text-white shadow hover:bg-sky-700 transition"
                  >
                    숙소 둘러보기
                  </button>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {getUniqueAccommodations().map((item: Wishlist) => {
                    const accommodation = accommodationDetails[item.accommodation_id];

                    return (
                      <div
                        key={item.id}
                        className="overflow-hidden rounded-2xl border border-sky-100/70 bg-white shadow-sm transition hover:shadow-md"
                      >
                        <div
                          className="relative h-48 cursor-pointer bg-gray-100"
                          onClick={() => router.push(`/accommodations/${item.accommodation_id}`)}
                        >
                          {accommodation?.first_image ? (
                            <img
                              src={accommodation.first_image}
                              alt={accommodation.name}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="flex h-full items-center justify-center">
                              <Heart className="h-12 w-12 text-gray-300" />
                            </div>
                          )}
                          <div className="absolute top-2 right-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRemove(item.accommodation_id);
                              }}
                              className="rounded-full bg-white/90 p-2 backdrop-blur transition hover:bg-white"
                              aria-label="삭제"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          </div>
                        </div>

                        <div className="p-4">
                          <h3
                            className="mb-2 cursor-pointer text-lg font-semibold text-gray-900 hover:text-blue-600"
                            onClick={() => router.push(`/accommodations/${item.accommodation_id}`)}
                          >
                            {accommodation?.name || "숙소 정보 로딩 중..."}
                          </h3>

                          {accommodation?.region && (
                            <div className="mb-3 flex items-center gap-1 text-sm text-gray-600">
                              <MapPin className="h-4 w-4" />
                              <span>{accommodation.region}</span>
                            </div>
                          )}

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenCalendar(item.accommodation_id);
                            }}
                            className="mb-3 flex w-full items-center justify-center gap-2 rounded-lg bg-sky-50 px-3 py-2 text-sm font-medium text-sky-700 transition hover:bg-sky-100"
                          >
                            <CalendarPlus className="h-4 w-4" />
                            날짜 알림 설정
                          </button>

                          {getAccommodationDates(item.accommodation_id).length > 0 && (
                            <div className="mb-3">
                              <p className="mb-2 text-xs text-gray-600">알림 설정 날짜:</p>
                              <div className="flex flex-wrap gap-1">
                                {getAccommodationDates(item.accommodation_id).map((date) => {
                                  const dateObj = new Date(date);
                                  const month = dateObj.getMonth() + 1;
                                  const day = dateObj.getDate();
                                  const weekday = dateObj.toLocaleDateString("ko-KR", { weekday: "short" });
                                  return (
                                    <span
                                      key={date}
                                      className="rounded bg-sky-100 px-2 py-1 text-xs text-sky-700"
                                    >
                                      {`${month}/${day}(${weekday})`}
                                    </span>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                          <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                            <Badge
                              variant={isNotificationEnabled(item.accommodation_id) ? "default" : "secondary"}
                              className="text-xs"
                            >
                              {isNotificationEnabled(item.accommodation_id) ? "알림 ON" : "알림 OFF"}
                            </Badge>

                            <button
                              onClick={() => handleToggleNotification(item.accommodation_id)}
                              className="flex items-center gap-1 text-xs text-gray-600 transition hover:text-blue-600"
                              aria-label="알림 토글"
                            >
                              {isNotificationEnabled(item.accommodation_id) ? (
                                <BellOff className="h-4 w-4" />
                              ) : (
                                <Bell className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
        </main>
      </div>

      <BottomNav activeHref="/wishlist" />

      {calendarOpen && selectedAccommodation && (
        <DateCalendar
          accommodationId={selectedAccommodation.id}
          accommodationName={selectedAccommodation.name}
          selectedDates={getAccommodationDates(selectedAccommodation.id)}
          onClose={() => setCalendarOpen(false)}
          onDatesChange={handleDatesChange}
        />
      )}
    </div>
  );
}
