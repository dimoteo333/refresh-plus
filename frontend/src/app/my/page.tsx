"use client";

import Image from "next/image";
import Link from "next/link";
import {
  Bell,
  CalendarClock,
  CreditCard,
  Heart,
  Hotel,
  Loader2,
  LogOut,
  NotebookPen,
  ShieldCheck,
  Sparkles,
  User,
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
import { differenceInCalendarDays, format } from "date-fns";
import { ko } from "date-fns/locale";
import { BookingStatus } from "@/types/booking";
import { Booking } from "@/types/booking";

type BookingWithAccommodation = Booking & {
  accommodation?: {
    name?: string;
  };
};
type NormalizedBooking = BookingWithAccommodation & { status: string };

export default function MyPage() {
  const { user, isLoading: authLoading, logout } = useAuth();
  const { data: bookings = [], isLoading: bookingsLoading } = useBookings();
  const { wishlist } = useWishlist();

  const normalizedBookings: NormalizedBooking[] = (bookings as BookingWithAccommodation[]).map((booking) => ({
    ...booking,
    status: (booking.status || "").toLowerCase() as BookingStatus,
  }));

  const scheduleStatuses = new Set(["pending", "won", "cancelled"]);
  const upcomingBookings = normalizedBookings.filter((booking) =>
    scheduleStatuses.has(booking.status)
  );

  const recentBookings = normalizedBookings.filter((booking) => {
    if (!booking.created_at) return false;
    const bookingDate = new Date(booking.created_at);
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
    return bookingDate >= ninetyDaysAgo;
  });

  const pendingCount = recentBookings.filter((b) => b.status === "pending").length;
  const wonCount = recentBookings.filter((b) => b.status === "won").length;
  const lostCount = recentBookings.filter((b) => b.status === "lost").length;

  const statusBadgeMap: Record<string, { label: string; className: string }> = {
    won: { label: "당첨", className: "bg-emerald-100 text-emerald-700" },
    pending: { label: "대기 중", className: "bg-amber-100 text-amber-700" },
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
                src="/images/sol-bear.svg"
                alt="SOL 캐릭터 로고"
                width={48}
                height={48}
                className="h-full w-full object-cover"
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
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                  <CreditCard className="h-5 w-5" />
                </div>
                <CardTitle className="text-base text-slate-900">포인트 현황</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-700">사용 가능</span>
                  <span className="font-semibold text-sky-700">{user?.points || 0} P</span>
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

          <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-4 shadow-lg backdrop-blur-lg sm:p-6">
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
                          {booking.accommodation?.name || "숙소 정보 없음"}
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
          </section>

          <section className="grid gap-4 sm:grid-cols-3">
            <Card className="border-sky-100/80 bg-white/80 shadow-sm backdrop-blur">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                  <Heart className="h-5 w-5" />
                </div>
                <CardTitle className="text-base text-slate-900">선호 태그</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2 pt-0 text-sm">
                {["오션뷰", "힐링", "노키즈존", "스파"].map((tag) => (
                  <Badge key={tag} variant="secondary" className="bg-sky-50 text-sky-700">
                    #{tag}
                  </Badge>
                ))}
              </CardContent>
            </Card>

            <Card className="border-sky-100/80 bg-white/80 shadow-sm backdrop-blur">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                  <NotebookPen className="h-5 w-5" />
                </div>
                <CardTitle className="text-base text-slate-900">신청 내역</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0 text-sm text-slate-700">
                <p>최근 90일 신청 {recentBookings.length}건</p>
                <p className="text-slate-600">승인 {wonCount} · 대기 {pendingCount} · 미당첨 {lostCount}</p>
              </CardContent>
            </Card>

            <Card className="border-sky-100/80 bg-white/80 shadow-sm backdrop-blur">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <CardTitle className="text-base text-slate-900">보안 설정</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0 text-sm text-slate-700">
                <p>2단계 인증 활성화</p>
                <p className="text-slate-600">기기 2대 로그인 중</p>
              </CardContent>
            </Card>
          </section>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
