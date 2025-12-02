"use client";

import { useAccommodations } from "@/hooks/useAccommodations";
import AccommodationCard from "@/components/accommodation/AccommodationCard";

export default function DashboardPage() {
  const { data: accommodations, isLoading } = useAccommodations({ limit: 6 });

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">대시보드</h1>
        <p className="text-gray-600">인기 숙소를 둘러보세요</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accommodations?.map((accommodation) => (
            <AccommodationCard
              key={accommodation.id}
              accommodation={accommodation}
            />
          ))}
        </div>
      )}
    </div>
  );
}
