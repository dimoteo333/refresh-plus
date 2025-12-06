"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { MapPin, Search, Heart, Bell, BellOff } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import BottomNav from "@/components/layout/BottomNav";
import { accommodationApi, wishlistApi } from "@/lib/api";
import { SearchAccommodation } from "@/types/accommodation";

export default function SearchPage() {
  const [keyword, setKeyword] = useState("");
  const [searchResults, setSearchResults] = useState<SearchAccommodation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 검색 실행 (키워드가 변경될 때마다)
  useEffect(() => {
    const fetchSearchResults = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem("user_id") || "";
        const response = await accommodationApi.search(token, keyword);
        setSearchResults(response.data);
      } catch (error) {
        console.error("검색 실패:", error);
      } finally {
        setIsLoading(false);
      }
    };

    // 300ms 디바운스
    const timeoutId = setTimeout(() => {
      fetchSearchResults();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [keyword]);

  // 즐겨찾기 토글
  const handleWishlistToggle = async (accommodationId: string, isWishlisted: boolean) => {
    try {
      const token = localStorage.getItem("user_id") || "";

      if (isWishlisted) {
        // 즐겨찾기 해제 - wishlist ID를 찾아서 삭제
        const wishlistResponse = await wishlistApi.getAll(token);
        const wishlistItem = wishlistResponse.data.find(
          (item: any) => item.accommodation_id === accommodationId
        );
        if (wishlistItem) {
          await wishlistApi.remove(token, wishlistItem.id);
        }
      } else {
        // 즐겨찾기 추가
        await wishlistApi.add(token, accommodationId);
      }

      // 검색 결과 갱신
      const response = await accommodationApi.search(token, keyword);
      setSearchResults(response.data);
    } catch (error) {
      console.error("즐겨찾기 토글 실패:", error);
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
                src="/images/sol-bear.svg"
                alt="SOL 캐릭터 로고"
                width={48}
                height={48}
                className="h-full w-full object-cover"
              />
            </div>
            <div>
              <p className="text-sm font-semibold text-sky-700">검색</p>
              <p className="text-xs text-gray-600">지역, 숙소명으로 찾기</p>
            </div>
          </div>
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-8">
          {/* 검색 섹션 */}
          <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-4 shadow-lg backdrop-blur-lg sm:p-6">
            <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl">
              원하는 숙소를 검색하세요
            </h1>

            <div className="mt-4 flex items-center gap-3 rounded-2xl border border-sky-100/70 bg-sky-50/70 px-4 py-3 shadow-inner">
              <Search className="h-5 w-5 text-sky-500" />
              <input
                type="text"
                placeholder="지역, 숙소명 검색"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none"
              />
            </div>

            {keyword && (
              <p className="mt-3 text-xs text-slate-600">
                &quot;{keyword}&quot; 검색 결과: {searchResults.length}개
              </p>
            )}
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
                  className="relative overflow-hidden border-sky-100/80 bg-white/80 shadow-sm backdrop-blur transition-shadow hover:shadow-md"
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
                        onClick={() =>
                          handleWishlistToggle(
                            accommodation.id,
                            accommodation.is_wishlisted
                          )
                        }
                        className={`rounded-full p-2 shadow-sm backdrop-blur-sm transition ${
                          accommodation.is_wishlisted
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
                    <h3 className="text-base font-semibold text-slate-900">
                      {accommodation.name}
                    </h3>
                    <p className="mt-1 text-xs text-slate-600">
                      {accommodation.accommodation_type || "숙소"}
                    </p>

                    {/* 평균 점수 */}
                    {accommodation.avg_score !== null &&
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
