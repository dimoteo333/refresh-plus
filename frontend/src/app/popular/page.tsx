"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { TrendingUp, Flame, Users, Trophy, Calendar, Target, ArrowLeft } from "lucide-react";
import BottomNav from "@/components/layout/BottomNav";
import { PopularAccommodation } from "@/types/accommodation";
import { accommodationApi } from "@/lib/api";

export default function PopularPage() {
  const router = useRouter();
  const [accommodations, setAccommodations] = useState<PopularAccommodation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPopularAccommodations = async () => {
      try {
        setLoading(true);
        const response = await accommodationApi.getPopular(10);
        setAccommodations(response.data);
      } catch (error) {
        console.error("Failed to fetch popular accommodations:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPopularAccommodations();
  }, []);

  // 순위에 따른 배지 색상
  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return "bg-gradient-to-br from-yellow-400 to-yellow-600 text-white";
    if (rank === 2) return "bg-gradient-to-br from-gray-300 to-gray-500 text-white";
    if (rank === 3) return "bg-gradient-to-br from-orange-400 to-orange-600 text-white";
    return "bg-gradient-to-br from-blue-500 to-blue-600 text-white";
  };

  // 순위에 따른 아이콘
  const getRankIcon = (rank: number) => {
    if (rank <= 3) return <Trophy className="h-4 w-4" />;
    return <TrendingUp className="h-4 w-4" />;
  };

  // 날짜 포맷팅
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekdays = ["일", "월", "화", "수", "목", "금", "토"];
    const weekday = weekdays[date.getDay()];
    return `${month}/${day}(${weekday})`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-red-50 via-orange-50/70 to-white text-gray-900">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-28 pt-6 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-red-500 to-orange-500 text-white shadow-lg">
              <Flame className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">
                실시간 인기 <span className="text-red-600">Top 10</span>
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                지금 가장 핫한 숙소를 실시간으로 확인하세요
              </p>
            </div>
          </div>
        </header>

        {/* 로딩 상태 */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-600 border-r-transparent"></div>
              <p className="mt-4 text-slate-600">인기 숙소를 불러오는 중...</p>
            </div>
          </div>
        )}

        {/* 차트 리스트 */}
        {!loading && (
          <main className="flex-1">
            <div className="space-y-4">
              {accommodations.map((accommodation, index) => {
                const rank = index + 1;
                return (
                  <Link
                    key={accommodation.id}
                    href={`/accommodations/${accommodation.id}`}
                    className="block"
                  >
                    <div className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-red-300 hover:shadow-lg sm:p-5">
                      <div className="flex items-center gap-4">
                        {/* 숙소 이미지 (순위 배지 포함) */}
                        <div className="flex-shrink-0">
                          <div className="relative h-24 w-24 overflow-hidden rounded-xl bg-slate-100 sm:h-28 sm:w-28">
                            {accommodation.first_image ? (
                              <Image
                                src={accommodation.first_image}
                                alt={accommodation.name}
                                fill
                                className="object-cover transition-transform group-hover:scale-110"
                                sizes="(max-width: 640px) 96px, 112px"
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center text-slate-400">
                                <Flame className="h-8 w-8" />
                              </div>
                            )}
                            {/* 순위 배지 오버레이 */}
                            <div className="absolute top-2 left-2">
                              <div
                                className={`${getRankBadgeColor(rank)} flex items-center gap-1 px-2 py-1 rounded-lg shadow-lg`}
                              >
                                {getRankIcon(rank)}
                                <span className="text-xs font-bold">{rank}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* 숙소 정보 */}
                        <div className="flex-1 min-w-0">
                          <div className="mb-2">
                            <h3 className="text-lg font-bold text-slate-900 truncate group-hover:text-red-600 transition-colors">
                              {accommodation.name}
                            </h3>
                            <p className="text-sm text-slate-600 mt-0.5">
                              {accommodation.region}
                            </p>
                          </div>

                          {/* 신청 정보 */}
                          <div className="flex flex-wrap items-center gap-3 text-sm">
                            <div className="flex items-center gap-1.5 text-slate-700">
                              <Calendar className="h-4 w-4 text-slate-500" />
                              <span className="font-medium">
                                {formatDate(accommodation.date)}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5 text-slate-700">
                              <Users className="h-4 w-4 text-slate-500" />
                              <span>
                                신청 <span className="font-semibold text-red-600">{accommodation.applicants}</span>명
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5 text-slate-700">
                              <Target className="h-4 w-4 text-slate-500" />
                              <span>
                                점수 <span className="font-semibold text-blue-600">{accommodation.score.toFixed(1)}</span>
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* 호버 효과 표시 */}
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-50 text-red-600">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* 빈 상태 */}
            {accommodations.length === 0 && !loading && (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-slate-100">
                  <Flame className="h-10 w-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  인기 숙소가 없습니다
                </h3>
                <p className="text-slate-600">
                  현재 신청 가능한 인기 숙소가 없습니다
                </p>
              </div>
            )}
          </main>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
