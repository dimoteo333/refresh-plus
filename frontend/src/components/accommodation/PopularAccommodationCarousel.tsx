"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Calendar, Users, TrendingUp, Flame } from "lucide-react";
import { PopularAccommodation } from "@/types/accommodation";
import { Badge } from "@/components/ui/badge";

interface PopularAccommodationCarouselProps {
  accommodations: PopularAccommodation[];
  autoPlayInterval?: number;
}

export default function PopularAccommodationCarousel({
  accommodations,
  autoPlayInterval = 5000,
}: PopularAccommodationCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  // 자동 슬라이드
  useEffect(() => {
    if (accommodations.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % accommodations.length);
    }, autoPlayInterval);

    return () => clearInterval(interval);
  }, [accommodations.length, autoPlayInterval]);

  const goToPrevious = () => {
    setCurrentIndex((prev) =>
      prev === 0 ? accommodations.length - 1 : prev - 1
    );
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % accommodations.length);
  };

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
  };

  if (accommodations.length === 0) {
    return (
      <div className="relative mx-auto max-w-[420px] overflow-hidden rounded-3xl border border-sky-100/60 bg-sky-50/80 shadow-xl flex items-center justify-center h-64">
        <p className="text-slate-600">인기 숙소 정보를 불러오는 중...</p>
      </div>
    );
  }

  const currentAccommodation = accommodations[currentIndex];
  const isTopThree = currentIndex < 3;

  return (
    <div className="relative mx-auto max-w-[420px]">
      {/* 메인 이미지 */}
      <div className="relative overflow-hidden rounded-3xl border border-sky-100/60 bg-sky-50/80 shadow-xl">
        <Link
          href={`/accommodations/${currentAccommodation.id}`}
          aria-label={`${currentAccommodation.name} 상세 페이지로 이동`}
          className="group block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
        >
          {currentAccommodation.first_image ? (
            <div className="relative h-64 w-full sm:h-80">
              <Image
                src={currentAccommodation.first_image}
                alt={currentAccommodation.name}
                fill
                className="object-cover transition duration-500 group-hover:scale-[1.02]"
                priority
              />

              {/* 상위 3개 인기 배지 (좌측 상단) */}
              {isTopThree && (
                <div className="absolute left-3 top-3">
                  <Badge className="bg-red-500 text-white hover:bg-red-600 gap-1 px-3 py-1.5">
                    <Flame className="h-4 w-4" />
                    인기
                  </Badge>
                </div>
              )}

              {/* 숙소 정보 오버레이 (하단) */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent p-4">
                <h3 className="text-lg font-semibold text-white mb-2">
                  {currentAccommodation.name}
                </h3>
                <div className="flex flex-wrap items-center gap-3 text-sm text-white/90">
                  {/* 신청 날짜 */}
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>{currentAccommodation.date}</span>
                  </div>
                  {/* 신청 인원 */}
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    <span>{currentAccommodation.applicants}명</span>
                  </div>
                  {/* 점수 */}
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4" />
                    <span>{currentAccommodation.score.toFixed(1)}점</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-64 w-full items-center justify-center bg-sky-50 sm:h-80">
              <p className="text-slate-600">이미지 없음</p>
            </div>
          )}
        </Link>

        {/* 좌우 화살표 버튼 */}
        {accommodations.length > 1 && (
          <>
            <button
              onClick={goToPrevious}
              className="absolute left-2 top-1/2 -translate-y-1/2 transition hover:scale-110"
              aria-label="이전 숙소"
            >
              <ChevronLeft className="h-8 w-8 text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]" />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 transition hover:scale-110"
              aria-label="다음 숙소"
            >
              <ChevronRight className="h-8 w-8 text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]" />
            </button>
          </>
        )}
      </div>

      {/* 하단 점 네비게이션 */}
      {accommodations.length > 1 && (
        <div className="mt-4 flex items-center justify-center gap-2">
          {accommodations.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`h-2 rounded-full transition-all ${
                index === currentIndex
                  ? "w-8 bg-sky-600"
                  : "w-2 bg-sky-300 hover:bg-sky-400"
              }`}
              aria-label={`슬라이드 ${index + 1}로 이동`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
