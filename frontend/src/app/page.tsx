import Image from "next/image";
import Link from "next/link";
import {
  Bell,
  Bot,
  Compass,
  MapPin,
  PlaneTakeoff,
  ShieldCheck,
  Sparkles,
  Star,
  Menu,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import BottomNav from "@/components/layout/BottomNav";

const buttonBase =
  "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
const primaryButtonClasses = `${buttonBase} bg-blue-600 text-white hover:bg-blue-700`;
const outlineButtonClasses = `${buttonBase} border border-gray-300 bg-white text-slate-800 hover:bg-gray-50`;

const featureCards = [
  {
    title: "실시간 알림",
    description: "예약 결과 · 찜한 숙소 · 포인트 회복까지 즉시 푸시",
    icon: Bell,
  },
  {
    title: "포인트 티켓팅",
    description: "점수 기반 자동 배정으로 공정하게 원하는 날짜를 확보",
    icon: Sparkles,
  },
  {
    title: "AI 챗봇",
    description: "FAQ RAG 챗봇이 여행/예약 궁금증을 바로 해결",
    icon: Bot,
  },
];

const journey = [
  { title: "원하는 숙소 찾기", detail: "실시간 신청 현황과 당첨 점수 한눈에", icon: Compass },
  { title: "간편 신청", detail: "클릭 한 번으로 PENDING 접수", icon: PlaneTakeoff },
  { title: "정오 이후 알림", detail: "배치 결과 WON/LOST 상태를 푸시로 확인", icon: Bell },
  { title: "MY 숙소 관리", detail: "예약 · 찜 · 알림 설정을 한 곳에서", icon: ShieldCheck },
];

export default function Home() {
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
              <p className="text-sm font-semibold text-sky-700">Refresh Plus</p>
              <p className="text-xs text-gray-600">신한 임직원 숙소 예약 플랫폼</p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-900 transition hover:bg-sky-100/40"
              aria-label="알림"
            >
              <Bell className="h-6 w-6" />
            </button>
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-900 transition hover:bg-sky-100/40"
              aria-label="전체 메뉴"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </header>

        <main className="mt-6 flex flex-1 flex-col gap-10">
          <section
            id="hero"
            className="relative overflow-hidden rounded-3xl border border-sky-100/60 bg-white/80 p-6 shadow-lg backdrop-blur-lg sm:p-8"
          >
            <div className="grid gap-8 md:grid-cols-2 md:items-center">
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <Badge className="bg-sky-100 text-sky-800">실시간 예약 · 알림</Badge>
                  <Badge variant="secondary" className="bg-white/80 text-sky-700">
                    모바일 최적화
                  </Badge>
                </div>
                <h1 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl">
                  여행의 설렘을
                  <br />
                  <span className="text-sky-600">포인트</span>로 예약하세요
                </h1>
                <p className="text-base leading-relaxed text-slate-700 sm:text-lg">
                  매일 자정 자동 배정, 원하는 숙소의 실시간 현황, 알림까지 한 번에.
                  신한 임직원을 위한 스마트한 연성소 예약 경험을 제공합니다.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    href="/sign-up"
                    className={`${primaryButtonClasses} h-11 px-5 text-base`}
                  >
                    시작하기
                  </Link>
                  <Link
                    href="/sign-in"
                    className={`${outlineButtonClasses} h-11 px-5 text-base`}
                  >
                    앱으로 로그인
                  </Link>
                  <div className="flex items-center gap-2 text-sm text-sky-800">
                    <Star className="h-4 w-4 fill-sky-500 text-sky-500" />
                    <span>실시간 알림 · 챗봇 · 포인트 티켓팅</span>
                  </div>
                </div>
              </div>
              <div className="relative">
                <div className="relative mx-auto max-w-[420px] overflow-hidden rounded-3xl border border-sky-100/60 bg-sky-50/80 shadow-xl">
                  <Image
                    src="/images/hero-travel.svg"
                    alt="여행 감성의 숙소 예약"
                    width={960}
                    height={640}
                    className="h-full w-full object-cover"
                    priority
                  />
                </div>
                <Card className="absolute -bottom-6 left-6 hidden w-56 rounded-2xl border-sky-100/60 bg-white/90 shadow-lg backdrop-blur-md sm:block">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg text-slate-800">오늘의 인기 숙소</CardTitle>
                  </CardHeader>
                  <CardContent className="flex items-center gap-3 pt-0">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
                      <MapPin className="h-6 w-6" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-slate-900">제주 바다뷰 리조트</p>
                      <p className="text-xs text-slate-600">평균 당첨 점수 78점</p>
                      <div className="flex items-center gap-1 text-xs text-sky-700">
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>알림 ON</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>

          <section id="features" className="grid gap-4 sm:grid-cols-3">
            {featureCards.map((feature) => (
              <Card
                key={feature.title}
                className="border-sky-100/80 bg-white/80 shadow-sm backdrop-blur"
              >
                <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <CardTitle className="text-lg text-slate-900">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent className="pt-2 text-sm text-slate-700">
                  {feature.description}
                </CardContent>
              </Card>
            ))}
          </section>

          <section
            id="journey"
            className="grid gap-6 rounded-3xl border border-sky-100/80 bg-white/70 p-6 shadow-md backdrop-blur-lg md:grid-cols-5"
          >
            <div className="md:col-span-2">
              <Badge className="bg-sky-100 text-sky-800">예약 여정</Badge>
              <h2 className="mt-3 text-2xl font-semibold text-slate-900">모바일 퍼스트 티켓팅</h2>
              <p className="mt-2 text-sm text-slate-700">
                자동화된 크롤러와 실시간 알림으로 여행 준비를 가볍게. 포인트 기반 배정과 챗봇까지
                모두 모바일에서 매끄럽게 동작합니다.
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="bg-sky-50 text-sky-700">
                  실시간 현황
                </Badge>
                <Badge variant="secondary" className="bg-sky-50 text-sky-700">
                  예약 결과 푸시
                </Badge>
                <Badge variant="secondary" className="bg-sky-50 text-sky-700">
                  Chainlit 챗봇
                </Badge>
              </div>
            </div>
            <div className="md:col-span-3 grid gap-3 sm:grid-cols-2">
              {journey.map((step) => (
                <Card
                  key={step.title}
                  className="border-sky-100/70 bg-gradient-to-br from-white to-sky-50/70 shadow-sm"
                >
                  <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 text-sky-700">
                      <step.icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-base text-slate-900">{step.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0 text-sm text-slate-700">{step.detail}</CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section
            id="alerts"
            className="flex flex-col gap-4 rounded-3xl border border-sky-100/70 bg-sky-900 text-white p-6 shadow-lg"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
                <Bell className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm uppercase tracking-wide text-white/70">스마트 알림</p>
                <h3 className="text-2xl font-semibold">놓치지 말아야 할 순간을 알려줘요</h3>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-sm text-white/80">찜한 숙소 예약 가능 시</p>
                <p className="mt-2 text-lg font-semibold">평균 당첨 점수 도달 알림</p>
              </div>
              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-sm text-white/80">PENDING 결과</p>
                <p className="mt-2 text-lg font-semibold">자정 배치 후 WON/LOST 푸시</p>
              </div>
              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-sm text-white/80">포인트 회복</p>
                <p className="mt-2 text-lg font-semibold">회복 타이밍 · 인기 숙소 마감 임박</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm text-white/80">
              <ShieldCheck className="h-5 w-5" />
              <span>Firebase · Kakao Talk 이중 채널 알림</span>
            </div>
          </section>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
