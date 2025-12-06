"use client";

import { useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface AccommodationImageCarouselProps {
  images: string[];
}

export default function AccommodationImageCarousel({
  images,
}: AccommodationImageCarouselProps) {
  const validImages = images?.filter(Boolean) ?? [];
  const [currentIndex, setCurrentIndex] = useState(0);

  if (validImages.length === 0) {
    return (
      <div className="relative h-64 w-full bg-gray-100 flex items-center justify-center">
        <p className="text-gray-500">이미지를 불러올 수 없습니다.</p>
      </div>
    );
  }

  const goToPrevious = () => {
    setCurrentIndex((prev) =>
      prev === 0 ? validImages.length - 1 : prev - 1
    );
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % validImages.length);
  };

  const currentImage = validImages[currentIndex];

  return (
    <div className="relative w-full">
      <div className="relative h-64 sm:h-80 md:h-96 w-full overflow-hidden rounded-none sm:rounded-2xl">
        <Image
          src={currentImage}
          alt={`숙소 이미지 ${currentIndex + 1}`}
          fill
          className="object-cover"
          priority
        />

        {validImages.length > 1 && (
          <>
            <button
              onClick={goToPrevious}
              className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/40 text-white p-2 rounded-full hover:bg-black/60"
              aria-label="이전 이미지"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/40 text-white p-2 rounded-full hover:bg-black/60"
              aria-label="다음 이미지"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </>
        )}
      </div>

      {validImages.length > 1 && (
        <div className="mt-4 flex items-center justify-center gap-2">
          {validImages.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`h-2 rounded-full transition-all ${
                index === currentIndex
                  ? "w-8 bg-blue-600"
                  : "w-2 bg-gray-300 hover:bg-gray-400"
              }`}
              aria-label={`이미지 ${index + 1} 보기`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
