"use client";

import Image from "next/image";
import Link from "next/link";
import {
  Bell,
  CalendarClock,
  Hotel,
  Loader2,
  LogOut,
  Sparkles,
  User,
  Medal,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import BottomNav from "@/components/layout/BottomNav";
import { useAuth } from "@/contexts/AuthContext";
import { useBookings } from "@/hooks/useBookings";
import { useWishlist } from "@/hooks/useWishlist";
import { useScoreBasedRecommendations } from "@/hooks/useAccommodations";
import { differenceInCalendarDays, format } from "date-fns";
import { ko } from "date-fns/locale";
import { BookingStatus, Booking } from "@/types/booking";

export default function MyPage() {
  const { user, isLoading: authLoading, logout } = useAuth();
  // FIXME: 예약 내역 조회가 너무 오래 걸려 임시로 비활성화
  // const { data: bookings = [], isLoading: bookingsLoading } = useBookings();
  const { wishlist } = useWishlist();
  const { data: scoreRecommendations = [], isLoading: recommendationsLoading } = useScoreBasedRecommendations(10);

  // const normalizedBookings: Booking[] = bookings.map((booking) => ({
  //   ...booking,
  //   status: (booking.status || "").toLowerCase() as BookingStatus,
  // }));

  // const scheduleStatuses = new Set(["pending", "won", "cancelled"]);
  // const upcomingBookings = normalizedBookings.filter((booking) =>
  //   scheduleStatuses.has(booking.status)
  // );

  const statusBadgeMap: Record<string, { label: string; className: string }> = {
    won: { label: "당첨", className: "bg-emerald-100 text-emerald-700" },
    pending: { label: "예약신청", className: "bg-blue-100 text-blue-700" },
    cancelled: { label: "취소", className: "bg-rose-100 text-rose-700" },
    completed: { label: "완료", className: "bg-slate-100 text-slate-700" },
  };

  const getNightCount = (booking: Booking) => {
    if (!booking.check_in || !booking.check_out) return 1;
    const start = new Date(booking.check_in);
    const end = new Date(booking.check_out);
    const nights = differenceInCalendarDays(end, start);
    return nights > 0 ? nights : 1;
  };

  const formatStaySummary = (booking: Booking) => {
    if (!booking.check_in) {
      return "일정 정보 없음";
    }
    const baseLabel = format(new Date(booking.check_in), "M월 d일", { locale: ko });
    return `${baseLabel} · ${getNightCount(booking)}박`;
  };
  const getStatusMeta = (status: string) =>
    statusBadgeMap[status] || {
      label: status ? status.toUpperCase() : "UNKNOWN",
      className: "bg-slate-100 text-slate-700",
    };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-sky-600" />
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
              <p className="text-sm font-semibold text-sky-700">MY 숙소</p>
              <p className="text-xs text-gray-600">포인트 · 예약 · 알림 관리</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="bg-white/80 text-sky-700 shadow-sm hidden sm:flex">
              <ShieldCheck className="mr-1 h-3.5 w-3.5" />
              계정 보호
            </Badge>
            <button
              onClick={logout}
              className="inline-flex items-center gap-2 rounded-xl bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-100"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">로그아웃</span>
            </button>
          </div>
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-8">
          <section className="grid gap-4 sm:grid-cols-3">
            <Card className="border-sky-100/80 bg-gradient-to-br from-white to-sky-50/70 shadow-sm">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-lg">
                  <User className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base text-slate-900">안녕하세요, {user?.name || "사용자"}</CardTitle>
                  <p className="text-xs text-slate-600">임직원 계정</p>
                </div>
              </CardHeader>
              <CardContent className="flex items-center justify-between pt-0 text-sm">
                <span className="text-slate-700">인증 상태</span>
                <Badge className={user?.is_verified ? "bg-emerald-600 text-white" : "bg-amber-600 text-white"}>
                  {user?.is_verified ? "인증완료" : "대기중"}
                </Badge>
              </CardContent>
            </Card>

            <Card className="border-sky-100/80 bg-white/80 shadow-sm backdrop-blur">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                  <Medal className="h-5 w-5" />
                </div>
                <CardTitle className="text-base text-slate-900">숙박 점수</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-700">나의 점수</span>
                  <span className="font-semibold text-amber-700">{user?.points ?? 0}점</span>
                </div>
                <div className="flex items-center justify-between text-slate-600">
                  <span>남은 박수</span>
                  <span>{user?.available_nights || 0} 박</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-sky-100/80 bg-sky-900 text-white shadow-lg">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15">
                  <Sparkles className="h-5 w-5" />
                </div>
                <CardTitle className="text-base">찜 · 알림 관리</CardTitle>
              </CardHeader>
              <CardContent className="flex items-center justify-between pt-0 text-sm text-white/80">
                <span>즐겨찾기 {wishlist.length}곳</span>
                <Link href="/wishlist" className="text-sky-100 underline underline-offset-4">
                  바로가기
                </Link>
              </CardContent>
            </Card>
          </section>

          {/* 점수 기반 추천 섹션 */}
          {scoreRecommendations.length > 0 && (
            <section className="relative overflow-hidden rounded-3xl border border-amber-200/50 bg-gradient-to-br from-amber-50 via-orange-50/80 to-yellow-50/60 p-6 shadow-xl sm:p-8">
              {/* 배경 장식 */}
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(251,191,36,0.1),transparent_50%)]" />
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,_rgba(249,115,22,0.08),transparent_50%)]" />

              <div className="relative">
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg">
                      <Sparkles className="h-5 w-5 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-amber-700 to-orange-700 bg-clip-text text-transparent">
                      {user?.name || "사용자"}님을 위한 인기 숙소
                    </h2>
                  </div>
                  <p className="text-sm text-amber-800/80 font-medium ml-12">
                    최근 3개월간 <span className="font-bold text-amber-900">{scoreRecommendations[0]?.score_range}</span> 점수대로 마감된 인기 숙소를 추천해드려요
                  </p>
                </div>

                {/* 맞춤 추천 배지 */}
                <div className="mb-4 ml-12">
                  <Badge className="bg-gradient-to-r from-amber-600 to-orange-600 text-white border-0 shadow-md px-3 py-1.5">
                    <Medal className="h-3.5 w-3.5 mr-1" />
                    맞춤 추천
                  </Badge>
                </div>

                <div className="relative -mx-2">
                  <div className="flex gap-3 overflow-x-auto px-2 pb-4 scrollbar-hide snap-x snap-mandatory" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                    {recommendationsLoading ? (
                      <div className="flex w-full justify-center py-12">
                        <div className="flex flex-col items-center gap-3">
                          <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
                          <p className="text-sm text-amber-700">추천 숙소를 불러오는 중...</p>
                        </div>
                      </div>
                    ) : (
                      scoreRecommendations.map((accommodation, index) => (
                        <Link
                          key={accommodation.id}
                          href={`/accommodations/${accommodation.id}`}
                          className="group relative flex-shrink-0 w-60 snap-start overflow-hidden rounded-xl bg-white shadow-md transition-all duration-300 hover:shadow-xl hover:-translate-y-1.5 border border-amber-100/50"
                        >
                          {/* 이미지 영역 */}
                          <div className="relative h-40 w-full overflow-hidden">
                            {/* 이미지 */}
                            {accommodation.first_image ? (
                              <Image
                                src={accommodation.first_image}
                                alt={accommodation.name}
                                fill
                                className="object-cover transition-transform duration-500 group-hover:scale-110"
                              />
                            ) : (
                              <div className="flex h-full items-center justify-center bg-gradient-to-br from-amber-100 to-orange-100">
                                <Hotel className="h-16 w-16 text-amber-300/50" />
                              </div>
                            )}

                            {/* 그라데이션 오버레이 */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-60 group-hover:opacity-40 transition-opacity" />

                            {/* 순위 뱃지 */}
                            {index < 3 && (
                              <div className="absolute top-2 left-2 flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg ring-2 ring-white/30">
                                <span className="text-xs font-bold text-white">{index + 1}</span>
                              </div>
                            )}

                            {/* 마감 횟수 뱃지 */}
                            <div className="absolute top-2 right-2 flex items-center gap-1 rounded-full bg-white/95 backdrop-blur-sm px-2.5 py-1.5 shadow-lg ring-1 ring-amber-200/50">
                              <CalendarClock className="h-3 w-3 text-amber-600" />
                              <span className="text-xs font-bold text-amber-900">{accommodation.visitor_count}회</span>
                            </div>
                          </div>

                          {/* 정보 영역 */}
                          <div className="p-3.5">
                            <h3 className="font-bold text-slate-900 line-clamp-1 text-base group-hover:text-amber-700 transition-colors">
                              {accommodation.name}
                            </h3>
                            <div className="mt-1.5 flex items-center gap-1.5">
                              <div className="flex items-center gap-1 rounded-lg bg-slate-100 px-2 py-0.5">
                                <Hotel className="h-3 w-3 text-slate-600" />
                                <span className="text-xs font-medium text-slate-700">{accommodation.region}</span>
                              </div>
                            </div>

                            {/* 호버 시 나타나는 정보 */}
                            <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                              <div className="flex items-center gap-1.5 text-xs text-amber-700">
                                <Sparkles className="h-3 w-3" />
                                <span className="font-medium">인기 숙소 · 빠른 마감</span>
                              </div>
                            </div>
                          </div>

                          {/* 카드 테두리 그라데이션 효과 */}
                          <div className="absolute inset-0 rounded-xl ring-1 ring-inset ring-amber-200/0 group-hover:ring-amber-300/50 transition-all pointer-events-none" />
                        </Link>
                      ))
                    )}
                  </div>
                </div>

                {/* 스크롤 힌트 */}
                {scoreRecommendations.length > 3 && (
                  <div className="mt-4 flex justify-center">
                    <div className="flex items-center gap-2 text-xs text-amber-700/60">
                      <div className="h-1 w-1 rounded-full bg-amber-400 animate-pulse" />
                      <span>좌우로 스크롤하여 더 많은 추천 숙소를 확인하세요</span>
                      <div className="h-1 w-1 rounded-full bg-amber-400 animate-pulse" />
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* FIXME: 예약 내역 조회가 너무 오래 걸려 임시로 비활성화 */}
          {/* <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-4 shadow-lg backdrop-blur-lg sm:p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">
                  예약 일정
                </h2>
                <p className="mt-1 text-sm text-slate-700">
                  당첨 · 대기 · 취소 내역을 확인하고 필요한 알림을 설정하세요.
                </p>
              </div>
              <Badge variant="secondary" className="bg-sky-50 text-sky-700">
                <CalendarClock className="mr-1 h-4 w-4" />
                캘린더 연동
              </Badge>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {bookingsLoading ? (
                <div className="col-span-2 flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-sky-600" />
                </div>
              ) : upcomingBookings.length === 0 ? (
                <div className="col-span-2 py-8 text-center text-slate-600">
                  <Hotel className="h-12 w-12 mx-auto mb-2 text-slate-400" />
                  <p>예약 일정이 없습니다</p>
                  <p className="text-sm mt-1">원하시는 숙소를 검색하여 예약 신청하세요</p>
                </div>
              ) : (
                upcomingBookings.map((booking) => {
                  const statusMeta = getStatusMeta(booking.status);
                  return (
                    <Card
                      key={booking.id}
                      className="border-sky-100/70 bg-gradient-to-br from-white to-sky-50/60 shadow-sm"
                    >
                      <CardHeader className="flex flex-row items-start gap-3 space-y-0">
                        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                          <Hotel className="h-5 w-5" />
                        </div>
                        <div>
                        <CardTitle className="text-base text-slate-900">
                          {booking.accommodation?.name || booking.accommodation_name || "숙소 정보 없음"}
                        </CardTitle>
                        <p className="text-xs text-slate-600">
                          {formatStaySummary(booking)}
                        </p>
                      </div>
                    </CardHeader>
                    <CardContent className="flex items-center justify-between pt-0">
                      <Badge className={statusMeta.className}>{statusMeta.label}</Badge>
                      <button
                        type="button"
                        className="inline-flex items-center gap-2 rounded-xl bg-sky-50 px-3 py-2 text-xs font-semibold text-sky-700 transition hover:bg-sky-100"
                      >
                        <Bell className="h-4 w-4" />
                        알림 설정
                      </button>
                    </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          </section> */}
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
