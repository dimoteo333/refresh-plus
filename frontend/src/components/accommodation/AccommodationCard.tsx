"use client";

import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Accommodation } from "@/types/accommodation";
import Image from "next/image";
import Link from "next/link";
import { MapPin } from "lucide-react";

interface AccommodationCardProps {
  accommodation: Accommodation;
  onBook?: (id: string) => void;
}

export default function AccommodationCard({
  accommodation,
  onBook,
}: AccommodationCardProps) {
  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      {/* 이미지 */}
      <div className="relative h-48 w-full bg-gray-200">
        {accommodation.images?.[0] ? (
          <Image
            src={accommodation.images[0]}
            alt={accommodation.name}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            No Image
          </div>
        )}

        {/* 배지 */}
        <div className="absolute top-2 right-2 flex gap-2">
          {accommodation.can_book_with_current_score && (
            <Badge variant="success">예약 가능</Badge>
          )}
          <Badge variant="secondary">★ {accommodation.rating}</Badge>
        </div>
      </div>

      <CardContent className="pt-4">
        {/* 숙소명 */}
        <h3 className="font-semibold text-lg line-clamp-2 mb-2">
          {accommodation.name}
        </h3>

        {/* 위치 */}
        <div className="flex items-center gap-1 text-sm text-gray-600 mb-3">
          <MapPin size={16} />
          <span>{accommodation.region}</span>
        </div>

        {accommodation.summary && accommodation.summary.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {accommodation.summary.slice(0, 3).map((item, index) => (
              <Badge
                key={`${accommodation.id}-card-summary-${index}`}
                variant="secondary"
                className="border-sky-100 text-sky-700"
              >
                {item}
              </Badge>
            ))}
          </div>
        )}

        {/* 가격 */}
        <div className="mb-3 font-bold text-xl">
          ₩{accommodation.price?.toLocaleString()}
          <span className="text-sm text-gray-600 font-normal">/박</span>
        </div>

        {/* 당첨 필요 점수 */}
        <div className="text-sm text-gray-700">
          <span className="text-gray-600">최근 4주 평균 당첨:</span>
          <span className="font-semibold ml-1">
            {accommodation.avg_winning_score_4weeks}점
          </span>
        </div>

        {/* 남은 방 수 */}
        <div className="mt-2 text-sm">
          <span className="text-gray-600">남은 방: </span>
          <span className="font-semibold">{accommodation.availability}개</span>
        </div>
      </CardContent>

      <CardFooter className="gap-2">
        <Link href={`/accommodations/${accommodation.id}`} className="flex-1">
          <Button variant="outline" className="w-full">
            상세보기
          </Button>
        </Link>

        {onBook && (
          <Button
            onClick={() => onBook(accommodation.id)}
            disabled={!accommodation.can_book_with_current_score}
            className="flex-1"
          >
            {accommodation.can_book_with_current_score ? "예약하기" : "점수 부족"}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
