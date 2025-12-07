"use client";

import Image from "next/image";
import {
  AlarmCheck,
  Bell,
  Flame,
  Heart,
  Loader2,
  MapPin,
  ShieldCheck,
  Sparkles,
  Star,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import BottomNav from "@/components/layout/BottomNav";
import { useWishlist } from "@/hooks/useWishlist";
import { useAuth } from "@/contexts/AuthContext";

const alertRules = [
  { title: "평균 점수 도달", desc: "내 점수 이상 확보 시 푸시", icon: Star },
  { title: "마감 임박", desc: "30분 전 인기 숙소 알림", icon: AlarmCheck },
  { title: "포인트 회복", desc: "다음 회복 시점 리마인드", icon: Sparkles },
];

export default function WishlistPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { wishlist, removeFromWishlist, isLoading: wishlistLoading } = useWishlist();

  const handleRemove = async (accommodationId: string) => {
    try {
      await removeFromWishlist(accommodationId);
    } catch (error) {
      console.error("Failed to remove from wishlist:", error);
    }
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
              <p className="text-sm font-semibold text-sky-700">즐겨찾기</p>
              <p className="text-xs text-gray-600">찜한 숙소와 알림을 한 번에</p>
            </div>
          </div>
          <Badge className="bg-white/80 text-sky-700 shadow-sm">
            <Heart className="mr-1 h-3.5 w-3.5 fill-sky-500 text-sky-500" />
            {wishlist.length}곳 찜
          </Badge>
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-8">
          <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-4 shadow-lg backdrop-blur-lg sm:p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl">
                  찜한 숙소
                </h1>
                <p className="mt-1 text-sm text-slate-700">
                  알림이 켜진 숙소는 배정 결과를 실시간으로 알려드려요.
                </p>
              </div>
              <Badge variant="secondary" className="bg-sky-50 text-sky-700">
                자동 동기화
              </Badge>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              {wishlistLoading ? (
                <div className="col-span-3 flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-sky-600" />
                </div>
              ) : wishlist.length === 0 ? (
                <div className="col-span-3 py-8 text-center text-slate-600">
                  <Heart className="h-12 w-12 mx-auto mb-2 text-slate-400" />
                  <p>즐겨찾기한 숙소가 없습니다</p>
                  <p className="text-sm mt-1">마음에 드는 숙소를 찾아 하트를 눌러보세요</p>
                </div>
              ) : (
                wishlist.map((item: any) => (
                  <Card
                    key={item.id}
                    className="border-sky-100/70 bg-gradient-to-br from-white to-sky-50/70 shadow-sm relative"
                  >
                    <button
                      onClick={() => handleRemove(item.accommodation_id)}
                      className="absolute top-3 right-3 h-8 w-8 rounded-full bg-white/80 hover:bg-white flex items-center justify-center transition-colors shadow-sm"
                      aria-label="Remove from wishlist"
                    >
                      <X className="h-4 w-4 text-slate-600" />
                    </button>
                    <CardHeader className="flex flex-row items-start gap-3 space-y-0 pr-12">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                        <MapPin className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base text-slate-900">
                          {item.accommodation?.name || "숙소 정보 없음"}
                        </CardTitle>
                        <p className="text-xs text-slate-600">
                          {item.accommodation?.location || "위치 정보 없음"}
                        </p>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3 pt-0">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-800">
                          {item.accommodation?.avg_winning_score
                            ? `평균 당첨 ${item.accommodation.avg_winning_score}점`
                            : "점수 정보 없음"}
                        </span>
                        <span className="text-xs text-sky-700">
                          {item.notify_when_bookable ? "알림 ON" : "알림 OFF"}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        {item.accommodation?.tags?.slice(0, 2).map((tag: string) => (
                          <Badge key={tag} variant="secondary" className="bg-sky-50 text-sky-700">
                            #{tag}
                          </Badge>
                        ))}
                        {item.notify_when_bookable && (
                          <Badge className="bg-blue-600 text-white">
                            <Bell className="mr-1 h-3.5 w-3.5" />
                            알림 유지
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </section>

          <section className="rounded-3xl border border-sky-100/70 bg-sky-900 text-white p-4 shadow-lg sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-white/70">
                  알림 규칙
                </p>
                <h2 className="text-xl font-semibold sm:text-2xl">
                  놓치기 쉬운 타이밍을 챙겨드려요
                </h2>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15">
                <ShieldCheck className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {alertRules.map((rule) => (
                <div
                  key={rule.title}
                  className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm"
                >
                  <div className="flex items-center gap-2 text-sm">
                    <rule.icon className="h-4 w-4 text-amber-200" />
                    <span className="font-semibold">{rule.title}</span>
                  </div>
                  <p className="mt-2 text-sm text-white/80">{rule.desc}</p>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
