"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Bell,
  Bot,
  Compass,
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
import ImageCarousel from "@/components/accommodation/ImageCarousel";
import PopularAccommodationCarousel from "@/components/accommodation/PopularAccommodationCarousel";
import SOLRecommendedAccommodationCarousel from "@/components/accommodation/SOLRecommendedAccommodationCarousel";
import { RandomAccommodation, PopularAccommodation, SOLRecommendedAccommodation } from "@/types/accommodation";
import { accommodationApi } from "@/lib/api";

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
  const [randomAccommodations, setRandomAccommodations] = useState<RandomAccommodation[]>([]);
  const [popularAccommodations, setPopularAccommodations] = useState<PopularAccommodation[]>([]);
  const [solRecommendedAccommodations, setSOLRecommendedAccommodations] = useState<SOLRecommendedAccommodation[]>([]);

  useEffect(() => {
    const fetchRandomAccommodations = async () => {
      try {
        const response = await accommodationApi.getRandom(5);
        setRandomAccommodations(response.data);
      } catch (error) {
        console.error("Failed to fetch random accommodations:", error);
      }
    };

    const fetchPopularAccommodations = async () => {
      try {
        const response = await accommodationApi.getPopular(5);
        setPopularAccommodations(response.data);
      } catch (error) {
        console.error("Failed to fetch popular accommodations:", error);
      }
    };

    const fetchSOLRecommendedAccommodations = async () => {
      try {
        const response = await accommodationApi.getSOLRecommended(5);
        setSOLRecommendedAccommodations(response.data);
      } catch (error) {
        console.error("Failed to fetch SOL recommended accommodations:", error);
      }
    };

    fetchRandomAccommodations();
    fetchPopularAccommodations();
    fetchSOLRecommendedAccommodations();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50/70 to-white text-gray-900">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-28 pt-1 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-3 px-1 py-1 sm:px-2">
          <div className="flex items-center gap-3">
            <Image
              src="/images/refresh_plus_logo.png"
              alt="Refresh Plus 로고"
              width={180}
              height={67}
              className="h-24 w-auto object-contain bg-transparent sm:h-24"
              priority
            />
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

        <main className="mt-3 flex flex-1 flex-col gap-10">
          <section
            id="hero"
            className="relative overflow-hidden rounded-3xl border border-sky-100/60 bg-white/80 p-6 shadow-lg backdrop-blur-lg sm:p-8"
          >
            <div className="grid gap-8 md:grid-cols-2 md:items-center">
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <Badge className="bg-sky-100 text-sky-800">실시간 예약 · 알림</Badge>
                </div>
                <h1 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl">
                  연성소를 누구보다
                  <br />
                  <span className="text-blue-600">빠르게</span> 예약하세요
                </h1>
                <p className="text-base leading-relaxed text-slate-700 sm:text-lg">
                  원하는 숙소의 실시간 현황, 푸시 알림, AI 추천까지 한 번에.
                  신한 임직원을 위한 스마트한 연성소 예약 경험을 제공합니다.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2 text-sm text-sky-800">
                    <Star className="h-4 w-4 fill-sky-500 text-sky-500" />
                    <span>실시간 알림 · 챗봇 · 추천</span>
                  </div>
                </div>
              </div>
              <div className="relative">
                <ImageCarousel accommodations={randomAccommodations} />
              </div>
            </div>
          </section>


          {/* 실시간 인기 숙소 섹션 */}
          <section
            id="popular-accommodations"
            className="relative overflow-hidden rounded-3xl border border-sky-100/60 bg-white/80 p-6 shadow-lg backdrop-blur-lg sm:p-8"
          >
            <div className="grid gap-8 md:grid-cols-2 md:items-center">
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <Badge className="bg-red-100 text-red-800">실시간 인기</Badge>
                </div>
                <h2 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl">
                  지금 가장 <span className="text-red-600">핫한</span> 숙소
                </h2>
                <p className="text-base leading-relaxed text-slate-700 sm:text-lg">
                  오늘 신청 가능한 숙소 중 가장 인기있는 숙소들이에요.
                  실시간 신청 현황과 예측 점수에 대해 확인하세요!
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    href="/popular"
                    className={`${primaryButtonClasses} h-11 px-5 text-base`}
                  >
                    실시간 인기 숙소
                  </Link>
                </div>
              </div>
              <div className="relative">
                <PopularAccommodationCarousel accommodations={popularAccommodations} />
              </div>
            </div>
          </section>


          {/* AI 기반 추천 및 챗봇 섹션 */}
          <section
            id="ai-features"
            className="relative overflow-hidden rounded-3xl border border-purple-100/60 bg-gradient-to-br from-purple-50/80 to-indigo-50/60 p-6 shadow-lg backdrop-blur-lg sm:p-8"
          >
            <div className="space-y-6">
              {/* 헤더 */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge className="bg-purple-100 text-purple-800">AI 추천 & 상담</Badge>
                </div>
                <h2 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl">
                  <span className="text-purple-600">AI 기반</span> 숙소 요약과 실시간 상담
                </h2>
                <div className="space-y-1">
                  <p className="text-base leading-relaxed text-slate-700 sm:text-lg">
                    AI 기반 숙소 요약, SOL 점수 계산 및 실시간 상담 챗봇을 제공해요.
                  </p>
                </div>
              </div>

              {/* AI 요약 박스 */}
              <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-sky-50 p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="rounded-full bg-indigo-100 p-2 text-indigo-700">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    숙소 3줄 요약
                  </h3>
                </div>
                <ul className="space-y-2 text-sm text-gray-800 leading-relaxed">
                  <li className="flex gap-2">
                    <span className="text-indigo-500">•</span>
                    <span>숙소의 핵심 정보와 특징을 한눈에 파악</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-indigo-500">•</span>
                    <span>한강뷰, 오션뷰 및 스파 등 부대시설에 대한 빠른 확인</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-indigo-500">•</span>
                    <span>주변 관광지 정보까지 빠르게 전달합니다</span>
                  </li>
                </ul>
              </div>

              {/* 챗봇 미리보기 박스 */}
              <div className="rounded-2xl border border-sky-100 bg-white/90 p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <div className="rounded-full bg-gradient-to-br from-sky-500 to-blue-600 p-2 text-white shadow-sm">
                    <Bot className="h-4 w-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    실시간 AI 챗봇 상담
                  </h3>
                </div>

                {/* 예시 대화 */}
                <div className="space-y-3">
                  {/* 질문 */}
                  <div className="flex justify-end">
                    <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-2.5 shadow-sm">
                      <p className="text-sm text-white">연 사용일수는 며칠인가요?</p>
                    </div>
                  </div>

                  {/* 답변 */}
                  <div className="flex justify-start">
                    <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-gray-100 px-4 py-2.5 shadow-sm">
                      <p className="text-sm text-gray-900 leading-relaxed">
                        입실일 기준 1월 1일부터 12월 31일까지 총 4박 사용 가능합니다.
                        단, 당일취소나 노쇼 차감이 있습니다.
                      </p>
                    </div>
                  </div>

                  {/* 챗봇 링크 */}
                  <div className="pt-2">
                    <Link
                      href="/chat"
                      className={`${primaryButtonClasses} h-10 w-full px-4 text-sm`}
                    >
                      <Bot className="h-4 w-4 mr-2" />
                      AI 챗봇과 대화하기
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </section>


          {/* SOL 추천 숙소 섹션 */}
          <section
            id="sol-recommended-accommodations"
            className="relative overflow-hidden rounded-3xl border border-blue-100/60 bg-gradient-to-br from-blue-50/80 to-sky-50/60 p-6 shadow-lg backdrop-blur-lg sm:p-8"
          >
            <div className="grid gap-8 md:grid-cols-2 md:items-center">
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <Badge className="bg-blue-100 text-blue-800">AI 추천</Badge>
                </div>
                <h2 className="flex items-center gap-2 text-3xl font-bold leading-tight text-slate-900 sm:text-4xl">
                  <Image
                    src="/images/sol_standing.png"
                    alt="쏠 캐릭터"
                    width={40}
                    height={40}
                    className="h-10 w-auto object-contain sm:h-12"
                  />
                  <span className="text-blue-600">쏠</span>이 추천하는 숙소
                </h2>
                <p className="text-base leading-relaxed text-slate-700 sm:text-lg">
                  네이버 호텔 최저가와 지금까지의 숙박 점수 데이터를 분석해
                  <span className="font-semibold text-blue-600"> 쏠</span>이 직접 선정한
                  <span className="font-semibold"> 가성비 최고의 숙소</span>들입니다.
                  합리적인 포인트로 프리미엄 숙소를 경험하세요!
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    href="/search"
                    className={`${primaryButtonClasses} h-11 px-5 text-base`}
                  >
                    전체 숙소 보기
                  </Link>
                </div>
              </div>
              <div className="relative">
                <SOLRecommendedAccommodationCarousel accommodations={solRecommendedAccommodations} />
              </div>
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
              <span>스마트폰에서 푸시 알림으로 편하게</span>
            </div>
          </section>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
