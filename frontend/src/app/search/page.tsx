import Image from "next/image";
import Link from "next/link";
import {
  Filter,
  Map,
  MapPin,
  Search,
  Sparkles,
  Star,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import BottomNav from "@/components/layout/BottomNav";

const suggestions = ["바다뷰", "노키즈존", "스파", "조식 포함", "포인트 낮은 순"];

const results = [
  {
    name: "여수 라이트하우스",
    location: "여수 | 오션뷰 테라스",
    score: "예상 당첨 72점",
    vibe: "노을",
  },
  {
    name: "속초 포레스트 호텔",
    location: "속초 | 힐링 스파",
    score: "예상 당첨 64점",
    vibe: "조용한 숙박",
  },
  {
    name: "제주 산책 레지던스",
    location: "제주 구좌 | 워케이션",
    score: "예상 당첨 58점",
    vibe: "장기숙박",
  },
];

export default function SearchPage() {
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
              <p className="text-sm font-semibold text-sky-700">검색</p>
              <p className="text-xs text-gray-600">필터와 당첨 점수로 빠르게 찾기</p>
            </div>
          </div>
          <Badge variant="secondary" className="bg-white/80 text-sky-700 shadow-sm">
            <Sparkles className="mr-1 h-3.5 w-3.5 text-sky-500" />
            스마트 검색
          </Badge>
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-8">
          <section className="rounded-3xl border border-sky-100/70 bg-white/80 p-4 shadow-lg backdrop-blur-lg sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl">
                원하는 숙소를 검색하세요
              </h1>
              <div className="flex items-center gap-2 text-xs text-slate-600">
                <TrendingUp className="h-4 w-4 text-sky-500" />
                최근 검색 기록을 기반으로 추천해요
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <div className="flex flex-1 items-center gap-3 rounded-2xl border border-sky-100/70 bg-sky-50/70 px-4 py-3 shadow-inner">
                <Search className="h-5 w-5 text-sky-500" />
                <input
                  type="text"
                  placeholder="지역, 숙소명, 키워드 검색"
                  className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none"
                />
              </div>
              <button
                type="button"
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:brightness-105"
              >
                <Filter className="h-4 w-4" />
                필터
              </button>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              {suggestions.map((keyword) => (
                <Badge
                  key={keyword}
                  variant="secondary"
                  className="bg-sky-50 text-sky-700"
                >
                  #{keyword}
                </Badge>
              ))}
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-3">
            {results.map((item) => (
              <Card
                key={item.name}
                className="border-sky-100/80 bg-white/80 shadow-sm backdrop-blur"
              >
                <CardHeader className="flex flex-row items-start gap-3 space-y-0">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                    <MapPin className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle className="text-base text-slate-900">{item.name}</CardTitle>
                    <p className="text-xs text-slate-600">{item.location}</p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-800">{item.score}</span>
                    <Badge className="bg-emerald-100 text-emerald-700">
                      <Star className="mr-1 h-3.5 w-3.5 fill-emerald-400 text-emerald-500" />
                      가용 객실
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <Map className="h-4 w-4 text-sky-500" />
                    {item.vibe}
                  </div>
                  <Link
                    href="/wishlist"
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-sky-50 py-2 text-sm font-semibold text-sky-700 transition hover:bg-sky-100"
                  >
                    <Sparkles className="h-4 w-4" />
                    찜하고 알림 받기
                  </Link>
                </CardContent>
              </Card>
            ))}
          </section>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
