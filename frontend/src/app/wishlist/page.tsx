"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

  const handleToggleNotification = async (item: Wishlist) => {
    try {
      await updateWishlist({
        id: item.id,
        data: {
          notify_enabled: !item.notify_enabled,
        },
      });
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
      const datesToRemove = currentDates.filter((d) => !dates.includes(d));

      // 추가할 날짜들 (새로 선택된 것 중 현재 없는 것들)
      const datesToAdd = dates.filter((d) => !currentDates.includes(d));

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

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로그인 확인 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-32">
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <Heart className="h-6 w-6 text-red-500" />
            <h1 className="text-2xl font-bold text-gray-900">찜한 숙소</h1>
          </div>
          {wishlist && wishlist.length > 0 && (
            <p className="mt-2 text-sm text-gray-600">총 {wishlist.length}개의 숙소</p>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : wishlist && wishlist.length === 0 ? (
          <div className="text-center py-12">
            <Heart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">찜한 숙소가 없습니다</h2>
            <p className="text-gray-600 mb-6">마음에 드는 숙소를 찜해보세요!</p>
            <button
              onClick={() => router.push("/search")}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              숙소 둘러보기
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {wishlist.map((item: Wishlist) => {
              const accommodation = accommodationDetails[item.accommodation_id];

              return (
                <div
                  key={item.id}
                  className="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition"
                >
                  <div
                    className="relative h-48 bg-gray-200 cursor-pointer"
                    onClick={() => router.push(`/accommodations/${item.accommodation_id}`)}
                  >
                    {accommodation?.first_image ? (
                      <img
                        src={accommodation.first_image}
                        alt={accommodation.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <Heart className="h-12 w-12 text-gray-300" />
                      </div>
                    )}
                    <div className="absolute top-2 right-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemove(item.accommodation_id);
                        }}
                        className="bg-white/90 backdrop-blur p-2 rounded-full hover:bg-white transition"
                        aria-label="삭제"
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </button>
                    </div>
                  </div>

                  <div className="p-4">
                    <h3
                      className="text-lg font-semibold text-gray-900 mb-2 cursor-pointer hover:text-blue-600"
                      onClick={() => router.push(`/accommodations/${item.accommodation_id}`)}
                    >
                      {accommodation?.name || "숙소 정보 로딩 중..."}
                    </h3>

                    {accommodation?.region && (
                      <div className="flex items-center gap-1 text-sm text-gray-600 mb-3">
                        <MapPin className="h-4 w-4" />
                        <span>{accommodation.region}</span>
                      </div>
                    )}

                    {/* 날짜 알림 설정 버튼 */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenCalendar(item.accommodation_id);
                      }}
                      className="w-full mb-3 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition flex items-center justify-center gap-2"
                    >
                      <CalendarPlus className="h-4 w-4" />
                      날짜 알림 설정
                    </button>

                    {/* 설정된 날짜 알림 표시 */}
                    {getAccommodationDates(item.accommodation_id).length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-600 mb-2">알림 설정 날짜:</p>
                        <div className="flex flex-wrap gap-1">
                          {getAccommodationDates(item.accommodation_id).map((date) => {
                            const dateObj = new Date(date);
                            const month = dateObj.getMonth() + 1;
                            const day = dateObj.getDate();
                            const weekday = dateObj.toLocaleDateString("ko-KR", { weekday: "short" });
                            return (
                              <span
                                key={date}
                                className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                              >
                                {`${month}/${day}(${weekday})`}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                      <Badge
                        variant={item.notify_enabled ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {item.notify_enabled ? "알림 ON" : "알림 OFF"}
                      </Badge>

                      <button
                        onClick={() => handleToggleNotification(item)}
                        className="flex items-center gap-1 text-xs text-gray-600 hover:text-blue-600 transition"
                        aria-label="알림 토글"
                      >
                        {item.notify_enabled ? (
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

      <BottomNav activeHref="/wishlist" />

      {/* Date Calendar Modal */}
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
